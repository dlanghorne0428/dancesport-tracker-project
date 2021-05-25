import requests
from comps.scoresheet.results_processor import Results_Processor
from comps.scoresheet.calc_points import calc_points
from comps.models.heatlist_dancer import Heatlist_Dancer
from comps.models.result_error import Result_Error



class O2cmResults(Results_Processor):
    '''This class processes the results from the NDCA Premier site...'''
    def __init__(self):
        super().__init__()

        # the base URL to use when requesting scoresheets
        self.base_url = None

        # the event ID to use when requesting scoresheets
        self.event_ID = None

        # payload used to request heats for a given dancer's code
        self.payload = dict()
        self.payload["selDiv"] = ""
        self.payload["selAge"] = ""
        self.payload["selSki"] = ""
        self.payload["selSty"] = ""
        self.payload["submit"] = "OK"

        # get access to format_name
        # self.hld = Heatlist_Dancer()


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


    def find_name_from_couple_table(self, field):
        start_pos_l = field.find("szLast=") + len("szlast=")
        end_pos_l = field.find("&", start_pos_l)
        start_pos_f = field.find("szFirst=", end_pos_l) + len("szFirst=")
        end_pos_f = field.find(" target", start_pos_f)
        return field[start_pos_l:end_pos_l] + ", " + field[start_pos_f:end_pos_f]


    def process_couple(self, entries, dancer_name, partner_name, shirt_number, result_str):
        # look for this couple in the entries and add the result and shirt number
        for entry in entries:
            if str(entry.couple.dancer_1) == dancer_name or str(entry.couple.dancer_2) == dancer_name or \
               str(entry.couple.dancer_1) == partner_name or str(entry.couple.dancer_2) == partner_name:
                entry.shirt_number = shirt_number
                if len(entry.result) == 0:
                    entry.result = result_str
                # TODO: generate error if result already exists.
                # print(entry)
                break
        else:
            # couple not found, create a late entry
            print("Could not find " + partner_name + " and " + dancer_name)
            couple_names = [dancer_name, partner_name]
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


    def process_scoresheet_for_event(self, entries, url):
        '''This is the method that requests and processes the scoresheet for a
           particular heat'''

        # on the o2cm site, we only handle final rounds at this time
        looking_for_final_round = True
        looking_for_score_column = False
        looking_for_final_summary = False
        looking_for_final_dance = False
        looking_for_result_column = False
        looking_for_recall_column = False
        looking_for_finalists = False
        looking_for_quarterfinal = False
        looking_for_prelim_round = False
        looking_for_eliminations = False
        process_finalists = False
        looking_for_semifinal = False
        # on the o2cm site, the couple names are listed separately from the heat results
        looking_for_couple_names = False

        self.entries_in_event = 0
        # for e in entries:
        #     print(e)
        self.heat = entries.first().heat

        # request the scoresheet and split the response into lines
        response = requests.get(url)
        lines = response.text.splitlines()
        i = 0

        # loop through all the lines
        while i < len(lines):
            l = lines[i]
            if looking_for_final_round:
                if 'class="h4"' in l:
                    # once the find the title with the final results, look for the score column or summary.
                    looking_for_score_column = True
                    num_scores = 0
                    total_score = 0
                    looking_for_final_round = False
                    #print("Found Final results")
                else:
                    i += 1
            elif looking_for_score_column:
                if 'class=h3' in l:
                    if "Score" in l:
                        next_row = False
                        rows = l.split("</tr>")
                        for r in rows:
                            if next_row:
                                fields = r.split("</td>")
                                score_column = len(fields) - 4
                                score = float(fields[score_column][len("<td>"):])
                                num_scores += 1
                                total_score += score
                                break
                            if "Score" in r:
                                next_row = True

                        i += 1
                    else:
                        looking_for_score_column = False
                        looking_for_final_summary = True
                elif "Couples" in l:
                    e = entries[0]
                    e.result = 1
                    avg_score = total_score / num_scores
                    e.points = round(calc_points(self.heat.base_value, placement=1, num_competitors=1, score=avg_score), 2)
                    #print(str(e), total_score, avg_score, e.points)
                    e.save()
                    return 1
                    i += 1
                else:
                    i += 1
            elif looking_for_final_summary:
                if 'class=h3' in l and "Summary" in l:
                    # once the summary header is found, look for the result columen
                    looking_for_final_summary = False
                    looking_for_result_column = True
                    #print("Found Summary")
                    col_count = 0
                else:
                    i += 1
            elif looking_for_result_column:
                #print(l)
                rows = l.split("</tr>")
                fields = rows[0].split("</td>")
                # count the number of columns until the result column is found
                if "Res" in l:
                    # once the result column is found, process each finalist
                    col_count = len(fields) - 2
                    #print("Found Results in Column", col_count)
                    looking_for_result_column = False
                    looking_for_finalists = True
                    results = list()
                else:
                    i += 1
            # elif looking_for_recall_column:
            #     # when looking for recalls, determine the number of columns
            #     fields = l.split("</th>")
            #     recall_column = len(fields) - 2
            #     accum_column = recall_column - 1
            #     i += 1
            #     looking_for_recall_column = False
            #     # start looking for couples that were eliminated in the current round
            #     looking_for_eliminations = True

            elif looking_for_finalists:
                rows = l.split("</tr>")
                # once the closing table tag is found we have one row per couple
                if "</table>" in rows[-1]:
                    rows = rows[:-1]
                    looking_for_finalists = False
                    #print("Found last finalist")
                    looking_for_couple_names = True
                    i += 1
                    # after processing the final results, look for possible semifinal
                    #looking_for_semifinal = True
                else:
                    i += 1
                # loop through all the couples
                for r in rows:
                    # split the row into columns
                    fields = r.split("</td>")
                    #print(fields)
                    if len(fields) == col_count + 1:
                        # get the couple name and number from the first column
                        couple_field = fields[0].split("t1b>")[1]
                        # get the result info from the last column
                        result_field = fields[col_count-1].split("<td>")[1]
                        # try:
                        #     result_place = int(result_field)
                        # except:
                        #     result_place = None
                        #print("Couple:", couple_field, "Result:", result_field)
                        entry={}
                        entry["couple"] = couple_field
                        entry["result"] = result_field
                        #print(entry)
                        results.append(entry)
                        self.entries_in_event += 1


            elif looking_for_couple_names:
                if 'class=t1b>Couples' in l:
                    #print("Found start of couple list")
                    #print(l)
                    rows = l.split("<tr>")
                    for r in rows:
                        if 'class=t1b>Judges' in r:
                            looking_for_couple_names = False
                            break
                        elif 'individual.asp' in r:
                            # this row has a couple number and names
                            cols = r.split("</td>")
                            # find the shirt number of this couple to match with results
                            start_pos = cols[0].find("t1b>") + len("t1b>")
                            number = cols[0][start_pos:]
                            # extract the couple names
                            couple_names = cols[1].split(",")
                            dancer_name = self.find_name_from_couple_table(couple_names[0])
                            partner_name = self.find_name_from_couple_table(couple_names[1])
                            # match the shirt number with the results found earlier
                            for e in results:
                                if e["couple"] == number:
                                    e["dancer"] = dancer_name
                                    e["partner"] = partner_name
                                    #print(e)
                                    self.process_couple(entries, dancer_name, partner_name, e["couple"], e["result"])
                                    break
                i += 1

            # elif looking_for_semifinal:
            #     # if we find a semifinal, set the rounds and look for the results of this round
            #     if 'class="roundHeader"' in l:
            #         #print("Found semi-final")
            #         self.heat.rounds = "S"
            #         looking_for_semifinal = False
            #         looking_for_final_dance = True
            #         dance_count = 0
            #     else:
            #         i += 1
            # elif looking_for_quarterfinal:
            #     # if we find a quarter final, set the rounds and look for the results of this round
            #     if 'class="roundHeader"' in l:
            #         #print("Found quarter-final")
            #         self.heat.rounds = "Q"
            #         looking_for_quarterfinal = False
            #         looking_for_final_dance = True
            #         dance_count = 0
            #     else:
            #         i += 1
            # elif looking_for_prelim_round:
            #     # if we find an earlier round, set the rounds and look for the results of this round
            #     if 'class="roundHeader">Third' in l:
            #         #print("Found Third Round")
            #         self.heat.rounds = "R3"
            #         looking_for_prelim_round = False
            #         looking_for_final_dance = True
            #         dance_count = 0
            #     elif 'class="roundHeader">Second' in l:
            #         #print("Found Second Round")
            #         if self.heat.rounds != "R3":
            #             self.heat.rounds = "R32"
            #         else:
            #             self.heat.rounds = "R2"
            #         looking_for_prelim_round = False
            #         looking_for_final_dance = True
            #         dance_count = 0
            #     elif 'class="roundHeader">First' in l:
            #         #print("Found First Round")
            #         if self.heat.rounds == "R32":
            #             self.heat.rounds = "R321"
            #         elif self.heat.rounds == "R2":
            #             self.heat.rounds = "R21"
            #         else:
            #             self.heat.rounds = "R1"
            #         looking_for_prelim_round = False
            #         looking_for_final_dance = True
            #         dance_count = 0
            #     else:
            #         i += 1
            # elif looking_for_final_dance:
            #     if 'class="eventResults"' in l:
            #         dance_count += 1
            #     # TODO: some prelim rounds may not dance all the dances. Need to handle this.
            #     if dance_count == num_dances:
            #         looking_for_final_dance = False
            #         looking_for_recall_column = True
            #     i += 1
            # elif looking_for_eliminations:
            #     # once we find the results of an early round, look for earlier rounds
            #     if "</table>" in l:
            #         looking_for_eliminations = False
            #         if self.heat.rounds == "S":
            #             looking_for_quarterfinal = True
            #         elif self.heat.rounds == "Q":
            #             looking_for_prelim_round = True
            #         elif self.heat.rounds == "R3":
            #             looking_for_prelim_round = True
            #         elif self.heat.rounds == "R2":
            #             looking_for_prelim_round = True
            #     else:
            #         # process the result of the next couple
            #         fields = l.split("</td>")
            #         # get the couple name and shirt number
            #         couple_field = fields[0].split("<td>")[1]
            #         # determine if the couple was recalled
            #         recall_place = fields[recall_column].split("<td>")[1]
            #         if recall_place != "Recall":
            #             # if the couple was not recalled determine how many votes they got
            #             accum_value = fields[accum_column].split("<td>")[1]
            #             result_str = self.temp_result(self.heat.rounds, accum_value)
            #
            #             # process this couple
            #             self.process_couple(entries, couple_field, result_str)
            #
            #         i += 1
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


    def find_heat_url(self, lines, heat_info):
        '''This method builds a URL to request a scoresheet.'''
        for l in lines:
            if "class=h5b" in l:
                if heat_info in l:
                    #print("found heat " + heat_info)
                    start_pos = l.find("href=") + len("href=")
                    end_pos = l.find("&bclr")
                    return "http://results.o2cm.com/" + l[start_pos:end_pos]
        else:
            print("could not find heat " + heat_info)
            return None


    def determine_heat_results(self, entries):
        '''This method obtains the results for all entries in the event.'''
        res_error = "No Change"
        # process the scoresheet for each of those events.
        for entry in entries:
            if entry.points is None:
                self.payload["selent"] = entry.code
                #print(self.payload)

                # obtain a list of heats danced by this dancer
                response = requests.post(self.base_url, data = self.payload)
                lines = response.text.split("</td>")
                heat_info = entry.heat.info
                end_pos = heat_info.find(' [')
                heat_url = self.find_heat_url(lines, heat_info[:end_pos])
                if heat_url is not None:
                    return self.process_scoresheet_for_event(entries, heat_url)
                else:
                    if res_error is None:
                        res_error = Result_Error()
                        res_error.comp = heat.comp
                        res_error.heat = heat
                        res_error.error = Result_Error.HEAT_NOT_FOUND
                        res_error.save()

        else: # all entries have results already
            return "No Change"


    def open(self, url):
        '''This method opens the results page for a competition on the 02cm.com site'''
        #extract base URL and event ID from URL
        start_pos = url.find("?event=")
        start_pos2 = start_pos + len("?event=")
        self.base_url = url[:start_pos]
        self.event_id = url[start_pos2:]
        self.payload["event"] = self.event_id

        #print("URL: " + url)
        #print("Base URL: " + self.base_url)
        #print("Event ID: " + self.event_id)
