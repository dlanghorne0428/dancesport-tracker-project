import requests
from .calc_points import calc_points
#from rankings.models import Dancer
from comps.models import Heat, HeatlistDancer
#from dancer_list import Dancer_List, Dancer_Type

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


class NdcaPremResults():
    '''This class processes the results from the NDCA Premier site...'''
    def __init__(self):
        # Keep a list of event objects (ID and name)
        self.events = []

        # Event results are categorized, for example "Professional Couple American Smooth"
        # Keep a list of those categories.
        self.categories = []

        # save the competition ID in order to request results for a given dancer
        self.comp_id = None

        # get access to format_name
        self.hld = HeatlistDancer()


    # def order_pro_am_couple(self, entry):
    #     '''This method uses the list of instructors to put the student first.'''
    #     if entry.dancer in self.instructors.names:
    #         entry.swap_names()
    #     elif entry.partner not in self.instructors.names:
    #         print("Instructor Unknown: ", entry.dancer, "or", entry.partner)


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


    def process_scoresheet_for_event(self, entries_in_event, event):
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
        total_entries = 0
        heat = entries_in_event.first().heat

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
                    # don't need to convert, leave it as a string
                    # try:
                    #     result_place = int(result_field)
                    # except:
                    #     result_place = None
                    total_entries += 1

                    # find the couple's shirt number
                    sub_fields = couple_field.split(" &amp; ")
                    first_space = sub_fields[0].find(" ")
                    shirt_number = sub_fields[0][:first_space]

                    # find the names of the couple and format them
                    dancer_name_list = list()
                    dancer_name = sub_fields[0][first_space+1:]
                    for s in range(1, len(dancer_name.split())):
                        dancer_name_list.append(self.hld.format_name(orig_name=dancer_name, simple=False, split_on=s))
                    partner_name_list = list()
                    partner_name = sub_fields[1]
                    for s in range(1, len(partner_name.split())):
                        partner_name_list.append(self.hld.format_name(orig_name=partner_name, simple=False, split_on=s))
                    #print(dancer_name, "and", partner_name)
                    #print(dancer_name_list)
                    #print(partner_name_list)

                    # look for this couple in the entries and add the result and shirt number
                    for entry in entries_in_event:
                        if str(entry.couple.dancer_1) in dancer_name_list or str(entry.couple.dancer_2) in dancer_name_list or \
                           str(entry.couple.dancer_1) in partner_name_list or str(entry.couple.dancer_2) in partner_name_list:
                            #print("Found " + str(entry.couple) + ": " + result_place)
                            entry.shirt_number = shirt_number
                            if len(entry.result) == 0:
                                entry.result = result_place
                            break
                    else:
                        # couple not found, create a late entry
                        print("Could not find", partner_name, "and", dancer_name)
                        xyz()
                        h = heat_report.build_late_entry()
                        h.dancer = dancer_name_list[0]
                        h.partner = partner_name_list[0]
                        h.shirt_number = shirt_number
                        h.result = result_place
                        h.code = "LATE"
                        heat_report.append(h)

            elif looking_for_semifinal:
                # if we find a semifinal, set the rounds and look for the results of this round
                if 'class="roundHeader"' in l:
                    print("Found semi-final")
                    heat.rounds = "S"
                    looking_for_semifinal = False
                    looking_for_final_dance = True
                    dance_count = 0
                else:
                    i += 1
            elif looking_for_quarterfinal:
                # if we find a quarter final, set the rounds and look for the results of this round
                if 'class="roundHeader"' in l:
                    print("Found quarter-final")
                    heat.rounds = "Q"
                    looking_for_quarterfinal = False
                    looking_for_final_dance = True
                    dance_count = 0
                else:
                    i += 1
            elif looking_for_prelim_round:
                # if we find an earlier round, set the rounds and look for the results of this round
                if 'class="roundHeader">Third' in l:
                    print("Found Third Round")
                    heat.rounds = "R3"
                    looking_for_prelim_round = False
                    looking_for_final_dance = True
                    dance_count = 0
                elif 'class="roundHeader">Second' in l:
                    print("Found Second Round")
                    heat.rounds = "R2"
                    looking_for_prelim_round = False
                    looking_for_final_dance = True
                    dance_count = 0
                elif 'class="roundHeader">First' in l:
                    print("Found First Round")
                    if heat.rounds == "R3":
                        heat.rounds = "R321"
                    elif heat.rounds == "R2":
                        heat.rounds = "R21"
                    else:
                        heat.rounds = "R1"
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
                    if heat.rounds == "S":
                        looking_for_quarterfinal = True
                    elif heat.rounds == "Q":
                        looking_for_prelim_round = True
                    elif heat.rounds == "R3":
                        looking_for_prelim_round = True
                    elif heat.rounds == "R2":
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

                        # extract the shirt number
                        sub_fields = couple_field.split(" &amp; ")
                        first_space = sub_fields[0].find(" ")
                        shirt_number = sub_fields[0][:first_space]

                        # extract the names of the couple
                        dancer_name_list = list()
                        dancer_name = sub_fields[0][first_space+1:]
                        for s in range(1, len(dancer_name.split())):
                            dancer_name_list.append(Dancer.format_name(dancer_name, split_on=s))
                        partner_name_list = list()
                        partner_name = sub_fields[1]
                        for s in range(1, len(partner_name.split())):
                            partner_name_list.append(Dancer.format_name(partner_name, split_on=s))

                        # look for the couple in the heat report
                        for index in range(heat_report.length()):
                            entry = heat_report.entry(index)
                            if entry.dancer in dancer_name_list:
                                entry.shirt_number = shirt_number
                                # put the couple names in the right order
                                if entry.category == "Heat" and not entry.amateur_heat():
                                    self.order_pro_am_couple(entry)
                                # if the couple already has a result, they were not recalled so don't overwrite it
                                if entry.result is None:
                                    entry.result = self.temp_result(heat_report.rounds(), accum_value)
                                break
                            elif entry.partner in dancer_name_list:
                                entry.shirt_number = shirt_number
                                if entry.category == "Heat" and not entry.amateur_heat():
                                    self.order_pro_am_couple(entry)
                                else:
                                    entry.swap_names()
                                if entry.result is None:
                                    entry.result = self.temp_result(heat_report.rounds(), accum_value)
                                break
                        else:
                            # if no matching couple, add a late entry to the heat report
                            h = heat_report.build_late_entry()
                            h.dancer = dancer_name_list[0]
                            h.partner = partner_name_list[0]
                            h.shirt_number = shirt_number
                            self.order_pro_am_couple(h)
                            if h.result is None:
                                h.result = self.temp_result(heat_report.rounds(), accum_value)
                            h.code = "LATE"
                            heat_report.append(h)
                    i += 1
            else:
                i+= 1

        # entire scoresheet was processed
        # for each entry in the heat report, extract the recall votes and calculate the points
        for e in entries_in_event:
            if e.points is None and e.result is not None:
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
                    placement = int(e.result)
                    accum_value = 0
                e.points = calc_points(heat.base_value, placement, num_competitors=total_entries, rounds=heat.rounds, accum=int(accum_value))
                #print(str(e.couple), "finish", e.result, "for", e.points, "points")
                e.save()


    def determine_heat_results(self, entries_in_event):
        '''This method obtains the results for all events in the given heat report.'''
        # process the scoresheet for each of those events.
        if entries_in_event.count() > 0:
            event_name = entries_in_event.first().heat.info
            for e in self.events:
                if e.name == event_name:
                    print("Processing " + e.name)
                    self.process_scoresheet_for_event(entries_in_event, e)
                    return True  # What to return here?
            else:
                print("Could not find event", event_name)
                xyz()
                return None
        else:
            print("No entries in event", event.name)
            xyz()
            return None


    def event_id(self, title):
        '''This method returns an event ID for the specified event title.'''
        for e in self.events:
            if e.name == title:
                return e.id
        else:
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

        #print("Catgories", self.categories)

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


    def close(self):
        '''This method performs any cleanup processing required.'''
        pass


