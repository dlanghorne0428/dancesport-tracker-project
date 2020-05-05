from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.core import serializers
from .heatlist.file_based_heatlist import FileBasedHeatlist
from .heatlist.comp_mngr_heatlist import CompMngrHeatlist
from .heatlist.comp_organizer_heatlist import CompOrgHeatlist
from .heatlist.ndca_prem_heatlist import NdcaPremHeatlist
from .scoresheet.results_processor import Results_Processor
from .scoresheet.comp_mngr_results import CompMngrResults
from .scoresheet.comp_organizer_results import CompOrgResults
from .models import Comp, Heat, HeatEntry
import time


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
        heatlist.load(comp.heatsheet_file, heatlist_dancers)
    else:
        if comp.url_data_format == Comp.COMP_MNGR:
            heatlist = CompMngrHeatlist()
        elif comp.url_data_format == Comp.NDCA_PREM:
            heatlist = NdcaPremHeatlist()
        else: # Comp CompOrganizer
            heatlist = CompOrgHeatlist()

        heatlist.load(comp.heatsheet_url, heatlist_dancers)

    progress_recorder.set_progress(0, num_dancers)
    for index in range(num_dancers):
        the_name = heatlist.get_next_dancer(index, comp)
        if the_name is None:
            break
        progress_recorder.set_progress(index, num_dancers, description=the_name)

    unmatched_entries = heatlist.complete_processing()
    result = [index, unmatched_entries]
    if unmatched_entries == 0:
        comp.process_state = comp.HEAT_ENTRIES_MATCHED
    else:
        comp.process_state = comp.HEATS_LOADED
    comp.save()
    return result


@shared_task(bind=True)
def process_scoresheet_task(self, comp_data):
    for deserialized_object in serializers.deserialize("json", comp_data):
        comp = deserialized_object.object

    progress_recorder = ProgressRecorder(self)

    if comp.scoresheet_url:
        if comp.url_data_format == Comp.COMP_MNGR:
            scoresheet = CompMngrResults()
        # elif comp.url_data_format == Comp.NDCA_PREM:
        #     heatlist = NdcaPremHeatlist()
        else: # CompOrganizer for now
             scoresheet = CompOrgResults()

        scoresheet.open(comp.scoresheet_url)

        heats_to_process = Heat.objects.filter(comp=comp).order_by('heat_number')
        num_heats = heats_to_process.count()

        index = 0
        progress_recorder.set_progress(0, num_heats)
        for heat in heats_to_process:
            index += 1
            entries_in_event = HeatEntry.objects.filter(heat=heat)
            scoresheet.determine_heat_results(entries_in_event)
            for e in entries_in_event:
                if e.result == "DNP":
                    print("Deleting", e)
                    e.delete()

            progress_recorder.set_progress(index, num_heats, description=str(heat) + " " + heat.info)

        xyz()

        unmatched_entries = len(scoresheet.late_entries)
        result = [index, unmatched_entries]
        if unmatched_entries == 0:
            comp.process_state = comp.RESULTS_RESOLVED
        else:
            comp.process_state = comp.SCORESHEETS_LOADED
        comp.save()
        return result
