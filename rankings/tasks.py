from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.core import serializers
from django.core.paginator import Paginator
from comps.models import Couple, HeatEntry
from operator import itemgetter
import time


@shared_task(bind=True)
def process_rating_task(self, heat_couple_type, heat_style, last_name, page_number):
    progress_recorder = ProgressRecorder(self)
    couples = Couple.objects.filter(couple_type=heat_couple_type)
    couple_stats = list()
    for c in couples:
        stats = {'couple': c, 'event_count': 0, 'total_points': 0.0, 'rating': 0.0, 'index': 0}
        couple_stats.append(stats)

    progress_recorder.set_progress(0, len(couple_stats))
    index = 0
    print("Found couples", len(couple_stats))
    for cs in couple_stats:
        entries = HeatEntry.objects.filter(couple=cs['couple']).filter(heat__style=heat_style)
        for e in entries:
            if e.points is not None:
                cs['event_count'] += 1
                cs['total_points'] += e.points
        if cs['event_count'] > 0:
            cs['total_points'] = round(cs['total_points'], 2)
            cs['rating'] = round(cs['total_points'] / cs['event_count'], 2)

        index += 1
        progress_recorder.set_progress(index, len(couple_stats))

    couple_stats.sort(key=itemgetter('rating'), reverse=True)
    while couple_stats[-1]['event_count'] == 0:
        couple_stats.pop()
        if len(couple_stats) == 0:
            break
    for i in range(len(couple_stats)):
        couple_stats[i]['index'] = i + 1
    if last_name is not None:
        if len(last_name) > 0:
            couple_stats = list(filter(lambda dancer: last_name in dancer['couple'].dancer_1.name_last  or \
                                                      last_name in dancer['couple'].dancer_2.name_last, couple_stats))
    paginator = Paginator(couple_stats, 16)
    page_obj = paginator.get_page(page_number)

    result = [cs, page_obj]
    return result
