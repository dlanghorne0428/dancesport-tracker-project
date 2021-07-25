import json
import requests
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


    def process_response(self, entries, e):
        '''This routine processes the response returned by the form submittal.
           It is the scoresheet results for a single dancer.
           We use this to extract the results of the heat we are interested in .'''


        heat_string = str(e.heat.heat_number)
        heat_info_from_scoresheet = None

        # If there are parenthesis in the heat info, the heat has multiple dances
        # For example (W/T/F).
        # At this point, we only care about the final results of the heat, not the
        # individual dances.
        if e.heat.multi_dance():
            event = "Multi-Dance"
        else:
            event = "Single Dance"

        # save the level of the event (e.g. Open vs. Rising Star, Bronze, Silver, Gold, etc.)
        level = e.heat.base_value

        # set the rounds indicator to finals, until proven otherwise
        rounds = "F"

        json_data = json.loads(self.response.text)

        print(json_data['Status'])
        if json_data['Status'] == 0:
            # no results for this competitor
            print("No scoresheet")
            return

        for ev in json_data['Result']['Events']:
            if ev['Heat'] == heat_string:
                for r in ev['Rounds']:
                    if r['Name'] == "Final":
                        self.entries_in_event = 0
                        for c in r['Summary']['Competitors']:
                            for entry in entries:
                                if str(entry.shirt_number) == c['Bib']:
                                    if len(c['Result']) == 1:
                                        result_str = c['Result'][0]
                                        if len(entry.result) == 0:
                                            entry.result = result_str
                                            self.entries_in_event += 1
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
                                    else:
                                        print("Multiple Results")
                                        xxx()
                            else:
                                print("Late Entry")
                                xxx()

                        for e in entries:
                            if e.points is None and len(e.result) > 0:
                                e.points = calc_points(level, int(e.result), num_competitors=self.entries_in_event, rounds=rounds)
                            if e.points is not None:
                                #print(e, e.result, e.points)
                                e.save()

                    else:
                        print("Early Round")
                        xxx()




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
        return requests.get(url,timeout=5.0)
