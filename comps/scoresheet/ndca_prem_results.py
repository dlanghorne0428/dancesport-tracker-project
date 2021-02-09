import requests
from comps.scoresheet.results_processor import Results_Processor
from comps.scoresheet.calc_points import calc_points
from comps.models.heatlist_dancer import Heatlist_Dancer


class NdcaPremEvent():
    '''An event is basically the description of a heat.
       For example, L-A1 Bronze Smooth 3-Dance Challenge (W/T/F).
       There may be more than one event in a given heat of a competition.
       This class stores the name and ID number of an event.'''
    def __init__(self, line):
        fields = line.split(">")
        # extract the event id for future use
        start_pos = fields[0].find("eventid=") + len("eventid=") + 1
        self.id = fields[0][start_pos:-1]
        # extract the event name
        self.name = fields[1]


class NdcaPremResults(Results_Processor):
    '''This class processes the results from the NDCA Premier site...'''
    def __init__(self):
        super().__init__()

        # Keep a list of event objects (ID and name)
        self.events = []

        # Event results are categorized, for example "Professional Couple American Smooth"
        # Keep a list of those categories.
        self.categories = []

        # save the competition ID in order to request results for a given dancer
        self.comp_id = None

        # get access to format_name
        self.hld = Heatlist_Dancer()


    def get_comp_name(self, comp_id):
        '''This method obtains the name of the competition based on the ID.'''
        url = "http://www.ndcapremier.com/scripts/compyears.asp?cyi=" + comp_id
        response = requests.get(url)
        lines = response.text.splitlines()
        # the comp name is enclosed in an HTML tag
        for l in lines:
            start_pos = l.find("<comp_name>")
            if start_pos > -1:
                start_pos += len("<comp_name>")
                end_pos = l.find("</comp_name>")
                comp_name = l[start_pos:end_pos]
                break
        return comp_name


    def temp_result(self, rounds, accum_value):
        '''This method builds a temporary result string based on the round that
           the couple was eliminated and the number of recall votes'''
        if rounds == "S":
            return "Semis-" + accum_value
        elif rounds == "Q":
            return "quarters-" + accum_value
        elif rounds == "R3":
            return "round 3-" + accum_value
        elif rounds == "R2":
            return "round 2-" + accum_value
        else:
            return "round 1-" + accum_value


    def process_couple(self, entries, couple_field, result_str):
        # find the couple's shirt number
        sub_fields = couple_field.split(" &amp; ")
        first_space = sub_fields[0].find(" ")
        shirt_number = sub_fields[0][:first_space]

        # find the names of the couple and format them
        dancer_name_list = list()
        dancer_name = sub_fields[0][first_space+1:]
        for s in range(1, len(dancer_name.split())):
            dancer_name_list.append(self.hld.format_name(orig_name=dancer_name, simple=False, split_on=s))
        if len(dancer_name_list) == 0:
            dancer_name_list.append(dancer_name)
        partner_name_list = list()
        partner_name = sub_fields[1]
        for s in range(1, len(partner_name.split())):
            partner_name_list.append(self.hld.format_name(orig_name=partner_name, simple=False, split_on=s))
        if len(partner_name_list) == 0:
            partner_name_list.append(partner_name)

        # look for this couple in the entries and add the result and shirt number
        for entry in entries:
            if str(entry.couple.dancer_1) in dancer_name_list or str(entry.couple.dancer_2) in dancer_name_list or \
               str(entry.couple.dancer_1) in partner_name_list or str(entry.couple.dancer_2) in partner_name_list:
                entry.shirt_number = shirt_number
                if len(entry.result) == 0:
                    entry.result = result_str
                break
        else:
            # couple not found, create a late entry
            print("Could not find " + partner_name + " and " + dancer_name)
            couple_names = [dancer_name_list[0], partner_name_list[0]]
            self.build_late_entry(self.heat, shirt_number, couple_names, result_str)


    def update_scoring(self, e):
        '''This method updates the result and points for a given entry, e.'''
        if e.points is None and len(e.result) > 0:
            if e.result.startswith("S"):
                accum_value = e.result[len("Semis-"):]
                e.result = "Semis"
                placement = -2
            elif e.result.startswith("q"):
                accum_value = e.result[len("quarters-"):]
                e.result = "quarters"
                placement = -1
            elif e.result.startswith("round 3-"):
                accum_value = e.result[len("round 3-"):]
                e.result = "round 3"
                placement = -3
            elif e.result.startswith("round 2-"):
                accum_value = e.result[len("round 2-"):]
                e.result = "round 2"
                placement = -5
            elif e.result.startswith("round 1-"):
                accum_value = e.result[len("round 1-"):]
                e.result = "round 1"
                placement = -10
            else:
                try:
                    placement = int(e.result)
                    accum_value = 0
                except:
                    return None
            e.points = calc_points(self.heat.base_value, placement, num_competitors=self.entries_in_event, rounds=self.heat.rounds, accum=int(accum_value))
            #print(str(e.couple) + " finish " + e.result + " for " + str(e.points) + " points")
            e.save()
            return e.result
        else:
            return None


    def process_scoresheet_for_event(self, entries, event):
        '''This is the method that requests and processes the scoresheet for a
           particular event. On the NDCA Premier site, the scoresheets are
           organized by event, not by dancer name.'''

        # on the NDCA Premier site, the Final round comes first.
        looking_for_final_round = True
        looking_for_final_summary = False
        looking_for_final_dance = False
        looking_for_result_column = False
        looking_for_recall_column = False
        looking_for_finalists = False
        looking_for_quarterfinal = False
        looking_for_prelim_round = False
        process_finalists = False
        looking_for_semifinal = False
        self.entries_in_event = 0
        self.heat = entries.first().heat

        # build the URL based on comp ID and event ID
        url = "http://www.ndcapremier.com/scripts/results.asp?cyi=" + self.comp_id + "&event=" + event.id
        # get the number of dances in this event. For example W,T,F is 3 dances.
        num_dances = event.name.count(",") + 1

        # request the scoresheet and split the response into lines
        response = requests.get(url)
        lines = response.text.splitlines()
        i = 0

        # loop through all the lines
        while i < len(lines):
            l = lines[i]
            if looking_for_final_round:
                if 'class="roundHeader"' in l:
                    # once the find the title with the final results, look for the summary.
                    looking_for_final_summary = True
                    looking_for_final_round = False
                else:
                    i += 1
            elif looking_for_final_summary:
                if "Final Summary" in l:
                    # once the summary header is found, look for the result columen
                    looking_for_final_summary = False
                    looking_for_result_column = True
                    col_count = 0
                else:
                    i += 1
            elif looking_for_result_column:
                fields = l.split("</th>")
                # count the number of columns until the result column is found
                col_count += len(fields) - 1
                if "Final Result" in l:
                    # once the result column is found, process each finalist
                    looking_for_result_column = False
                    looking_for_finalists = True
                else:
                    i += 1
            elif looking_for_recall_column:
                # when looking for recalls, determine the number of columns
                fields = l.split("</th>")
                recall_column = len(fields) - 2
                accum_column = recall_column - 1
                i += 1
                looking_for_recall_column = False
                # start looking for couples that were eliminated in the current round
                looking_for_eliminations = True
            elif looking_for_finalists:
                # skip the first field, it closes out the previous header row
                rows = fields[-1].split("</tr>")[1:]
                # once the closing table tag is found we have one row per couple
                if "</table>" in rows[-1]:
                    rows = rows[:-1]
                    looking_for_finalists = False
                    # after processing the final results, look for possible semifinal
                    looking_for_semifinal = True
                else:
                    i += 1
                # loop through all the couples
                for r in rows:
                    # split the row into columns
                    fields = r.split("</td>")
                    # get the couple name and number from the first column
                    couple_field = fields[0].split("<td>")[1]
                    # get the result info from the last column
                    result_place = fields[col_count-1].split("<td>")[1]
                    self.entries_in_event += 1

                    # process this couple
                    self.process_couple(entries, couple_field, result_place)

            elif looking_for_semifinal:
                # if we find a semifinal, set the rounds and look for the results of this round
                if 'class="roundHeader"' in l:
                    #print("Found semi-final")
                    self.heat.rounds = "S"
                    looking_for_semifinal = False
                    looking_for_final_dance = True
                    dance_count = 0
                else:
                    i += 1
            elif looking_for_quarterfinal:
                # if we find a quarter final, set the rounds and look for the results of this round
                if 'class="roundHeader"' in l:
                    #print("Found quarter-final")
                    self.heat.rounds = "Q"
                    looking_for_quarterfinal = False
                    looking_for_final_dance = True
                    dance_count = 0
                else:
                    i += 1
            elif looking_for_prelim_round:
                # if we find an earlier round, set the rounds and look for the results of this round
                if 'class="roundHeader">Third' in l:
                    #print("Found Third Round")
                    self.heat.rounds = "R3"
                    looking_for_prelim_round = False
                    looking_for_final_dance = True
                    dance_count = 0
                elif 'class="roundHeader">Second' in l:
                    #print("Found Second Round")
                    if self.heat.rounds != "R3":
                        self.heat.rounds = "R32"
                    else:
                        self.heat.rounds = "R2"
                    looking_for_prelim_round = False
                    looking_for_final_dance = True
                    dance_count = 0
                elif 'class="roundHeader">First' in l:
                    #print("Found First Round")
                    if self.heat.rounds == "R32":
                        self.heat.rounds = "R321"
                    elif self.heat.rounds == "R2":
                        self.heat.rounds = "R21"
                    else:
                        self.heat.rounds = "R1"
                    looking_for_prelim_round = False
                    looking_for_final_dance = True
                    dance_count = 0
                else:
                    i += 1
            elif looking_for_final_dance:
                if 'class="eventResults"' in l:
                    dance_count += 1
                # TODO: some prelim rounds may not dance all the dances. Need to handle this.
                if dance_count == num_dances:
                    looking_for_final_dance = False
                    looking_for_recall_column = True
                i += 1
            elif looking_for_eliminations:
                # once we find the results of an early round, look for earlier rounds
                if "</table>" in l:
                    looking_for_eliminations = False
                    if self.heat.rounds == "S":
                        looking_for_quarterfinal = True
                    elif self.heat.rounds == "Q":
                        looking_for_prelim_round = True
                    elif self.heat.rounds == "R3":
                        looking_for_prelim_round = True
                    elif self.heat.rounds == "R2":
                        looking_for_prelim_round = True
                else:
                    # process the result of the next couple
                    fields = l.split("</td>")
                    # get the couple name and shirt number
                    couple_field = fields[0].split("<td>")[1]
                    # determine if the couple was recalled
                    recall_place = fields[recall_column].split("<td>")[1]
                    if recall_place != "Recall":
                        # if the couple was not recalled determine how many votes they got
                        accum_value = fields[accum_column].split("<td>")[1]
                        result_str = self.temp_result(self.heat.rounds, accum_value)

                        # process this couple
                        self.process_couple(entries, couple_field, result_str)

                    i += 1
            else:
                i+= 1

        # entire scoresheet was processed
        # for each entry in the event, extract the recall votes and calculate the points
        event_result = None
        for e in entries:
            temp_result = self.update_scoring(e)
            if event_result is None:
                event_result = temp_result
        for late_entry in self.late_entries:
            temp_result = self.update_scoring(late_entry)
            if temp_result is not None:
                print("LATE ENTRY SCORING: " + late_entry.result + " " + str(late_entry.points))
                if event_result is None:
                    event_result = temp_result

        return event_result


    def determine_heat_results(self, entries):
        '''This method obtains the results for all entries in the event.'''
        # process the scoresheet for each of those events.
        if entries.count() > 0:
            for entry in entries:
                if entry.points is None:
                    event_name = entries.first().heat.info
                    for event in self.events:
                        if event.name == event_name:
                            #print("Processing " + event.name)
                            event_result = self.process_scoresheet_for_event(entries, event)
                            if event_result is not None:
                                for entry in entries:
                                    if entry.points is None:
                                        entry.result = "DNP"

                            return event_result

                    else:
                        print("ERROR: Could not find event " + event_name)
                        return None
            else: # all entries have results already
                return None
        else:
            print("ERROR: No entries in event " + event.name)
            return None


    def open(self, url):
        '''This method opens the results page for a competition on the NDCA Premier site
           It extracts all the event names and associated IDs.'''
        #extract comp name and comp_id from URL
        start_pos = url.find("cyi=") + len("cyi=")
        self.comp_id = url[start_pos:]
        self.comp_name = self.get_comp_name(self.comp_id)
        # request that page
        url = "http://www.ndcapremier.com/scripts/event_categories.asp?cyi=" + self.comp_id
        response = requests.get(url)
        # split the response into event categories
        categories = response.text.split("</a>")
        for cat_link in categories:
            if len(cat_link) > 0:
                start_pos = cat_link.find("style=") + len("style=") + 1
                end_pos = cat_link.find('">', start_pos)
                category = cat_link[start_pos:end_pos]
                self.categories.append(category)

        # build a list of events, by looping through the event categories.
        for cat in self.categories:
            url = "http://www.ndcapremier.com/scripts/event_list.asp?cyi=" + self.comp_id + "&cat=" + cat
            response = requests.get(url)
            event_lines = response.text.split("</a>")
            for e in event_lines:
                if len(e) > 0:
                    event = NdcaPremEvent(e)
                    #print(event.name + " " +  event.id)
                    self.events.append(event)
