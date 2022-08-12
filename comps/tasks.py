from celery import shared_task
from celery_progress.backend import ProgressRecorder
from datetime import datetime, date, timezone, timedelta
from django.core import serializers
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
from comps.views.update_elo_ratings import initial_elo_rating
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