if __name__ == '__main__':
    results = NdcaPremResults()
    results.open("http://www.ndcapremier.com/results.htm?cyi=398")
    h = Heat()
    h.info = "WDC World Professional Latin Int'l Latin Championship (CC,S,R,PD,J)"
    h.set_category("Pro heat")
    h.set_level()
    h.dancer = "Bager, Troels" #"Alitto, Oreste"
    h.partner = "Jeliazkova, Ina" # "Belozerova, Valeriia"
    h.rounds = "F"
    hr = Heat_Report()
    hr.append(h)
    results.determine_heat_results(hr)
    print("Results Processed")
#    results.determine_heat_results("Professional Rising Star Events Amer. Rhythm (CC,R,SW,B,M)")
#    results.determine_heat_results("Professional Rising Star Events Int'l Ballroom (W,T,VW,F,Q)")
#    results.determine_heat_results("Professional Rising Star Events Int'l Latin (CC,S,R,PD,J)")
     # this heat had a semi final
#    results.determine_heat_results("Professional Open Championships  Int'l Ballroom Championship (W,T,VW,F,Q)")
#    results.determine_heat_results("Professional Open Championships  Amer. Rhythm Championship (CC,R,SW,B,M)")
#    results.determine_heat_results("Professional Open Championships  Int'l Latin Championship (CC,S,R,PD,J)")
#    results.determine_heat_results("Professional Open Championships  Amer. Smooth Championship (W,T,F,VW)")
#    results.determine_heat_results("Professional Open Championships  Show Dance Championship (SD)")
