from celery import shared_task
from celery_progress.backend import ProgressRecorder
from datetime import datetime, date, timezone, timedelta
from django.core import serializers
from django.shortcuts import get_object_or_404
from .heatlist.file_based_heatlist import FileBasedHeatlist
from .heatlist.comp_mngr_heatlist import CompMngrHeatlist
from .heatlist.comp_organizer_heatlist import CompOrgHeatlist
from .heatlist.ndca_prem_heatlist import NdcaPremHeatlist
from .heatlist.ndca_prem_feed_heatlist import NdcaPremFeedHeatlist
from .heatlist.o2cm_heatlist import O2cmHeatlist
from .scoresheet.results_processor import Results_Processor
from .scoresheet.comp_mngr_results import CompMngrResults
from .scoresheet.comp_organizer_results import CompOrgResults
from .scoresheet.ndca_prem_results import NdcaPremResults
from .scoresheet.ndca_prem_feed_results import NdcaPremFeedResults
from .scoresheet.o2cm_results import O2cmResults
from comps.models.comp import Comp
from comps.models.heat import Heat, UNKNOWN
from comps.models.heat_entry import Heat_Entry
from comps.models.result_error import Result_Error
from comps.scoresheet.calc_points import initial_elo_rating
from rankings.models.elo_rating import EloRating
from multielo import MultiElo
import numpy
import time


@shared_task(bind=True)
def clear_comp_task(self, comp_data, heat_data):
    for deserialized_object in serializers.deserialize("json", comp_data):
        comp = deserialized_object.object

    heats = list()
    for deserialized_object in serializers.deserialize("json", heat_data):
        heats.append(deserialized_object.object)
    num_heats = len(heats)

    progress_recorder = ProgressRecorder(self)
    progress_recorder.set_progress(0, num_heats)
    for index in range(num_heats):
        h = heats[index]
        heat_info = h.info
        if heat_info is None:
            break
        h.delete()
        progress_recorder.set_progress(index + 1, num_heats, description=heat_info)

    result = num_heats
    # reset the status
    comp.process_state = Comp.INITIAL
    comp.heatsheet_load_time = Comp.default_time
    comp.save()
    return result


@shared_task(bind=True)
def process_heatlist_task(self, comp_data, heatlist_data):
    for deserialized_object in serializers.deserialize("json", comp_data):
        comp = deserialized_object.object
    heatlist_dancers = list()
    for deserialized_object in serializers.deserialize("json", heatlist_data):
        heatlist_dancers.append(deserialized_object.object)
    num_dancers = len(heatlist_dancers)

    progress_recorder = ProgressRecorder(self)

    if comp.heatsheet_file:
        heatlist = FileBasedHeatlist()
        print("Using Heatlist File")
        heatlist.load(comp.heatsheet_file, heatlist_dancers)
    else:
        if comp.url_data_format == Comp.COMP_MNGR:
            heatlist = CompMngrHeatlist()
        elif comp.url_data_format == Comp.NDCA_PREM:
            heatlist = NdcaPremHeatlist()
        elif comp.url_data_format == Comp.COMP_ORG:
            heatlist = CompOrgHeatlist()
        elif comp.url_data_format == Comp.O2CM:
            heatlist = O2cmHeatlist()
        else: # Comp CompOrganizer
            heatlist = NdcaPremFeedHeatlist()


        heatlist.load(comp.heatsheet_url, heatlist_dancers)

    progress_recorder.set_progress(0, num_dancers)
    for index in range(num_dancers):
        the_name = heatlist.get_next_dancer(index, comp)
        if the_name is None:
            break
        progress_recorder.set_progress(index + 1, num_dancers, description=the_name)

    unmatched_entries = heatlist.complete_processing()
    result = [num_dancers, unmatched_entries]
    if unmatched_entries == 0:
        comp.process_state = comp.HEAT_ENTRIES_MATCHED
    else:
        comp.process_state = comp.HEATS_LOADED

    comp.heatsheet_load_time = datetime.now(tz=timezone(-timedelta(hours=4)))

    comp.save()
    return result


