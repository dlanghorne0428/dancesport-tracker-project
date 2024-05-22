import string

from comps.scoresheet.calc_points import calc_points
from comps.models.heat_entry import Heat_Entry
from comps.models.unmatched_heat_entry import Unmatched_Heat_Entry
from comps.models.heatlist_dancer import Heatlist_Dancer
from comps.models.result_error import Result_Error


class Results_Processor():
    '''This is a base class for processing scoresheets.'''

    def __init__(self):
        ''' Initialize the class.'''
        # the URL will contain the address of the server.
        self.url = ""

        # this counts the number of couples entered in an event.
        self.entries_in_event = 0

        #this variable counts the number of late entries detected
        self.late_entries = list()

    def get_table_data(self, line):
        '''In the scoresheet results for a competitor, the data we want is stored
           in table cells. Find the <td> tags to extract the data.'''
        start_pos = line.find("<td>") + len("<td>")
        end_pos = line.find("<", start_pos)
        name = line[start_pos:end_pos]
        return name


    def get_shirt_number(self, competitor):
        '''The scoresheet results list the shirt number of the couple,
           followed by a space, then the couple names. This routine
           extracts and returns the shirt number.'''
        fields = competitor.split()
        if len(fields) != 2:
            index = 0
            while fields[0][index].isdigit():
                index += 1
                if index == len(fields[0]):
                    break
            return fields[0][:index]
        else:
            return fields[0]


    def get_heat_info(self, line, heat_string, trailer):
        '''The scoresheet results list the heat category and number,
           then a description of the heat. There is an optional trailer
           that indicates Final, Semi-final, etc.
           heat_string contains the category and the number
           trailer contains the expected trailer.
           Return everything between the heat_string and the trailer.'''
        extended_trailer = " - " + trailer
        start_pos = line.find(heat_string) + len(heat_string)
        end_pos = line.find(extended_trailer)
        if end_pos == -1:
            end_pos = line.find(trailer)
            if end_pos == -1:
                # could not find either version of the trailer
                remaining_text = line[start_pos:]
                return remaining_text.strip()

        # if we get here, we found one of the possible trailers
        remaining_text = line[start_pos:end_pos]
        return remaining_text.strip()


    def get_couple_names(self, competitor):
        '''The scoresheet results list the shirt number of the couple,
           followed by a space, then the couple names. This routine extracts
           and returns the couple names as an 2-elem array of strings.'''
        couple_names = []
        entrant_fields = competitor.split()
        # if there is a space in one of the names, there are more than 2 fields
        if len(entrant_fields) != 2:
            #print("Split on Space Error", entrant_fields)
            i = 0
            # in this case, get past the numeric characters of the shirt number
            # to find the start of the couple names
            while i < len(competitor):
                if competitor[i].isalpha():
                    break
                else:
                    i += 1
            # split on the slash between the couple names
            couple_names = competitor[i:].split("/")
        else:
            # this is the normal flow, split on the slash to get each name
            couple_names = entrant_fields[1].split("/")
            if len(couple_names) != 2:
                print("Split on Slash Error " + entrant_fields[1])
        return couple_names


    def build_heatlist_dancer(self, name):
        dancers = Heatlist_Dancer.objects.filter(name=name)
        if dancers.count() > 0:
            d = dancers.first()
        else:
            d = Heatlist_Dancer()
            d.name = name
            d.code = "LATE"
            d.save()
        return d


    def build_late_entry(self, heat, shirt_number, couple_names, result, points=None):
        if len(couple_names) != 2:
            return
        late_entry = Heat_Entry()
        late_entry.heat = heat
        late_entry.shirt_number = shirt_number
        late_entry.result = result
        if points is not None:
            late_entry.points = points
        late_entry.code = "LATE"
        saved = False
        while not saved:
            try:
                late_entry.save()
            except IntegrityError:
                print("Duplicate key for " + str(late_entry))
                num_tries += 1
                if num_tries == 20:
                    print("Unable to add " + str(late_entry))
                    continue # return -1
            else:
                saved = True             

        self.late_entries.append(late_entry)

        # need to create UnmatchedHeatEntry
        dancer = self.build_heatlist_dancer(couple_names[0])
        partner = self.build_heatlist_dancer(couple_names[1])
        same_entries = Unmatched_Heat_Entry.objects.filter(entry=late_entry, dancer=dancer, partner=partner)
        if same_entries.count() > 0:
            unmatched_entry = same_entries.first()
        else:
            unmatched_entry = Unmatched_Heat_Entry()
            unmatched_entry.populate(late_entry, dancer, partner)
            print("LATE ENTRY " + str(unmatched_entry))
            saved = False
            while not saved:
                try:
                    unmatched_entry.save()
                except IntegrityError:
                    print("Duplicate key for " + str(nmatched_entry))
                    num_tries += 1
                    if num_tries == 20:
                        print("Unable to add " + str(nmatched_entry))
                        continue # return -1
                else:
                    saved = True            
            


    def process_response(self, entries, e):
        '''This routine processes the response returned by the form submittal.
           It is the scoresheet results for a single dancer.
           We use this to extract the results of the heat we are interested in .'''
        # Build the string to find the results for the heat we want.
        # For example: Pro Heat 5:
        heat_string = e.heat.get_category_display() + " "
        # if the heat number is 0, leave it out
        if e.heat.heat_number != 0:
            heat_string += str(e.heat.heat_number)

        # if extra field was TBD or BOBR, there may be more than one, so include the heat info field
        if e.heat.extra in ["TBD", "BOBR"]:
            heat_string += e.heat.extra + ": " + e.heat.info
        elif len(e.heat.extra) > 0 and e.heat.extra.isalpha():
            # if the extra field are alphanumerics, include them
            heat_string += e.heat.extra + ":"
        else: # need the colon directly after the number, to distinguish 5 from 51, etc.
            heat_string += ":"
        
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

        # these are state variables to keep track of where we are in the parsing
        looking_for_recall_column = False
        looking_for_result_column = False
        looking_for_eliminations = False
        looking_for_finalists = False
        result = None

        # split the response into separate lines so we can loop through them
        lines = self.response.text.splitlines()
        for line in lines:
            # the result column is the last in the table, but there is one
            # column per judge, and we don't know how many judges there are
            if looking_for_result_column:
                # find the start of a table row
                if "<tr>" in line:
                    count = 0
                # If we have found the result column, save which column it is
                # and change the state to looking_for_finalists
                elif "<td>" in line and "Result" in line:
                    result_column = count
                    looking_for_finalists = True
                    looking_for_result_column = False
                    self.entries_in_event = 0
                    count = 0
                # skip past this column, it is not the last
                elif "<td>" in line:
                    count += 1

            # If we are processing the preliminary round results,
            # we look for the Recall column in the results of the last dance.
            # The logic is basically the same as looking for results, except
            # when we find that column, the next state is looking_for_eliminations
            elif looking_for_recall_column:
                if "<tr>" in line:
                    count = 0
                # this should only be true on sheets that don't identify the semi-final heat
                elif "<td>" in line and "Result" in line:
                    looking_for_recall_column = False
                    result = "Finals"
                elif "<td>" in line and "Recall" in line:
                    recall_column = count
                    accum_column = recall_column - 1
                    looking_for_eliminations = True
                    looking_for_recall_column = False
                    count = 0
                    max_recalls = 0
                    if rounds =="F":
                        temp_result = "Semis"
                        result_index = -2
                        rounds = "S"
                        print("Found Semis unexpectedly")
                        res_error = Result_Error()
                        res_error.comp = e.heat.comp
                        res_error.heat = e.heat
                        res_error.error = Result_Error.UNEXPECTED_EARLY_ROUND
                        res_error.save()
                elif "<td>" in line:
                    count += 1

            # If we are processing the preliminary round results,
            # we want to know which entries were not recalled to the next round.
            elif looking_for_eliminations:
                if "<td>" in line:
                    if count == 0:
                        # This is the first column, get the competitor information.
                        # This could be any of the entries in this heat, not necessarily
                        # the dancer we used to submit the form
                        current_competitor = self.get_table_data(line)
                        count += 1

                    elif count == accum_column:
                        # This column indicates how many recall votes a couple received.
                        # If the couple was not recalled, this number affects their points for the heat.
                        try:
                            accum = int(self.get_table_data(line))
                        except:
                            accum = 0
                        count += 1
                        
                    elif count == recall_column:
                        # If the data indicates the couple was recalled, we can ignore them,
                        # as we will get their results in the next round.
                        # If the couple was not recalled, we need to capture those results
                        if self.get_table_data(line) != "Recall":
                            
                            # check if this entrant had the most recalls of those eliminated
                            max_recalls = max(accum, max_recalls)                            

                            # extract the shirt number from the scoresheet
                            #couple_names = self.get_couple_names(current_competitor)
                            shirt_number = self.get_shirt_number(current_competitor)

                            # try to find this couple from the scoresheet in the original heat report
                            for e in entries:

                                if e.shirt_number == shirt_number:
                                    if len(e.result) == 0:
                                        # If the couple was not recalled, their result is the round
                                        # in which they were eliminated, save the accumulated number of recalls 
                                        # for later points calculations
                                        e.result = temp_result + '-' + str(accum)
                                        break

                                    elif e.result == temp_result:
                                        break
                                    else:
                                        print(str(e.heat.heat_number) +  " Same shirt # - new result: " + str(e.couple) + " " + e.result + " " + temp_result + " " + str(accum))
                                        res_error = Result_Error()
                                        res_error.comp = e.heat.comp
                                        res_error.heat = e.heat
                                        res_error.couple = e.couple
                                        res_error.error = Result_Error.TWO_RESULTS_FOR_COUPLE
                                        res_error.save()
                                        e.result = temp_result

                            # If we get here, we didn't find an entry on the heatsheet that matches
                            # this line on the scoresheet. This is the dreaded late entry.
                            else:
                                # Build a structure for the late entry couple with the results
                                couple_names = self.get_couple_names(current_competitor)
                                late_result = temp_result + '-' + str(accum)
                                self.build_late_entry(e.heat, shirt_number=shirt_number, result=late_result, couple_names=couple_names)

                        # reset the count to prepare for the next line of the scoresheet
                        count = 0

                    else:
                        # skip this column, it is not the recall column
                        count += 1

                elif "</table>" in line:
                    # once we get to the end of the table, there are no more entries to process
                    # calculate the points for those eliminated in this round, based on the max recalls
                    looking_for_eliminations = False
                    #print('max_recalls ' + str(max_recalls))
                    for e in entries:
                        if e.points is None and len(e.result) > 0:
                            dash_pos = e.result.find('-')
                            accum = int(e.result[dash_pos+1:])
                            e.result = e.result[:dash_pos]
                            e.points = calc_points(level, result_index, rounds=rounds, ratio=accum/max_recalls)
                            #print(str(e) + ' ' + e.result + ' ' + str(accum))
                        if e.points is not None:
                            e.save()
                    for late_entry in self.late_entries:
                        if late_entry.points is None:
                            dash_pos = late_entry.result.find('-')
                            accum = int(late_entry.result[dash_pos+1:]) 
                            late_entry.result = late_entry.result[:dash_pos]
                            late_entry.points = calc_points(level, result_index, rounds=rounds, ratio=accum/max_recalls)
                            #print(str(late_entry) + ' ' + late_entry.result + ' ' + str(accum))
                            late_entry.save()                    

            # When we are looking for finalists, the logic is similar to looking for eliminations
            elif looking_for_finalists:
                num_competitors = len(entries)
                if "<td>" in line:
                    if count == 0:
                        current_competitor = self.get_table_data(line)
                        self.entries_in_event += 1
                        count += 1
                    elif count == result_column:
                        # When we get to the result column, we want to extract the number that indicates
                        # the finishing position of this couple in this heat.
                        # Need to check for non-digit, as the result could include a tiebreaker rule
                        # For example: 3(R11) means they finished in 3rd place.
                        result_field = self.get_table_data(line)
                        index = 0
                        while index < len(result_field) and result_field[index] in string.digits:
                            index += 1
                        result_place = int(result_field[:index])

                        #couple_names = self.get_couple_names(current_competitor)
                        shirt_number = self.get_shirt_number(current_competitor)

                        # loop through all entries on the heatsheet to find a match
                        for e in entries:

                            if e.shirt_number == shirt_number:
                                if len(e.result) == 0:
                                    e.result = str(result_place)
                                    break
                                elif e.result == str(result_place):
                                    break
                                else:
                                    print(str(e.heat.heat_number) + " Same number - new result: " + " " + str(e.couple.dancer_1) + " " + str(e.couple.dancer_2) + " " + e.result + " " + str(result_place))
                                    e.result = str(result_place)
                                    res_error = Result_Error()
                                    res_error.comp = e.heat.comp
                                    res_error.heat = e.heat
                                    res_error.couple = e.couple
                                    res_error.error = Result_Error.TWO_RESULTS_FOR_COUPLE
                                    res_error.save()
                                    break

                        else:    # this code runs when competitor not found in heat
                            couple_names = self.get_couple_names(current_competitor)
                            if len(couple_names) > 1:
                                self.build_late_entry(e.heat, shirt_number=shirt_number, result=str(result_place), couple_names=couple_names)
                            else:
                                print("Error in couple " + " " + str(couple_names))

                        # reset for next line of the scoresheet
                        count = 0

                    else:  # skip past this column
                        count += 1

                # When we see the closing table tag, we are done with this heat.
                elif "</table>" in line:
                    looking_for_finalists = False
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
                            #print("LATE ENTRY SCORING: " + late_entry.result + " " + str(late_entry.points))
                    break;

            # We get here if we aren't in any of the "looking" states
            # Note: These scoresheets list the preliminary rounds first, ending with the final round

            # If this check is true, we found first round results for this heat
            elif heat_string in line and "First Round" in line and ("<p>" in line or "<h3>" in line):
                temp_result = "round 1"    # indicate which round we are in
                result_index = -10         # use this to pull values from the points table
                rounds = "R1"
                heat_info_from_scoresheet = self.get_heat_info(line, heat_string, "First Round")
                looking_for_recall_column = True  # enter the next state

            # If this check is true, we found second round results for this heat
            elif heat_string in line and "Second Round" in line and ("<p>" in line or "<h3>" in line):
                temp_result = "round 2"    # indicate which round we are in
                result_index = -5         # use this to pull values from the points table
                rounds = "R21"
                heat_info_from_scoresheet = self.get_heat_info(line, heat_string, "Second Round")
                looking_for_recall_column = True  # enter the next state

            # If this check is true, we found third round results for this heat
            elif heat_string in line and "Third Round" in line and ("<p>" in line or "<h3>" in line):
                temp_result = "round 3"    # indicate which round we are in
                result_index = -53        # use this to pull values from the points table
                rounds = "R321"
                heat_info_from_scoresheet = self.get_heat_info(line, heat_string, "Third Round")
                looking_for_recall_column = True  # enter the next state

            # If this check is true, we found quarter-final results for this heat
            elif heat_string in line and "QUARTER" in line.upper() and "FINAL" in line.upper() and ("<p>" in line or "<h3>" in line):
                temp_result = "quarters"    # indicate which round we are in
                result_index = -1      # use this to pull values from the points table
                #print("Found Quarterfinals")
                # if we haven't seen a prelim round, set rounds indicator to quarters
                if rounds == "F":
                    rounds = "Q"
                heat_info_from_scoresheet = self.get_heat_info(line, heat_string, "Quarter-final")
                looking_for_recall_column = True  # enter the next state

            # If this check is true, we found Semi-final results for this heat
            elif heat_string in line and "SEMI-FINAL" in line.upper() and ("<p>" in line or "<h3>" in line):
                temp_result = "Semis"
                result_index = -2
                #print("Found Semifinals")
                if rounds == "F":
                    rounds = "S"
                heat_info_from_scoresheet = self.get_heat_info(line, heat_string, "Semi-final")
                looking_for_recall_column = True

            # If this check is true, we found the Final results for this heat
            elif heat_string in line and ("<p>" in line or "<h3>" in line):   # and "Final" in line:
                #print("Found " + heat_string)
                heat_info_from_scoresheet = self.get_heat_info(line, heat_string, "Final")
                # if this is a single dance event, we can look for the results now
                if event == "Single Dance":
                    result = "Finals"
                    #print("Found Finals - single dance")
                    looking_for_result_column = True
                else:
                    looking_for_recall_column = True  # this may not be the final on some websites

            # If this is the Final of a Multi-Dance event, we process the Final Summary
            elif result == "Finals" and "Final summary" in line and ("<p>" in line or "<h3>" in line):
                if event == "Multi-Dance":
                    #print("Found Finals")
                    looking_for_result_column = True

            elif "Place" in line and "<th>" in line:
                print("Found a table header with Place " + line)

        # Return which level of results we were able to find on this dancer's scoresheet
        # If they were eliminated before the finals, the final results will not appear,
        # and the calling routine will have to try another dancer to get those.
        return result


    def determine_heat_results(self, entries):
        '''This routine extracts the results for a given heat.
           A lise of heat entries is passed in.'''
        # loop through the entries in the heat
        loop_count = 0
        # initalize the result to "No Change".
        # if a scoresheet is processed, its result (possibly none) will be returned
        heat_result = "No Change"
        for e in entries:
            # if we don't already know the result for this entry
            if len(e.result) == 0:
                # get the scoresheet for this entry and process it
                loop_count += 1
                # if loop_count > 1:
                #     print("Reading Scoresheet for " + e.heat.get_category_display() + " " + str(e.heat.heat_number) + " " + str(e.couple))
                self.response = self.get_scoresheet(e)
                result = self.process_response(entries, e)
                if result is not None:
                    heat_result = result
        if heat_result is not None:
            for e in entries:
                if e.points is None:
                    e.result = "DNP"

        return heat_result
