from comps.models import Heat_Entry
from decimal import Decimal
from django.db.models import Q

def process_entries(entries, stats):
    for e in entries:
        if e.points is not None:
            stats['event_count'] += 1
            stats['total_points'] += e.points
    if stats['event_count'] > 0:
        stats['total_points'] = round(stats['total_points'], 2)
        stats['rating'] = round(stats['total_points'] / stats['event_count'], 2)



def couple_stats(couple, heat_style=None):
    stats = {'couple': couple, 'event_count': 0, 'total_points': Decimal(0.00), 'rating': Decimal(0.00), 'index': 0}
    entries = Heat_Entry.objects.filter(couple=couple)
    if heat_style is not None:
        entries = entries.filter(heat__style=heat_style)
    process_entries(entries, stats)
    return stats


def instructor_stats(instructor, heat_style=None):
    stats = {'instructor': instructor, 'event_count': 0, 'total_points': Decimal(0.00), 'rating': Decimal(0.00), 'index': 0}
    entries = Heat_Entry.objects.filter(Q(couple__couple_type="PAC") | Q(couple__couple_type="JPC")).filter(couple__dancer_2=instructor)
    if heat_style is not None:
        entries = entries.filter(heat__style=heat_style)
    process_entries(entries, stats)
    return stats


def student_stats(student, heat_style=None):
    stats = {'student': student, 'event_count': 0, 'total_points': Decimal(0.00), 'rating': Decimal(0.00), 'index': 0}
    entries = Heat_Entry.objects.filter(Q(couple__couple_type="PAC") | Q(couple__couple_type="JPC")).filter(couple__dancer_1=student)
    if heat_style is not None:
        entries = entries.filter(heat__style=heat_style)
    process_entries(entries, stats)
    return stats


def pro_comp_stats(dancer, heat_style=None):
    stats = {'dancer': dancer, 'event_count': 0, 'total_points': Decimal(0.00), 'rating': Decimal(0.00), 'index': 0}
    entries = Heat_Entry.objects.filter(couple__couple_type="PRC").filter(Q(couple__dancer_1=dancer) | Q(couple__dancer_2=dancer))
    if heat_style is not None:
        entries = entries.filter(heat__style=heat_style)
    process_entries(entries, stats)
    return stats


def am_comp_stats(dancer, heat_style=None):
    stats = {'dancer': dancer, 'event_count': 0, 'total_points': Decimal(0.00), 'rating': Decimal(0.00), 'index': 0}
    entries = Heat_Entry.objects.filter(Q(couple__couple_type="AMC") | Q(couple__couple_type="JAC")).filter(Q(couple__dancer_1=dancer) | Q(couple__dancer_2=dancer))
    if heat_style is not None:
        entries = entries.filter(heat__style=heat_style)
    process_entries(entries, stats)
    return stats