@shared_task(bind=True)
def process_scoresheet_task(self, comp_data):
    for deserialized_object in serializers.deserialize("json", comp_data):
        comp = deserialized_object.object

    progress_recorder = ProgressRecorder(self)

    if comp.scoresheet_file:
        results_file = comp.scoresheet_file
        results_file.open(mode="rt")
        while True:
            try:
                line = results_file.readline().decode().strip()
            except:
                print("read failure")
                break
            print(line)
            if line.startswith('Comp Name'):
                continue
            if line.startswith('Results'):
                num_heats = int(line.split('\t')[1])
                progress_recorder.set_progress(0, num_heats, description="Reading file for results")
                index = 0
                continue
            if line.startswith('--'):
                break
            heat_data = line.split('\t')
            category = heat_data[0]
            heat_number = int(heat_data[1])
            time_string = heat_data[2]
            heat_info = heat_data[3]
            matching_heat = Heat.objects.filter(comp=comp, heat_number=heat_number, info=heat_info)
            if len(matching_heat) == 0:
                print("No matching heats")
            elif len(matching_heat) > 1:
                print("More than one matching heat")
            else:
                heat = matching_heat[0]
                index += 1
                progress_recorder.set_progress(index, num_heats, description=heat_info)
            while len(line) > 0:
                # these are the entries
                line = results_file.readline().decode().strip() 
                if len(line) == 0:
                    continue
                entry_info = line.split('\t')
                shirt_number = entry_info[1]
                result = entry_info[2]
                points = entry_info[3]
                matching_entry = Heat_Entry.objects.filter(heat=heat, shirt_number=shirt_number)
                if len(matching_entry) == 0:
                    print("No matching entries")
                elif len(matching_entry) > 1:
                    print("More than one matching heat")
                else:
                    entry = matching_entry[0]
                    if result is None or points is None:
                        continue
                    entry.result = result
                    entry.points = points
                    entry.save()
                    #print(str(entry) + ' ' + result + ' ' + str(points))
                    
        unmatched_entries = 0
        results_file.close()    
    
    elif comp.scoresheet_url:
        if comp.url_data_format == Comp.COMP_MNGR:
            scoresheet = CompMngrResults()
        elif comp.url_data_format == Comp.NDCA_PREM:
             scoresheet = NdcaPremResults()
        elif comp.url_data_format == Comp.NDCA_FEED:
              scoresheet = NdcaPremFeedResults()
        elif comp.url_data_format == Comp.O2CM:
              scoresheet = O2cmResults()
        else: # CompOrganizer for now
             scoresheet = CompOrgResults()

        heats_to_process = Heat.objects.filter(comp=comp).order_by('time')
        num_heats = heats_to_process.count()

        index = 0
        progress_recorder.set_progress(0, num_heats, description="Accessing website for results")
        scoresheet.open(comp.scoresheet_url)

        for heat in heats_to_process:
            index += 1
            heat_str = heat.get_category_display() + " " + str(heat.heat_number)
            if heat.time.date() >= datetime.now(tz=timezone(-timedelta(hours=4))).date():
                progress_recorder.set_progress(index, num_heats, description= "Skipping - " + heat_str + " " + heat.info)
                continue
            
            if heat.initial_elo_value is None:
                elo_value = initial_elo_rating(heat.category, heat.info)
                if elo_value is None:
                    print("Unknown Initial Elo Rating" + str(heat))
                    res_err = Result_Error()
                    res_err.comp = comp
                    res_err.heat = heat
                    res_err.error = Result_Error.UNKNOWN_ELO_VALUE
                    res_err.save()                
                else:
                    heat.initial_elo_value = elo_value
                    heat.save()
                
            if heat.category == Heat.PRO_HEAT or heat.multi_dance() or heat.dance_off:
                if heat.style == UNKNOWN:
                    print("Unknown Heat Style " + str(heat))
                    res_err = Result_Error()
                    res_err.comp = comp
                    res_err.heat = heat
                    res_err.error = Result_Error.UNKNOWN_STYLE
                    res_err.save()

                if heat.base_value == 0:
                    print("Unknown Heat Level " + str(heat))
                    res_err = Result_Error()
                    res_err.comp = comp
                    res_err.heat = heat
                    res_err.error = Result_Error.UNKNOWN_LEVEL
                    res_err.save()

                entries_in_event = Heat_Entry.objects.filter(heat=heat)
                if entries_in_event.count() > 0:
                    heat_result = scoresheet.determine_heat_results(entries_in_event)
                    if heat_result is None:
                        print("No results for " + str(heat))
                        res_err = Result_Error()
                        res_err.comp = comp
                        res_err.heat = heat
                        res_err.error = Result_Error.NO_RESULTS_FOUND
                        res_err.save()
                    else:
                        for e in entries_in_event:
                            if e.result == "DNP":
                                print("No result found for " + str(e))
                                res_err = Result_Error()
                                res_err.comp = comp
                                res_err.heat = heat
                                res_err.couple = e.couple
                                res_err.error = Result_Error.NO_COUPLE_RESULT
                                res_err.save()
                                #e.delete()
                else:
                    print("No entries in " + str(heat))
                    res_err = Result_Error()
                    res_err.comp = comp
                    res_err.heat = heat
                    res_err.error = Result_Error.NO_ENTRIES_FOUND
                    res_err.save()

                progress_recorder.set_progress(index, num_heats, description= heat_str + " " + heat.info)

            else:  # don't score freestyles, and delete those heats
                progress_recorder.set_progress(index, num_heats, description="Deleting " + heat_str + " " + heat.info)
                heat.delete()

        unmatched_entries = len(scoresheet.late_entries)
        
    result = [index, unmatched_entries]
    if unmatched_entries == 0:
        comp.process_state = comp.RESULTS_RESOLVED
    else:
        comp.process_state = comp.SCORESHEETS_LOADED
    comp.save()
    return result


