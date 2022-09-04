#from celery import shared_task
#from celery_progress.backend import ProgressRecorder
#from django.core.cache import cache
#from comps.models import Heat_Entry
#from rankings.models import Dancer, Couple
#from rankings.rating_stats import couple_stats, instructor_stats
#from decimal import Decimal
#from operator import itemgetter
#import time

#@shared_task(bind=True)
#def calc_couple_ratings(self, heat_couple_type, heat_style, cache_key):
    #progress_recorder = ProgressRecorder(self)

    #couples = Couple.objects.filter(couple_type=heat_couple_type)
    #progress_recorder.set_progress(0, len(couples))
    #couple_stat_list = list()

    #index = 0
    #for c in couples:
        #couple_stat_list.append(couple_stats(c, heat_style))
        #index += 1
        #progress_recorder.set_progress(index, len(couples))

    #couple_stat_list.sort(key=itemgetter('rating'), reverse=True)
    #while couple_stat_list[-1]['event_count'] == 0:
        #couple_stat_list.pop()
        #if len(couple_stat_list) == 0:
            #break
    #for i in range(len(couple_stat_list)):
        #couple_stat_list[i]['index'] = i + 1

    #cache.add(cache_key, couple_stat_list)

    #result = index
    #return result


#@shared_task(bind=True)
#def calc_teacher_ratings(self, heat_style, cache_key):
    #progress_recorder = ProgressRecorder(self)

    #teachers = Dancer.objects.filter(dancer_type="PRO")
    #progress_recorder.set_progress(0, len(teachers))
    #teacher_stat_list = list()
    #index = 0
    #for t in teachers:
        #teacher_stat_list.append(instructor_stats(t, heat_style))
        #index += 1
        #progress_recorder.set_progress(index, len(teachers))

    #teacher_stat_list.sort(key=itemgetter('rating'), reverse=True)
    #while teacher_stat_list[-1]['event_count'] == 0:
        #teacher_stat_list.pop()
        #if len(teacher_stat_list) == 0:
            #break
    #for i in range(len(teacher_stat_list)):
        #teacher_stat_list[i]['index'] = i + 1

    #cache.set(cache_key, teacher_stat_list)

    #result = index
    #return result
