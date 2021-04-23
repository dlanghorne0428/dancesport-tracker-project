import requests
import html

from rankings.models import Couple, Dancer
from comps.models.heat import Heat
from comps.models.heatlist_dancer import Heatlist_Dancer
from comps.heatlist.heatlist import Heatlist


class O2cmHeatlist(Heatlist):
    '''This is a derived class for reading Heatlist information from the O2cm website.
       It derives from the generic Heatlist class and presents the same interface.
       The class overrides the following methods:
       - open()
       - get_next_dancer()
       - complete_processing()
       '''
    def __init__(self):
        super().__init__()
        # the payload will contain the form values that we submit to obtain
        # the results. Initially it is empty
        self.payload = dict()
        self.url = None

    ############### EXTRACTION ROUTINES  #################################################
    # the following helper methods extract specific data items from the NdcaPremier site
    ######################################################################################
    def find_url(self, line):
        ''' In the O2cm HTML file format, the URL can be found
            on a line containing the key "action=" '''
        fields = line.split()
        for f in fields:
            if "action=" in f:
                self.url = f[len("action="):]


    def find_payload_field(self, line):
        ''' In the O2cm HTML file format, the values that get
            submitted to the form are found on lines containing "name=" and "value="
            Extract those pairs and store them in the payload dictionary.'''
        key = None
        value = None
        start_pos = line.find("name=") + len("name=")
        end_pos = line.find(' ', start_pos)
        key = line[start_pos:end_pos]
        start_pos = line.find("value=") + len("value=")
        end_pos = line.find('>', start_pos)
        value = line[start_pos:end_pos]
        self.payload[key] = value


    def get_partner(self, line):
        '''This method searches for the partner's name on the given line.'''
        if 'class=h5b' in line:
            start_pos = line.find("with: ") + len("with: ")
            if start_pos > -1:
                end_pos = line.find("</td>", start_pos)
                name = line[start_pos:-5]
                for d in self.dancers:
                    if d.name == name:
                        return d
                print("No match found for partner named", name)
                return "Unknown"
        else:
            return None


    def load_heat(self, line="", comp_ref=""):

        h = Heat()
        h.comp = comp_ref
        h.rounds = "F"      # assume final only

        if len(line) > 0:
            # find the heat number and convert to integer
            start_pos = line.find("[")
            if start_pos > -1:
                start_pos +=  len("[")
                end_pos = line.find(']', start_pos)
                number_string = line[start_pos:end_pos]
                if len(number_string) == 0:
                    h.heat_number = 0
                    h.extra = ""
                else:
                    try:
                        h.heat_number = int(number_string)
                        #print("Heat Number:", h.heat_number, end=" ")
                    except:
                        # extract non-digit info into the extra property
                        index = 0
                        while number_string[index].isdigit():
                            index += 1
                            h.heat_number = int(number_string[:index])
                            h.extra = number_string[index:]

            else:
                return None

            # find the heat time
            start_pos = end_pos = line.find(" @", start_pos) + 3
            if start_pos > 0:
                end_pos = line.find("M") + 1
                if end_pos > start_pos:
                    time_string = line[start_pos:end_pos]
                    h.set_time(time_string, "Saturday", "%I:%M %p")  # day not available in this format
                else:
                    return None

            else:
                return None

            # find the heat description information
            start_pos = end_pos + 1  # skip past the space after the M found above
            if start_pos > 0:
                end_pos = line.find("</td>", start_pos)
                if end_pos > start_pos:
                    h.info = line[start_pos:end_pos]
                    # find the heat description information
                    if "Professional" in h.info:
                        h.category = Heat.PRO_HEAT
                    elif "Solo " in h.info:
                        h.category = Heat.SOLO
                    else:
                        h.category = Heat.NORMAL_HEAT

                    # set the style and level if necessary
                    h.remove_info_prefix()
                    h.set_level()
                    h.set_dance_style()
                else:
                    return None
            else:
                return None
        else:
            return None
        return h


    def get_heats_for_dancer(self, dancer, heat_data, comp_ref):
        '''This method extracts heat information from the heat_data read in from a URL.
        The information is saved into the specified dancer object.'''
        fields = heat_data.split("<table")
        # isolate the list of heats
        if len(fields) == 3:
            rows = fields[2].split("</tr>")
            if len(rows) <= 1:
                print("Error parsing heat rows")
            row_index = 0
            partner = None
            # parse all the rows with heat information
            while row_index < len(rows) - 1:
                # check if this item specifies a partner name
                p = self.get_partner(rows[row_index])
                if p is not None:
                    partner = p

                elif "class=h5n" in rows[row_index]:
                    if partner is not None:
                        if partner.name > dancer.name:
                            # if this row is the start of a new heat, create a new heat object
                            heat = Heat()
                            heat = self.load_heat(rows[row_index], comp_ref)
                            if heat is not None:
                                if "Solo Star" in heat.info:
                                    h = None
                                else:
                                    h = self.add_heat_to_database(heat, comp_ref)
                                if h is not None:
                                    # this format doesn't store shirt numbers, use code instead
                                    self.build_heat_entry(h, dancer, partner, shirt_number=dancer.code)

                # go to the next row
                row_index += 1

        else:
            print("Error parsing heat data")


    ############### OVERRIDDEN METHODS  #######################################################
    # the following methods override the parent class to obtain data from the  NdcaPremier site
    ###########################################################################################
    def open(self, comp):
        '''This method obtains the name of the competition and a list of all the dancers.'''
        #extract comp name and comp_id from URL
        url = comp.heatsheet_url
        start_pos = url.find("event=") + len("event=")
        self.comp_id = url[start_pos:]
        self.comp_name = self.comp_id

        # open this URL to obtain a list of dancers
        response = requests.get(url)
        competitors = response.text.split("</OPTION>")
        #print(competitors[0])

        # get the URL from the <form> tag
        if "<form" in competitors[0]:
            self.find_url(competitors[0])
            #print(self.url)

        # get payload fields from the input tag
        if "<input" in competitors[-1]:
            self.find_payload_field(competitors[-1])
            #print(self.payload)

        for c in range(1,len(competitors) - 1):
            safe = html.unescape(competitors[c])
            d = Heatlist_Dancer()
            d.load_from_o2cm(safe)
            d.comp = comp
            d.alias = None
            try:
                code_num = int(d.code)
                if d.code != "0":
                    self.dancers.append(d)
            except:
                print("Invalid competitor", d.name, d.code)


    def load(self, url, heatlist_dancers):
        # load the list of dancers found by open()
        for d in heatlist_dancers:
            self.dancers.append(d)

        #extract comp name and comp_id from URL
        start_pos = url.find("event=") + len("event=")
        self.comp_id = url[start_pos:]
        self.comp_name = self.comp_id
        self.url = "http://entries.o2cm.com/default.asp"
        self.payload["event"] = self.comp_name


    def get_next_dancer(self, index, comp_ref):
        '''This method reads the heat information for the dancer at the given index.'''
        d = self.dancers[index]
        # build the payload.
        self.payload["selEnt"] = d.code
        self.payload["submit"] = "OK"
        #print(d, self.payload)
        #print(self.comp_id)

        # Make the HTML request as if the button was clicked on the form.
        # The data is returned as text
        response =  requests.post(self.url, data = self.payload)
        #print (response.text)
        self.get_heats_for_dancer(d, response.text, comp_ref)
        return d.name


    def complete_processing(self):
        return self.unmatched_entries
