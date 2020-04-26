from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.core import serializers
from .comp_mngr_heatlist import CompMngrHeatlist
from .comp_organizer_heatlist import CompOrgHeatlist
from .ndca_prem_heatlist import NdcaPremHeatlist
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
        progress_recorder.set_progress(index, num_dancers, description=the_name)
    unmatched_heat_count = heatlist.complete_processing()
    result = [num_dancers, unmatched_heat_count]
    return result
