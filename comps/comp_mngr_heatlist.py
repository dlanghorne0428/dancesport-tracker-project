import string
import requests

from django.db.models import Q
from rankings.models import Couple, Dancer
from .models import Heat, HeatEntry, HeatlistDancer, UnmatchedHeatEntry
from .heatlist import Heatlist


class CompMngrHeatlist(Heatlist):
    ''' This class derives from Heatlist. It parses the heatlist in CompMngr format and stores
        information about the heats in this competition.'''

    def __init__(self):
        super().__init__()
        self.lines = None

    ############### EXTRACTION ROUTINES  #################################################
    # the following methods extract specific data items from lines in the CompMngr file
    ######################################################################################
    def get_comp_name(self,line):
        '''This method extracts the name of the competition.
           It is found on the given line after a <strong> tag until the next HTML tag.'''
        start_pos = line.find("<strong>") + len("<strong>")
        end_pos = line.find("<", start_pos)
        name = line[start_pos:end_pos]
        return name


    def get_dancer_name(self, line, start_pos=20):
        '''This method returns the dancer name from a line, starting at a given column.
           In the HTML file produced by CompMngr, the dancer names are inside a <strong> tag.'''
        end_pos = line.find("</strong>")
        name = line[start_pos:end_pos]
        return name

    def load_heat(self, h, category, line="", comp_ref="", number=0):
        h.comp = comp_ref
        if category == "Pro heat":
            h.category = Heat.PRO_HEAT
        else:
            h.category = Heat.NORMAL_HEAT
        h.heat_number = number
        h.rounds = "F"      # assume final only
        if len(line) > 0:           # if line is not empty, parse it to obtain other properites
            fields = line.split("<td>")
            # get the session number, heat number, and multi-round info
            heat_time = fields[1].split("</td>")[0]
            if "@" in heat_time:
                heat_time_fields = heat_time.split("@")
                h.session = heat_time_fields[0]
                heat_time = heat_time_fields[1]
            else:
                h.session = ""
            if "<br>" in heat_time:
                time_session_fields = heat_time.split("<br>")
                heat_time = time_session_fields[0]

            # the heat_time string is in this format hh:mm PM day-of-week
            time_fields = heat_time.split()
            if len(time_fields) == 2:
                time_string = time_fields[0]
                day_of_week = time_fields[1]
                h.set_time(time_string, day_of_week)
            else:
                print("Invalid time format")

            # get the heat info
            h.info = fields[4].split("</td>")[0]
            h.remove_info_prefix()
            h.set_level()
            h.set_dance_style()

            # pull any non-digit characters from the heat number into extra
            start_pos = fields[3].find(category) + len(category) + 1
            i = start_pos
            # stop at the first non-digit
            while fields[3][i] in string.digits:
                i = i + 1
            if i > start_pos:
                h.heat_number = int(fields[3][start_pos:i])
            # anything non-digit is extra information, like ballroom assignment
            num_chars = len("</td>")
            h.extra = fields[3][i:-num_chars]
            h.extra = h.extra.replace("Ballroom ", "")

    ################# READING THE HEATLIST HTML FILE ################################
    # These methods process the HTML data file in CompMngr heatlist format
    # and populates the data structures
    ##################################################################################
    def open(self, url):
        '''This method opens the heatlist filename and finds all the dancer names.
           The file is left open so other methods can find the heat information.'''
        dancer = None       # variables for the current dancer
        found_last_dancer = False

        # open the file and loop through all the lines until last dancer is found
        #self.fhand = open(filename,encoding="utf-8")
        response = requests.get(url)
        self.lines = response.text.splitlines()
        self.line_index = 0
        while self.line_index < len(self.lines):
            line = self.lines[self.line_index]
            self.line_index += 1
            # if the line has "Show Entries", we can extract the name of a dancer
            if "Show entries" in line:
                dancer = HeatlistDancer()
                dancer.load_from_comp_mngr(line.strip())
                self.dancers.append(dancer)
            # if we see the line that says "size="", extract the name of the competition
            if 'size=' in line:
                self.comp_name = self.get_comp_name(line.strip())
                #print("Comp Name =", self.comp_name)
            # if we see the closing </table> tag, we have found all the dancers
            if "/table" in line:
                #print("Found", len(self.dancers), "dancers")
                found_last_dancer = True
            # once we have found the last dancer, stop after finding the closing </div> tag
            if "/div" in line:
                if found_last_dancer:
                    break;

    def load(self, url, heatlist_dancers):
        for d in heatlist_dancers:
            self.dancers.append(d)
            print(d.name)

        # open the file and skip all the lines until last dancer is found
        response = requests.get(url)
        self.lines = response.text.splitlines()
        self.line_index = 0
        found_last_dancer = False
        while self.line_index < len(self.lines):
            line = self.lines[self.line_index]
            self.line_index += 1
            # if we see the closing </table> tag, we have found all the dancers
            if "/table" in line:
                #print("Found", len(self.dancers), "dancers")
                found_last_dancer = True
            # once we have found the last dancer, stop after finding the closing </div> tag
            if "/div" in line:
                if found_last_dancer:
                    break;


    def build_heat(self, category_str, line, comp_ref):
        # turn that heat info into an object and add it to the database
        heat = Heat()
        self.load_heat(heat, category_str, line, comp_ref)
        return self.add_heat_to_database(heat, comp_ref)


    def get_next_dancer(self, dancer_index, comp_ref):
        '''This method continues to parse the CompMngr heatlist file, extracting the heat
           information for the next dancer.
           The dancer_index is a counter, providing a quick way to find the dancer object
           based on the dancer's name'''
        dancer = None       # object for the current dancer

        while self.line_index < len(self.lines):
            line = self.lines[self.line_index]
            self.line_index += 1
            # A line with "Entries For" indicates the start of a new dancer's heat information
            if "Entries for" in line:
                dancer_name = self.get_dancer_name(line.strip())
                # check if this dancer name matches the dancer object at the given index
                if dancer_name == self.dancers[dancer_index].name:
                    dancer = self.dancers[dancer_index]
                    dancer_index += 1
                else:  # if not, search for dancer object based on the name
                    dancer = self.find_dancer(dancer_name)
            # A line with "With " indicates the start of a new partner for the current dancer
            elif "With " in line:
                partner_name = self.get_dancer_name(line.strip(), line.find("With ") + 5)
                if "/" in partner_name:
                    partner = None
                elif len(partner_name) == 0:
                    partner = None
                else:
                    partner = self.find_dancer(partner_name)

            # look for lines with pro heat number information
            elif "Pro heat " in line:
                if partner is not None:
                    if partner_name > dancer_name:
                        h = self.build_heat("Pro heat", line, comp_ref)
                        if h is not None:
                            shirt_number = line.split("<td>")[2].split("</td>")[0]
                            self.build_heat_entry(h, dancer, partner, shirt_number)

            # look for lines with heat number information
            elif "Heat " in line:
                if partner is not None:
                    if partner_name > dancer_name:
                        # turn this line into a heat object and add it to the database
                        h = self.build_heat("Heat", line, comp_ref)
                        if h is not None:
                            shirt_number = line.split("<td>")[2].split("</td>")[0]
                            self.build_heat_entry(h, dancer, partner, shirt_number)

            # if we see the closing </div> tag, we are done with this dancer.
            elif "/div" in line:
                break;

        # return the name of the dancer, so the calling GUI can display it.
        return dancer_name


    def complete_processing(self):
        '''This method completes the processing of the Comp Manager heatlist,
           by closing the file and sorting the lists.'''
        return self.unmatched_heats
