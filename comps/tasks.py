from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.core import serializers
from .heatlist.file_based_heatlist import FileBasedHeatlist
from .heatlist.comp_mngr_heatlist import CompMngrHeatlist
from .heatlist.comp_organizer_heatlist import CompOrgHeatlist
from .heatlist.ndca_prem_heatlist import NdcaPremHeatlist
from .models import Comp
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
