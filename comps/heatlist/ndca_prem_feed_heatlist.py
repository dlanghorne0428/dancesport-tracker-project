import requests
import html
import json

from rankings.models.couple import Couple
from rankings.models.dancer import Dancer
from comps.models.heat import Heat
from comps.models.heatlist_dancer import Heatlist_Dancer
from comps.models.heatlist_error import Heatlist_Error
from comps.heatlist.heatlist import Heatlist


class NdcaPremFeedHeatlist(Heatlist):
    '''This is a derived class for reading Heatlist information in the new "Feed" format
       of the NDCAPremier website
       It derives from the generic Heatlist class and presents the same interface.
       The class overrides the following methods:
       - open()
       - get_next_dancer()
       - complete_processing()
       '''
    def __init__(self):
        super().__init__()

    ############### EXTRACTION ROUTINES  #################################################
    # the following helper methods extract specific data items from the NdcaPremier site
    ######################################################################################
    def get_comp_name(self, comp_id):
        '''This method obtains the name of the competition based on the ID found on the website.'''
        url = "http://www.ndcapremier.com/scripts/compyears.asp?cyi=" + comp_id
        response = requests.get(url)
        lines = response.text.splitlines()
        for l in lines:
            start_pos = l.find("<comp_name>")
            if start_pos > -1:
                start_pos += len("<comp_name>")
                end_pos = l.find("</comp_name>")
                comp_name = l[start_pos:end_pos]
                break
        return comp_name


    def get_partner(self, line):
        '''This method searches for the partner's name on the given line.'''
        if 'partner-name' in line:
            fields = line.split("</tr>")
            for f in fields:
                start_pos = f.find("With ") + len("With ")
                if start_pos > -1 + len("With "):
                    name = f[start_pos:-5]
                    p = self.find_dancer(name, format_needed=True)
                    if p is not None:
                        return p

        return None


    def load_heat(self, h, json_record="", comp_ref=""):

        h.comp = comp_ref
        h.rounds = "F"      # assume final only

        # find the heat number and convert to integer
        number_string = json_record['Heat']
        if len(number_string) == 0:
            h.heat_number = 0
            h.extra = ""
        else:
            try:
                h.heat_number = int(number_string)
            except:
                # extract non-digit info into the extra property
                index = 0
                while number_string[index].isdigit():
                    index += 1
                if index == 0:
                    h.heat_number = 0
                    h.extra = "TBD"
                else:
                    h.heat_number = int(number_string[:index])
                    h.extra = number_string[index:]

        # find the heat description information
        h.info = json_record['Event_Name']
        if "Professional" in h.info:
            h.category = Heat.PRO_HEAT
        elif "Solo Single " in h.info:
            h.category = Heat.NORMAL_HEAT
        elif "Solo " in h.info and "Solo Star" not in h.info:
            h.category = Heat.SOLO
        elif "Formation " in h.info:
            h.category = Heat.FORMATION
        else:
            h.category = Heat.NORMAL_HEAT

        if h.extra == "" and 'Floor' in json_record:
            if json_record['Floor'] is not None:
                h.extra = '[' + json_record['Floor'] + ']'

        if h.extra == "" and 'Ballroom' in json_record:
            if json_record['Ballroom'] is not None:
                h.extra = '[' + json_record['Ballroom'] + ']'

        # find the heat time
        time_string = json_record['Rounds'][0]['Round_Time']
        time_fields = time_string.split()
        day_of_week = ""
        the_date = time_fields[0]
        the_time = time_fields[1] + time_fields[2]
        h.set_time(the_time, day_of_week, time_format="%I:%M:%S%p", date_string=the_date)

        # set the style and level if necessary
        h.remove_info_prefix()
        h.set_level()
        h.set_dance_style()
        #print(str(h.category) + ' ' + str(h.heat_number) +  ' ' + h.info)


    def get_heats_for_dancer(self, dancer, heat_data, comp_ref, multis_only=None):
        '''This method extracts heat information from the heat_data read in from a URL.
        The information is saved into the specified dancer object.'''
        try:
            json_data = json.loads(heat_data)
        except:
            print("Unable to parse heatsheet - " + dancer.name)
            return

        if json_data['Status'] == 0:
            # no heatlist for this competitor
            print("No heatlist - " + dancer.name)
            return

        json_record= json.loads(heat_data)

        if dancer.name == "Maj, Alexia":
            print(json_record['Result']['Entries'])
            
        for entry in json_record['Result']['Entries']:
            # find partner name
            num_participant_records = len(entry['Participants'])
            if num_participant_records == 0:
                partner_name = "{No, Partner}"
            elif num_participant_records > 1:
                print(entry['Participants'])
                # error case
                partner_name = "None"
            else:
                p = entry['Participants'][0]
                partner_name_list = p['Name']
                partner_name = ""
                if len(partner_name_list) == 0:
                    partner_name = "{No, Partner}"
                elif len(partner_name_list) == 1:
                    partner_name = "., " + partner_name_list[0]
                elif len(partner_name_list) == 2:
                    if partner_name_list[0] is not None and partner_name_list[1] is not None:
                        partner_name = partner_name_list[1] + ", " + partner_name_list[0]
                    else:
                        partner_name = "., " + partner_name_list[0]

            partner = self.find_dancer(partner_name, format_needed=False) # for now
            if partner is None:
                #print("Error parsing partner_name", partner_name_list, partner_name)
                in_database = Heatlist_Error.objects.filter(comp=comp_ref).filter(dancer=dancer.name)
                if len(in_database) == 0:
                    self.build_heatlist_error(comp_ref, Heatlist_Error.PARSING_ERROR, dancer_name=dancer.name)
            elif dancer.name > partner.name:
                #print(dancer.name + " greater than " + partner_name + ". Skipping!")
                pass
            else:
                #print(dancer.name + " with " + partner.name)
                for e in entry['Events']:
                    shirt_number = e['Bib']
                    heat = Heat()
                    self.load_heat(heat, e, comp_ref)
                    h = self.add_heat_to_database(heat, comp_ref, multis_only)
                    if h is not None:
                        self.build_heat_entry(h, dancer, partner, shirt_number=shirt_number)





    ############### OVERRIDDEN METHODS  #######################################################
    # the following methods override the parent class to obtain data from the  NdcaPremier site
    ###########################################################################################
    def open(self, comp):
        '''This method obtains the name of the competition and a list of all the dancers.'''
        #extract comp name and comp_id from URL
        url = comp.heatsheet_url
        start_pos = url.find("cyi=") + len("cyi=")
        self.comp_id = url[start_pos:]

        # open this URL to obtain a list of dancers in JSON format
        url= "http://ndcapremier.com/feed/heatlists/?cyi=" + self.comp_id
        response = requests.get(url)
        data = json.loads(response.text)
        print("Dancers found: " + str(len(data['Result'])))
        for c in data['Result']:
            if c['Type'] != 'Attendee':
                print("Skipping: " + c['Type'] + ' ' + str(c['Name']))
                continue;
            d = Heatlist_Dancer()
            d.load_from_ndca_premier_feed(c)
            d.comp = comp
            d.alias = None
            try:
                code_num = int(d.code)
                if d.code != "0":
                    self.dancers.append(d)
            except:
                print("Invalid competitor " + d.name + " " + d.code)
                self.build_heatlist_error(comp, Heatlist_Error.NO_CODE_FOUND, dancer_name=d.name)


    def load(self, url, heatlist_dancers):
        # load the list of dancers found by open()
        for d in heatlist_dancers:
            self.dancers.append(d)

        #extract comp_id from URL
        start_pos = url.find("cyi=") + len("cyi=")
        self.comp_id = url[start_pos:]


    def get_next_dancer(self, index, comp_ref, multis_only=None):
        '''This method reads the heat information for the dancer at the given index.'''
        d = self.dancers[index]
        if d.code != "0":
            url= "http://ndcapremier.com/feed/heatlists/?cyi=" + self.comp_id + "&id=" + d.code + "&type=attendee"
            response = requests.get(url)
            self.get_heats_for_dancer(d, response.text, comp_ref, multis_only)
        return d.name


    def complete_processing(self):
        return self.unmatched_entries
