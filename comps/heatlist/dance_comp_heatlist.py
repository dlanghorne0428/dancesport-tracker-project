import requests
import json

from rankings.models.couple import Couple
from rankings.models.dancer import Dancer
from comps.models.heat import Heat
from comps.models.heatlist_dancer import Heatlist_Dancer
from comps.models.heatlist_error import Heatlist_Error
from comps.heatlist.heatlist import Heatlist

class DanceCompHeatlist(Heatlist):
    
    def __init__(self):
        super().__init__()
        self.heat_entry_table = list()
        
        
    def load_heat(self, heat, json_record="", comp_ref=""):
        
        heat.comp = comp_ref
        heat.rounds = "F"   # assume final only
        
        # get the category, heat number, and extra
        heat.extra = ''
        hn_str = json_record['heat_number']
        if hn_str.startswith('Heat'):
            heat.category = Heat.NORMAL_HEAT
            number_string = hn_str[len('Heat '):]
            
        elif hn_str.startswith('Pro heat'):
            heat.category = Heat.PRO_HEAT
            number_string = hn_str[len('Pro heat '):]  
            
        elif hn_str.startswith('Solo'):
            heat.category = Heat.SOLO
            number_string = hn_str[len('Solo '):]  
           
        elif hn_str.startswith('Formation'):
            heat.category = HEAT.FORMATION
            number_string = hn_str[len('Formation '):]  
            
        else:
            heat.category = 'Unknown'
            number_string = hn_str
            print('ERROR: ' + hn_str)
            
        try:
            heat.heat_number = int(number_string)
        except:
            # extract non-digit info into the extra property
            index = 0
            while number_string[index].isdigit():
                index += 1
            if index == 0:
                heat.heat_number = 0
                heat.extra = "TBD"
            else:
                heat.heat_number = int(number_string[:index])
                heat.extra = number_string[index:]
                
        if 'division' in json_record:
            if json_record['division'] in json_record['name'] and heat.multi_dance():  
                heat.info = json_record['age'] + ' ' + json_record['name']
            else:
                heat.info = json_record['age'] + ' ' + json_record['division'] + ' ' + json_record['name'] 
        else:
            heat.info = json_record['age'] + ' ' + json_record['name']
        
        time_str = json_record['time']
        session = json_record['session']
        # should read the schedule from the website and convert into day of week
        if session == 1:
            day_of_week = "Thursday"
        elif session == 2 or session == 3:
            day_of_week = "Friday"
        elif session == 4 or session == 5:
            day_of_week = "Saturday"
        elif session == 6:
            day_of_week = 'Sunday'
        else:
            day_of_week = "Unknown"
        
        heat.set_time(time_str, day_of_week)
        heat.set_level()
        heat.set_dance_style()
        #print(heat)
            
    ############### EXTRACTION ROUTINES  #################################################
    # the following helper methods extract specific data items from the DanceComp site
    ######################################################################################    
    
    def lookup_dancer(self, dancer_code):
        for d in self.dancers:
            if d.code == dancer_code:
                return d
        else:
            return None
    
    
    def get_heats_for_dancer(self, dancer, comp_ref):
        '''This method extracts heat information from the heat_data read in from a URL.
        The information is saved into the specified dancer object.'''
        
        # loop through all the heat entries to heats for this dancer
        for entry in self.heat_entry_table:

            # only look for dancer1 position
            if 'dancer1_num' in entry:
                if entry['dancer1_num'] == dancer.code:
                    if 'dancer2_num' in entry: 
                        partner = self.lookup_dancer(entry['dancer2_num'])
                        if partner is None:
                            partner = self.dancers[-1]  #{No, Partner}
                        #print(str(dancer) + ' ' +  str(partner))
                        shirt_number = entry['number_on_the_back']
                        heat = Heat()
                        self.load_heat(heat, entry, comp_ref)
                        h = self.add_heat_to_database(heat, comp_ref)
                        if h is not None:
                            self.build_heat_entry(h, dancer, partner, shirt_number=shirt_number)
                            #print(entry)

        
    ############### OVERRIDDEN METHODS  #######################################################
    # the following methods override the parent class to obtain data from the  NdcaPremier site
    ###########################################################################################
    def open(self, comp):
        '''This method obtains the name of the competition and a list of all the dancers.'''
        #extract comp name and comp_id from URL
        url = comp.heatsheet_url    
                
        # open this URL to obtain a list of dancers in JSON format
        response = requests.get(url)
        lines = response.text.split(';')

        for line in lines:
            if "let heatTable" in line:
                start_pos = line.find('data: ')
                end_pos = line.find('}],')
            
                heat_data = line[start_pos+len('data: '):end_pos+2]
                break
    
        self.heat_entry_table = json.loads(heat_data)

        # loop through all the heat entries to find the dancers
        for h in self.heat_entry_table:

            if 'Dancer1_name' in h:
                d = Heatlist_Dancer()
                d.load_from_dance_comp(h, dancer1=True)
                d.comp = comp
                d.alias = None
                self.dancers.append(d)
            else:
                print('NO DANCERS ' + str(h))
            
            if 'Dancer2_name' in h:
                d = Heatlist_Dancer()
                d.load_from_dance_comp(h, dancer1=False)    
                d.comp = comp
                d.alias = None  
                self.dancers.append(d)
                

    def load(self, url, heatlist_dancers):
        # load the list of dancers found by open()
        for d in heatlist_dancers:
            self.dancers.append(d)
              
        # open this URL to obtain a list of heat entries in JSON format
        response = requests.get(url)
        lines = response.text.split(';')

        for line in lines:
            if "let heatTable" in line:
                start_pos = line.find('data: ')
                end_pos = line.find('}],')
            
                heat_data = line[start_pos+len('data: '):end_pos+2]
                break
    
        self.heat_entry_table = json.loads(heat_data)
        print('data loaded')
    
        
        
    def get_next_dancer(self, index, comp_ref):
        '''This method reads the heat information for the dancer at the given index.'''
        d = self.dancers[index]
        if d.code != "0":
            self.get_heats_for_dancer(d, comp_ref)
        return d.name    
            
            #print(category + ' ' + str(heat_number) + extra + ' ' + info +  ' ' + day_of_week + ' ' + time_str)
            #print()


    def complete_processing(self):
        return self.unmatched_entries