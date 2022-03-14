import json
import requests
from comps.models.result_error import Result_Error
from comps.scoresheet.calc_points import calc_points
from comps.scoresheet.results_processor import Results_Processor


class NdcaPremFeedResults(Results_Processor):
    '''This class is derived from a Results_Processor base class.
       It parses a results file from the NdcaPremier website in the "feed" format
       and extracts the results of the competition.'''

    def __init__(self):
        ''' Initialize the class.'''
        super().__init__()
        self.comp_name = None


    def get_couple_names(self, participants):
        couple_names = []
        if len(participants) == 2:
            for n in participants:
                if len(n['Name']) == 2:
                    couple_names.append(n['Name'][1] + ", " + n['Name'][0])
        return couple_names


    def process_response(self, entries, e):
        '''This routine processes the response returned by the form submittal.
           It is the scoresheet results for a single dancer.
           We use this to extract the results of the heat we are interested in .'''

        # determine heat to search for in the scoresheet
        if e.heat.heat_number == 0:
            heat_string = e.heat.extra
        elif len(e.heat.extra) > 0 and e.heat.extra[0] != '[':
            heat_string = str(e.heat.heat_number) + e.heat.extra
        else:
            heat_string = str(e.heat.heat_number)

        # save the level of the event (e.g. Open vs. Rising Star, Bronze, Silver, Gold, etc.)
        level = e.heat.base_value

        # set the rounds indicator to finals, until proven otherwise
        rounds = "F"

        # find the beginning of the JSON data
        if self.response.text[0] == "{":
            start_pos = 0
        else:
            start_pos = self.response.text.find("{")

        try:
            json_data = json.loads(self.response.text[start_pos:])
        except:
            print("Unable to parse scoresheet - " + str(e.heat))
            return

        if json_data['Status'] == 0:
            # no results for this competitor
            print("No scoresheet")
            return

        # search all the events on this dancer's scoresheet
        for ev in json_data['Result']['Events']:
            # once we find the heat we want
            if ev['Heat'] == heat_string:
                for r in ev['Rounds']:
                    if r['Name'] == "Final":
                        # process final round results
                        self.entries_in_event = 0
                        # don't process Solo - keep looking for heat_string
                        if r['Scoring_Method'] == "Solos":
                            continue
                        # loop through all the competitors in this heat
                        for c in r['Summary']['Competitors']:
                            self.entries_in_event += 1
                            for entry in entries:
                                # find matching entry by shirt number
                                if str(entry.shirt_number) == c['Bib']:
                                    # This Result list is length 1, unless there are tiebreakers, so use the last item
                                    result_str = c['Result'][-1]
                                    if len(entry.result) == 0:
                                        entry.result = result_str
                                        break
                                    elif entry.result == result_str:
                                        break
                                    else:
                                        print(str(entry.heat.heat_number) + " Same number - new result: " + " " + str(entry.couple.dancer_1) + " " + str(entry.couple.dancer_2) + " " + entry.result + " " + result_str)
                                        entry.result = result_str
                                        res_error = Result_Error()
                                        res_error.comp = entry.heat.comp
                                        res_error.heat = entry.heat
                                        res_error.couple = entry.couple
                                        res_error.error = Result_Error.TWO_RESULTS_FOR_COUPLE
                                        res_error.save()
                                        break

                            else: # late entry in final
                                couple_names = self.get_couple_names(c['Participants'])
                                if len(couple_names) == 2:
                                    self.build_late_entry(entry.heat, shirt_number=c['Bib'], result=c['Result'][-1], couple_names=couple_names)
                                else:
                                    print("error in late entry couple names")
                                    xxx()

                        # now we know the number of entries, calculate points
                        for e in entries:
                            if e.points is None and len(e.result) > 0:
                                e.points = calc_points(level, int(e.result), num_competitors=self.entries_in_event, rounds=rounds)
                            if e.points is not None:
                                #print(e, e.result, e.points)
                                e.save()

                        for late_entry in self.late_entries:
                            if late_entry.points is None:
                                late_entry.points = calc_points(level, int(late_entry.result), num_competitors=self.entries_in_event, rounds=rounds)
                                late_entry.save()

                    else: # process early rounds, looking for those who were eliminated
                        if r['Name'] == "Semi-Final":
                            if rounds == "F":
                                rounds = "S"
                            result_index = -2
                            temp_result = "Semis"
                        elif r['Name'] == "Quarter-Final":
                            if rounds == "F":
                                rounds = "Q"
                            result_index = -1
                            temp_result = "quarters"
                        elif r['Name'] == "Round 1":
                            if rounds == "F":
                                rounds = "R1"
                            result_index = -10
                            temp_result = "round 1"
                        elif r['Name'] == "Round 2":
                            if rounds == "F" or rounds == "R1":
                                rounds = "R21"
                            result_index = -5
                            temp_result = "round 2"
                        elif r['Name'] == "Round 3":
                            if rounds == "F" or rounds == "R1" or rounds == "R21":
                                rounds = "R321"
                            result_index = -3
                            temp_result = "round 3"
                        else:
                            print("Unknown Round")
                            print(r)
                            xxx()
                        for c in r['Summary']['Competitors']:
                            if c['Recalled'] == 0:
                                for entry in entries:
                                    if str(entry.shirt_number) == c['Bib']:
                                        if len(entry.result) == 0 or entry.result == temp_result:
                                            # If the couple was not recalled, their result is the round
                                            # in which they were eliminated
                                            entry.result = temp_result

                                            # Lookup their points, and exit the loop
                                            entry.points = calc_points(level, result_index, rounds=rounds, accum=c['Total'])
                                            break
                                        else:
                                            res_error = Result_Error()
                                            res_error.comp = e.heat.comp
                                            res_error.heat = e.heat
                                            res_error.couple = e.couple
                                            res_error.error = Result_Error.TWO_RESULTS_FOR_COUPLE
                                            res_error.save()
                                            entry.result = temp_result
                                            break

                                else:  # late entry
                                    try:
                                        couple_names = self.get_couple_names(c['Participants'])
                                        if len(couple_names) == 2:
                                            points = calc_points(level, result_index, rounds=rounds, accum=c['Total'])
                                            self.build_late_entry(entry.heat, shirt_number=c['Bib'], result=temp_result, couple_names=couple_names, points=points)
                                        else:
                                            print("error in late entry names")
                                            xxx()
                                    except:
                                        print("error in late entry names")


    ############### PRIMARY ROUTINES  ####################################################
    # the following methods are called from the main GUI program.
    ######################################################################################
    def open(self, url):
        '''This routine opens a scoresheet from the given URL.
           It saves information such that we can request results for any
           dancer in the competition'''
        #extract comp name from URL
        start_pos = url.find("cyi=") + len("cyi=")
        self.comp_name = url[start_pos:]
        #print(self.comp_name)

        # build a base_url that can be used to grab results for individual dancers
        self.base_url = "https://ndcapremier.com/feed/results/?cyi=" + self.comp_name
        #print(self.base_url)


    def get_scoresheet(self, entry):
        '''This routine requests the scoresheet for a given entry in this heat
           and returns it to the calling routine for processing.'''
        # build the request field based on the numeric code found in the entry
        url = self.base_url + "&id=A" + entry.code
        #print("Requesting", url)

        # Make the HTML request and the data is returned as text.
        return requests.get(url,timeout=10.0)
