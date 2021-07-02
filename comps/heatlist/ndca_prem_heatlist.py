import requests
import html

from rankings.models import Couple, Dancer
from comps.models.heat import Heat
from comps.models.heatlist_dancer import Heatlist_Dancer
from comps.models.heatlist_error import Heatlist_Error
from comps.heatlist.heatlist import Heatlist


class NdcaPremHeatlist(Heatlist):
    '''This is a derived class for reading Heatlist information from the NdcaPremier website.
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


    def load_heat(self, h, line="", comp_ref=""):

        h.comp = comp_ref
        h.rounds = "F"      # assume final only
        if len(line) > 0:
            # split the heat information into fields
            cols = line.split("</td>")
            for c in cols:
                # find the heat time
                start_pos = c.find("-time-round")
                if start_pos > -1:
                    start_pos += len("-time-round") + 2
                    end_pos = c.find("</div>")
                    time_string = c[start_pos:end_pos]
                    time_fields = time_string.split()
                    day_of_week = time_fields[0].split(',')[0]
                    time_string = time_fields[1] + time_fields[2]
                    h.set_time(time_string, day_of_week)
                    continue

                # find the heat number and convert to integer
                start_pos = c.find("-heat")
                if start_pos > -1:
                    start_pos +=  len("-heat") + 2
                    number_string = c[start_pos:]
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
                    continue

                # find the heat description information
                start_pos = c.find("-desc")
                if start_pos > -1:
                    start_pos += len("-desc") + 2
                    h.info = c[start_pos:]
                    if "Professional" in h.info:
                        h.category = Heat.PRO_HEAT
                    elif "Solo " in h.info:
                        h.category = Heat.SOLO
                    elif "Formation " in h.info:
                        h.category = Heat:FORMATION        
                    else:
                        h.category = Heat.NORMAL_HEAT

                    # set the style and level if necessary
                    h.remove_info_prefix()
                    h.set_level()
                    h.set_dance_style()


    def get_heats_for_dancer(self, dancer, heat_data, comp_ref):
        '''This method extracts heat information from the heat_data read in from a URL.
        The information is saved into the specified dancer object.'''
        fields = heat_data.split("<table>")
        # isolate the list of heats
        if len(fields)  == 2:
            rows = fields[1].split("</tr>")
            if len(rows) <= 1:
                print("Error parsing heat rows")
                in_database = Heatlist_Error.objects.filter(comp=comp_ref).filter(dancer=dancer.name)
                if len(in_database) == 0:
                    self.build_heatlist_error(comp_ref, Heatlist_Error.PARSING_ERROR, dancer_name=dancer.name)

            row_index = 0
            partner = None
            # parse all the rows with heat information
            while row_index < len(rows) - 1:
                # check if this item specifies a partner name
                p = self.get_partner(rows[row_index])
                if p is not None:
                    partner = p

                elif "heatlist-sess" in rows[row_index]:
                    if partner is None:
                        partner = self.dancers[-1]
                        print (dancer.name, partner.name)
                    if partner.name > dancer.name:
                        # if this row is the start of a new heat, create a new heat object
                        heat = Heat()
                        self.load_heat(heat, rows[row_index], comp_ref)
                        # if "Solo Star" in heat.info:
                        #     h = None
                        # else:
                        h = self.add_heat_to_database(heat, comp_ref)
                        if h is not None:
                            # this format doesn't store shirt numbers, use code instead
                            self.build_heat_entry(h, dancer, partner, shirt_number=dancer.code)

                # go to the next row
                row_index += 1

        else:
            print("Error parsing heat data")
            in_database = Heatlist_Error.objects.filter(comp=comp_ref).filter(dancer=dancer.name)
            if len(in_database) == 0:
                self.build_heatlist_error(comp_ref, Heatlist_Error.PARSING_ERROR, dancer_name=dancer.name)


    ############### OVERRIDDEN METHODS  #######################################################
    # the following methods override the parent class to obtain data from the  NdcaPremier site
    ###########################################################################################
    def open(self, comp):
        '''This method obtains the name of the competition and a list of all the dancers.'''
        #extract comp name and comp_id from URL
        url = comp.heatsheet_url
        start_pos = url.find("cyi=") + len("cyi=")
        self.comp_id = url[start_pos:]
        #self.comp_name = self.get_comp_name(self.comp_id)

        # open this URL to obtain a list of dancers
        url = "http://www.ndcapremier.com/scripts/competitors.asp?cyi=" + self.comp_id
        print(url)
        response = requests.get(url)
        competitors = response.text.split("</a>")
        for c in range(len(competitors) - 1):
            if 'class="team"' in competitors[c]:
                continue
            safe = html.unescape(competitors[c])
            d = Heatlist_Dancer()
            d.load_from_ndca_premier(safe)
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

        #extract comp name and comp_id from URL
        start_pos = url.find("cyi=") + len("cyi=")
        self.comp_id = url[start_pos:]
        #self.comp_name = self.get_comp_name(self.comp_id)


    def get_next_dancer(self, index, comp_ref):
        '''This method reads the heat information for the dancer at the given index.'''
        d = self.dancers[index]
        url = "http://ndcapremier.com/scripts/heatlists.asp?cyi=" + self.comp_id + "&id=" + d.code + "&type=competitor"
        response = requests.get(url)
        self.get_heats_for_dancer(d, response.text, comp_ref)
        return d.name


    def complete_processing(self):
        return self.unmatched_entries
