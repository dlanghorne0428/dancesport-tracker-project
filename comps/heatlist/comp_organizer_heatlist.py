import requests

from django.db.models import Q
from rankings.models.couple import Couple
from rankings.models.dancer import Dancer
from comps.models.heat import Heat
from comps.models.heatlist_dancer import Heatlist_Dancer
from comps.models.heatlist_error import Heatlist_Error
from comps.heatlist.heatlist import Heatlist


class CompOrgHeatlist(Heatlist):
    '''This is a derived class for reading Heatlist information from a website in CompOrganizer format.
       It derives from the generic Heatlist class and presents the same interface.
       The class overrides the following methods:
       - open()
       - get_next_dancer()
       - complete_processing()
       '''
    def __init__(self):
        '''This method initializes the class'''
        super().__init__()
        self.base_url = None


    ############### EXTRACTION ROUTINES  #################################################
    # the following helper methods extract specific data items from the website
    ######################################################################################
    def get_partner(self, line):
        '''This method searches for the partner's name on the given line.'''
        #print("looking for partner: " + line)
        if "class='partner'" in line:
            start_pos = line.find("with ") + len("with ")
            substr = line[start_pos:]
            stripped = substr.strip()
            if len(stripped) > 0:
                return stripped
            else:
                return ""

        return None


    def load_heat(self, h, items, item_index, comp_ref):

        h.comp = comp_ref

        # get the heat number string and convert it to an integer
        start_pos = items[item_index+1].find("-heat") + len("-heat") + 2
        number_string = items[item_index+1][start_pos:]
        index = 0
        while not (number_string[index].isdigit()):
            index += 1
            if index == len(number_string):
                break
        # get the heat category
        category_string = number_string[:index]
        if category_string in ["Team match "]:
            h.heat_number = -1  # indicate an error
            h.category = None
        elif category_string == "Solo ":
            h.category = Heat.SOLO
        elif category_string == "Pro heat ":
            h.category = Heat.PRO_HEAT
        elif category_string == "Heat ":
            h.category = Heat.NORMAL_HEAT
        elif category_string == "Formation ":
            h.category = Heat.FORMATION

        try:
            h.heat_number = int(number_string[index:])
        except:
            # split out extra non-digit info from the heat number
            if index == len(number_string):
                h.heat_number = -1  # indicate an error
                h.category = None
                h.extra = number_string
            else:
                end_index = index
                while number_string[end_index].isdigit():
                    end_index += 1
                if end_index > index:
                    h.heat_number = int(number_string[index:end_index])
                else:
                    h.heat_number = 0
                h.extra = number_string[end_index:]
                h.extra = h.extra.replace("Ballroom ", "")
                if len(h.extra) >= 20:
                    h.extra = h.extra[:18] + h.extra[-1]                

        # save the heat time, determine if there are multiple rounds
        start_pos = items[item_index+2].find("-time") + len("-time") + 2
        heat_time = items[item_index+2][start_pos:]
        time_fields = heat_time.split()
        if len(time_fields) >= 2:
            if "<br" in time_fields[1]:
                time_string = time_fields[1].split("<br")[0]
            else:
                time_string = time_fields[1]
            day_of_week = time_fields[0]
        else:
            day_of_week = ""
            time_string = ""
        h.set_time(time_string, day_of_week)

        start_pos = items[item_index+4].find("-desc") + len("-desc") + 2
        h.info = items[item_index+4][start_pos:]
        h.remove_info_prefix()
        h.set_level()
        h.set_dance_style()


    def get_heats_for_dancer(self, dancer, heat_data, comp_ref, multis_only=None):
        '''This method extracts heat information from the heat_data.
           The information is saved into the specified dancer object.'''
        # all the heat information is in a series of table data cells.
        # split them into a list
        items = heat_data.split("</td>")
        if len(items) <= 1:
            print("Error parsing heat")
            self.build_heatlist_error(comp_ref, Heatlist_Error.PARSING_ERROR, dancer_name=dancer.name)

        item_index = 0
        partner = None
        # process all the list items
        while item_index < len(items):
            # check if this item specifies a partner name
            p_string = self.get_partner(items[item_index])
            if p_string is not None:
                if "/" in p_string:
                    partner = None
                elif len(p_string) > 0:
                    partner = self.find_dancer(p_string)
                    if partner is None:
                        print(dancer.name + " No partner found " + p_string)
                        in_database = Heatlist_Error.objects.filter(comp=comp_ref).filter(dancer=dancer.name)
                        if len(in_database) == 0:
                            self.build_heatlist_error(comp_ref, Heatlist_Error.NO_PARTNER_FOUND, dancer_name=dancer.name)

                else: # assign to {No, Partner}
                    partner_name = "{No, Partner}"
                    partner = self.find_dancer(partner_name)
                    print(dancer.name + " " + partner.name)

                # partner found, go to next item
                item_index += 1

            # no partner, check if this item has the start of a new heat
            elif "heatlist-sess" in items[item_index]:
                if partner is not None:
                    if partner.name > dancer.name:
                        # build heat object, which takes up the next five items
                        heat = Heat()
                        self.load_heat(heat, items, item_index, comp_ref)
                        if "Solo Star" in heat.info:
                            heat.category = Heat.NORMAL_HEAT
                        if heat.category is not None:
                            h = self.add_heat_to_database(heat, comp_ref, multis_only)
                            if h is not None:
                                start_pos = items[item_index+3].find("-numb") + len("-numb") + 2
                                shirt_number = items[item_index+3][start_pos:]
                                self.build_heat_entry(h, dancer, partner, shirt_number)
                    else:
                        #print("Skipping: " + dancer.name + " greater than " + partner.name)
                        #print("index:" + str(item_index) + " items length: " + str(len(items)))
                        pass
                item_index += 5

            else:
                # try the next item
                item_index += 1


    ############### OVERRIDDEN METHODS  #######################################################
    # the following methods override the parent class to obtain data from the website
    ###########################################################################################
    def open(self, comp):
        '''This method obtains the name of the competition and a list of all the dancers.'''
        #extract comp name from URL
        url = comp.heatsheet_url
        print(comp.heatsheet_url)
        response = requests.get(url, timeout=5.0)
        lines = response.text.splitlines()
        for l in lines:
            if "var cmid" in l:
                # this line is in this format"
                # var cmid = "beachbash2019";
                # extract the name from between the quotes
                self.comp_name = l.split('= "')[1][:-2]
                print(self.comp_name)
                break

        end_pos = url.find("/pages")

        # save this string for later use
        self.base_url = url[:end_pos] + "/scripts/heatlist_scrape.php?comp=" + self.comp_name
        print(self.base_url)

        # open the base URL to extract a list of dancers
        response = requests.get(self.base_url, timeout=5.0)
        competitors = response.text.split("},")
        print("Competitors = " + str(len(competitors)))
        for c in range(len(competitors)):
            start_pos = competitors[c].find('"id')
            d = Heatlist_Dancer()
            d.load_from_comp_org(competitors[c][start_pos:])
            d.comp = comp
            d.alias = None
            try:
                code_num = int(d.code)
                if d.code != "0":
                    self.dancers.append(d)
                else:
                    print("Invalid competitor " + d.name + " " + d.code)
                    self.build_heatlist_error(comp, Heatlist_Error.NO_CODE_FOUND, dancer_name=d.name)
            except:
                print("Invalid competitor " + d.name + " " + d.code)
                self.build_heatlist_error(comp, Heatlist_Error.NO_CODE_FOUND, dancer_name=d.name)


    def load(self, url, heatlist_dancers):
        # load the list of dancers found by open()
        for d in heatlist_dancers:
            self.dancers.append(d)

        #extract comp name from URL
        response = requests.get(url,timeout=5.0)
        lines = response.text.splitlines()
        for l in lines:
            if "var cmid" in l:
                # this line is in this format"
                # var cmid = "beachbash2019";
                # extract the name from between the quotes
                self.comp_name = l.split('= "')[1][:-2]
                break

        # save this string for later use in URL access
        end_pos = url.find("/pages")
        self.base_url = url[:end_pos] + "/scripts/heatlist_scrape.php?comp=" + self.comp_name
        print(self.base_url)


    def get_next_dancer(self, dancer_index, comp_ref, multis_only=None):
        '''This method reads the heat information for the dancer at the given index.'''
        d = self.dancers[dancer_index]
        url = self.base_url + "&competitor=" + d.code
        response = requests.get(url,timeout=10.0)
        self.get_heats_for_dancer(d, response.text, comp_ref, multis_only)
        return d.name


    def complete_processing(self):
        '''This method sorts data structures after all the heat information
           has been obtained from the website.'''
        return self.unmatched_entries
