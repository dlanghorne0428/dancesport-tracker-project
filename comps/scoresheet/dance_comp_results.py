import json
import requests
from comps.models.result_error import Result_Error
from comps.scoresheet.calc_points import calc_points
from comps.scoresheet.results_processor import Results_Processor


class DanceCompResults(Results_Processor):
    '''This class is derived from a Results_Processor base class.
       It parses a results file from the NdcaPremier website in the "feed" format
       and extracts the results of the competition.'''

    def __init__(self):
        ''' Initialize the class.'''
        super().__init__()
        self.comp_name = None
        self.results_table = list()


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


        if len(self.response) > 0:
            #print(self.response)
            self.entries_in_event = 0
            level = e.heat.base_value
            rounds = 'F'
            
            for r in self.response:
                for entry in entries:
                    if entry.shirt_number == r['number_on_the_back']:
                        #print(str(entry.couple) + ' Place: ' + str(r['place'])) 
                        entry.result = str(r['place'])
                        self.entries_in_event += 1
                        
            # now we know the number of entries, calculate points
            for entry in entries:
                if entry.points is None and len(entry.result) > 0:
                    entry.points = calc_points(level, int(entry.result), num_competitors=self.entries_in_event, rounds=rounds)
                if entry.points is not None:
                    #print(entry, entry.result, entry.points)
                    entry.save()   
            
            return 1
                    
        else:
            return 
     


    ############### PRIMARY ROUTINES  ####################################################
    # the following methods are called from the main GUI program.
    ######################################################################################
    def open(self, url):
        '''This routine opens a scoresheet from the given URL.
           It saves information such that we can request results for any
           dancer in the competition'''
        # open this URL to obtain a list of heat results
        response = requests.get(url)
        lines = response.text.split(';')

        for line in lines:
            if "let resultTable" in line:
                start_pos = line.find('data: ')
                end_pos = line.find('}],')
            
                result_data = line[start_pos+len('data: '):end_pos+2]
                break
    
        self.result_table = json.loads(result_data)
        #print(self.result_table)


    def get_scoresheet(self, entry):
        '''This routine requests the scoresheet for a given entry in this heat
           and returns it to the calling routine for processing.'''
        heat_str = entry.heat.get_category_display() + ' ' + str(entry.heat.heat_number) 
        if len(entry.heat.extra) > 0:
            heat_str += entry.heat.extra
        heat_str += ':'

        matching_records = list()
        #print(heat_str)
        for r in self.result_table:
            if 'heat' in r:
                if r['heat'].startswith(heat_str): #and entry.heat.info in r['heat']:
                    #print(r)
                    matching_records.append(r)

        return matching_records
