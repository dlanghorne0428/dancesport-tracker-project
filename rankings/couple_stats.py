from comps.models import Heat_Entry
from decimal import Decimal

def couple_stats(couple, heat_style):
    stats = {'couple': couple, 'event_count': 0, 'total_points': Decimal(0.00), 'rating': Decimal(0.00), 'index': 0}
    entries = Heat_Entry.objects.filter(couple=couple).filter(heat__style=heat_style)
    for e in entries:
        if e.points is not None:
            stats['event_count'] += 1
            stats['total_points'] += e.points
    if stats['event_count'] > 0:
        stats['total_points'] = round(stats['total_points'], 2)
        stats['rating'] = round(stats['total_points'] / stats['event_count'], 2)
    return stats