@shared_task(bind=True)
def update_elo_ratings_for_comps(self, comp_id_list):
    progress_recorder = ProgressRecorder(self)

    total_heats = 0
    
    # multiple comp IDs indicate we are recalculating the ratings from scratch
    if len(comp_id_list) > 1:
        print('Clearing couple elo ratings')
        ratings = EloRating.objects.all()
        progress_recorder.set_progress(0, len(ratings), description='clearing couple ratings')
        
        couple_index = 0
        for r in ratings:
            couple_index += 1   # increment progress indicator
            r.value = None      # claar rating
            r.num_events = 0    # reset number of events for this couple / style
            r.save()   
            progress_recorder.set_progress(couple_index, len(ratings), description='clearing couple ratings')
    
    # determine how many heats there are to recalculate
    for comp_id in comp_id_list:
        comp = get_object_or_404(Comp, pk=comp_id)
        heats = Heat.objects.filter(comp=comp).order_by('time', 'heat_number') 
        
        # if recalculating all the ratings, reset the process state 
        if len(comp_id_list) > 1:
            if comp.process_state in [Comp.ELO_RATINGS_UPDATED, Comp.COMPLETE]:
                comp.process_state = Comp.RESULTS_RESOLVED
                comp.save() 
            # if recalculating all the ratings, clear elo_applied flag for all heats
            for h in heats:
                if h.elo_applied:
                    h.elo_applied = False
                    h.save()     
        
        # add the number of heats for this comp to the total. 
        # If this is the only comp being processed this still works
        total_heats += len(heats)
        progress_recorder.set_progress(0, total_heats, description='collecting heats')
        
    heat_index = 0
    
    # initialize the multi-elo entries
    elo = MultiElo(score_function_base=1.25)    
    
    for comp_id in comp_id_list:
        # if recalculating all ratings, get the comp and heats for this comp id
        # if only processing one comp, we already have the comp and heats
        if len(comp_id_list) > 1:
            comp = get_object_or_404(Comp, pk=comp_id)    
            heats = Heat.objects.filter(comp=comp).order_by('time', 'heat_number')    
    
        result = total_heats
        # for each heat in this comp
        for h in heats:
            
            heat_index += 1
            
            # skip this heat if elo ratings have already been applied
            if h.elo_applied:
                info = ("Elo rating already applied: " + str (h))
                progress_recorder.set_progress(heat_index, total_heats, description=info)
                print(info)
            
            else:
                info = ("Updated Elo ratings for: " + str (h))
                # get the entries for this heat in order of their results
                entries = Heat_Entry.objects.filter(heat=h).order_by('-points')
                
                # if there are multiple entries, update elo ratings for each entry
                if len(entries) > 1:
                    # determine initial elo rating for entries with no previous rating
                    if h.initial_elo_value is None:                    
                        print("No initial Elo value for " + str(h))   
                        continue
                    else:
                        initial_rating = h.initial_elo_value   
                        #print(str(h) + ' ' + str(h.time) + ' ' + h.info + ' ' + h.style +  ' ' + str(initial_rating))
                    
                    rating_list = list()
                    elo_inputs = list()
                    # for each entry
                    for e in entries:
                        # get their existing elo rating or create one with initial rating
                        try:
                            rating = EloRating.objects.get(couple=e.couple, style=h.style)
                            if rating.value is None:
                                rating.value = initial_rating
                                rating.save()
                        except EloRating.DoesNotExist:
                            rating = EloRating()
                            rating.couple = e.couple
                            rating.style = h.style
                            rating.value = initial_rating
                            rating.save()
                            
                        rating_list.append(rating)
                        elo_inputs.append(rating.value)
                    
                    new_ratings = elo.get_new_ratings(numpy.array(elo_inputs))
                    
                    for index in range(len(rating_list)):
                        difference = new_ratings[index] - elo_inputs[index]
                        #print('  ' + str(rating_list[index]) + ' ' + str(round(new_ratings[index], 2)) + ' ' + str(round(difference, 2)))
        
                        entries[index].elo_adjust = difference
                        entries[index].save()
                        rating_list[index].value = new_ratings[index]
                        rating_list[index].num_events += 1
                        rating_list[index].save()
                        
                    h.elo_applied = True
                    progress_recorder.set_progress(heat_index, total_heats, description=info)
                    h.save()            
            
        else:
            # processed all heats, set process state accordingly
            comp.process_state = Comp.ELO_RATINGS_UPDATED
            comp.save()            
        
    
    return result