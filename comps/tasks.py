from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.core import serializers
from .comp_mngr_heatlist import CompMngrHeatlist
from .models import Comp
import time

@shared_task(bind=True)
def my_task(self, seconds):
    print(seconds)
    progress_recorder = ProgressRecorder(self)
    result = 0
    for i in range(seconds):
        time.sleep(1)
        result += i
        progress_recorder.set_progress(i + 1, seconds)
    return result

@shared_task(bind=True)
def process_heatlist_task(self, comp_data):
    for deserialized_object in serializers.deserialize("json", comp_data):
    #do_something_with(obj)
        comp = deserialized_object.object
        progress_recorder = ProgressRecorder(self)
        result = 0
        heatlist = CompMngrHeatlist()
        heatlist.open(comp.heatsheet_url)
        num_dancers = len(heatlist.dancers)
        progress_recorder.set_progress(0, num_dancers)
        for index in range(num_dancers):
            the_name = heatlist.get_next_dancer(index, comp)
            result += 1
            progress_recorder.set_progress(index, num_dancers, description=the_name)
        heatlist.complete_processing()
    return result
