import json

from rankings.models.couple import Couple
from rankings.models.dancer import Dancer
from comps.models.heat import Heat
from comps.models.heatlist_dancer import Heatlist_Dancer
from comps.models.heatlist_error import Heatlist_Error 
from comps.heatlist.heatlist import Heatlist


class FileBasedHeatlist(Heatlist):
    '''This class reads heat list information from a file.'''

    NUM_COLUMNS = 7
    CATEGORY_COLUMN = 0
    HEAT_NUM_COLUMN = 1
    TIME_COLUMN = 2
    INFO_COLUMN = 3
    SHIRT_NUM_COLUMN = 4
    NAMES_COLUMN = 5
    RESULT_RANK_COLUMN = 6

    ############### COMMON FILE FORMAT ROUTINES  #########################################
    # the following methods deal with saving heatlists in a common file format and
    # reloading them. This eliminates the need to return to the original website source.
    ######################################################################################

    def open(self, comp):
        '''Begin the process of reading heatsheet data from the common file format.'''
        self.filedata = comp.heatsheet_file
        self.filedata.open(mode="rt")
        line = self.filedata.readline().decode().strip()
        self.comp_name = line.split(":")[1]
        print(self.comp_name)
        # read past the line that says Dancers:
        line = self.filedata.readline().decode().strip()
        while True:
            line = self.filedata.readline().decode().strip()
            if line == "Heats":
                break
            else:
                d = Heatlist_Dancer()
                d.load_from_file(line)
                d.comp = comp
                print(str(d))
                self.dancers.append(d)

        # close the file
        self.filedata.close()


    def load(self, fieldfile, heatlist_dancers):
        '''Load the dancers object, reopen the file and skip past the dancers'''
        for d in heatlist_dancers:
            self.dancers.append(d)

        self.filedata = fieldfile
        self.filedata.open(mode="rt")
        line = self.filedata.readline().decode().strip()
        self.comp_name = line.split(":")[1]
        # read past the line that says Dancers:
        line = self.filedata.readline().decode().strip()
        while True:
            line = self.filedata.readline().decode().strip()
            if line == "Heats":
                break
                # leave the file open


    def load_heat(self, summary, comp_ref):
        self.heat.comp = comp_ref
        category = summary[self.CATEGORY_COLUMN]
        if category == "Pro heat":
            self.heat.category = Heat.PRO_HEAT
        elif category == "Solo":
            self.heat.category = Heat.SOLO
        else:
            self.heat.category = Heat.NORMAL_HEAT

        #extract heat number and extra info, if any
        try:
            self.heat.heat_number = int(summary[self.HEAT_NUM_COLUMN])
        except:
            end_index = 0
            while summary[self.HEAT_NUM_COLUMN][end_index].isdigit():
                end_index += 1
            self.heat.heat_number = int(summary[self.HEAT_NUM_COLUMN][:end_index])
            self.heat.extra = summary[self.HEAT_NUM_COLUMN][end_index:]

        # extract the heat time information
        time_fields = summary[self.TIME_COLUMN].split("T")
        print(time_fields)
        date_string = time_fields[0]
        time_string = time_fields[1].split("+")[0]
        self.heat.set_time(time_string, "", time_format="%H:%M:%S", date_string=date_string)

        # extract the heat description
        self.heat.info = summary[self.INFO_COLUMN]
        self.heat.remove_info_prefix()
        self.heat.set_level()
        self.heat.set_dance_style()


    def get_next_dancer(self, dancer_index, comp_ref):
        '''Read heat information for the next dance from the common file format.
           Must be called after the file has alrady been opened.'''
        line = self.filedata.readline().decode().strip()
        fields = line.split(":")
        d = self.dancers[dancer_index]
        print(d)
        try:
            num_heats = int(fields[-1])
        except:
            print("Error: Dancer: " + str(dancer_index) + " Heat count not found in " + line)
            self.build_heatlist_error(comp_ref, Heatlist_Error.NO_HEAT_COUNT, dancer_name=d.name)
            num_heats = -1
            return None
        for index in range(num_heats):
            line = self.filedata.readline().decode().strip()
            heat_info = line.split('\t')
            print(heat_info)
            couple_fields = heat_info[self.NAMES_COLUMN].split (" and ")
            shirt_number = heat_info[self.SHIRT_NUM_COLUMN]
            if len(couple_fields) == 2:
                partner_name = couple_fields[1]
                if partner_name == d.name:
                    partner_name = couple_fields[0]
                p = self.find_dancer(partner_name)
            else:
                print("No partner found in " + str(couple_fields))
                in_database = Heatlist_Error.objects.filter(comp=comp_ref).filter(dancer=d.name)
                if len(in_database) == 0:
                    self.build_heatlist_error(comp_ref, Heatlist_Error.NO_PARTNER_FOUND, dancer_name=d.name)
                p = None
            if p is not None:
                if p.name > d.name:
                    self.heat = Heat()
                    self.load_heat(heat_info, comp_ref)
                    h = self.add_heat_to_database(self.heat, comp_ref)
                    #print(self.heat.category, self.heat.heat_number, d.name, p.name, shirt_number)
                    if h is not None:
                        self.build_heat_entry(h, d, p, shirt_number)
                        
        # get past blank line                
        line = self.filedata.readline()  

        #print("Index:", dancer_index, "Name", d.name, "Heats", num_heats)
        return d.name


    def complete_processing(self):
        '''Complete the process of reading heatsheet data from the common file format.'''
        # close the file
        self.filedata.close()
        return self.unmatched_entries
