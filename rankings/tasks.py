from celery import shared_task, task
from celery_progress.backend import ProgressRecorder
from django.core.cache import cache
from comps.models import Couple, Heat_Entry
from decimal import Decimal
from operator import itemgetter
import time

@shared_task()
def calc_couple_ratings(heat_couple_type, heat_style, cache_key):
    couples = Couple.objects.filter(couple_type=heat_couple_type)
    couple_stats = list()
    for c in couples:
        stats = {'couple': c, 'event_count': 0, 'total_points': Decimal(0.00), 'rating': Decimal(0.00), 'index': 0}
        couple_stats.append(stats)

    for cs in couple_stats:
        entries = Heat_Entry.objects.filter(couple=cs['couple']).filter(heat__style=heat_style)
        for e in entries:
            if e.points is not None:
                cs['event_count'] += 1
                cs['total_points'] += e.points
        if cs['event_count'] > 0:
            cs['total_points'] = round(cs['total_points'], 2)
            cs['rating'] = round(cs['total_points'] / cs['event_count'], 2)

    couple_stats.sort(key=itemgetter('rating'), reverse=True)
    while couple_stats[-1]['event_count'] == 0:
        couple_stats.pop()
        if len(couple_stats) == 0:
            break
    for i in range(len(couple_stats)):
        couple_stats[i]['index'] = i + 1

    if cache.add(cache_key, couple_stats):
        print("Wrote " + cache_key + ' ' + str(len(couple_stats)))
    else:
        print(cache_key + " exists.")
    #return couple_stats
