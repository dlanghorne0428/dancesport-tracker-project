from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.core.cache import cache
from comps.models import Heat_Entry
from rankings.models import Dancer, Couple
from decimal import Decimal
from operator import itemgetter
import time

@shared_task(bind=True)
def calc_couple_ratings(self, heat_couple_type, heat_style, cache_key):
    progress_recorder = ProgressRecorder(self)

    couples = Couple.objects.filter(couple_type=heat_couple_type)
    progress_recorder.set_progress(0, len(couples))
    couple_stats = list()
    for c in couples:
        stats = {'couple': c, 'event_count': 0, 'total_points': Decimal(0.00), 'rating': Decimal(0.00), 'index': 0}
        couple_stats.append(stats)

    index = 0
    for cs in couple_stats:
        entries = Heat_Entry.objects.filter(couple=cs['couple']).filter(heat__style=heat_style)
        for e in entries:
            if e.points is not None:
                cs['event_count'] += 1
                cs['total_points'] += e.points
        if cs['event_count'] > 0:
            cs['total_points'] = round(cs['total_points'], 2)
            cs['rating'] = round(cs['total_points'] / cs['event_count'], 2)
        index += 1
        progress_recorder.set_progress(index, len(couples))

    couple_stats.sort(key=itemgetter('rating'), reverse=True)
    while couple_stats[-1]['event_count'] == 0:
        couple_stats.pop()
        if len(couple_stats) == 0:
            break
    for i in range(len(couple_stats)):
        couple_stats[i]['index'] = i + 1

    cache.add(cache_key, couple_stats)

    result = index
    return result


@shared_task(bind=True)
def calc_teacher_ratings(self, heat_style, cache_key):
    progress_recorder = ProgressRecorder(self)

    teachers = Dancer.objects.filter(dancer_type="PRO")
    progress_recorder.set_progress(0, len(teachers))
    teacher_stats = list()
    for t in teachers:
        if Couple.objects.filter(couple_type="PAC").filter(dancer_2=t).count() > 0:
            stats = {'teacher': t, 'event_count': 0, 'total_points': Decimal(0.00), 'rating': Decimal(0.00), 'index': 0}
            teacher_stats.append(stats)

    possible_matching_entries = Heat_Entry.objects.filter(couple__couple_type="PAC").filter(heat__style=heat_style)

    index = 0
    for ts in teacher_stats:
        entries = possible_matching_entries.filter(couple__dancer_2=ts['teacher'])
        for e in entries:
            if e.points is not None:
                ts['event_count'] += 1
                ts['total_points'] += e.points
        if ts['event_count'] > 0:
            ts['total_points'] = round(ts['total_points'], 2)
            ts['rating'] = round(ts['total_points'] / ts['event_count'], 2)

        index += 1
        progress_recorder.set_progress(index, len(teachers))

    teacher_stats.sort(key=itemgetter('rating'), reverse=True)
    while teacher_stats[-1]['event_count'] == 0:
        teacher_stats.pop()
        if len(teacher_stats) == 0:
            break
    for i in range(len(teacher_stats)):
        teacher_stats[i]['index'] = i + 1

    cache.set(cache_key, teacher_stats)

    result = index
    return result
