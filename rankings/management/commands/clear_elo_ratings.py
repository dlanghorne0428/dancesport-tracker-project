from django.core.management.base import BaseCommand
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from rankings.models.elo_rating import EloRating


class Command(BaseCommand):
    def handle(self, *args, **options):
        print('Clearing couple elo ratings')
        ratings = EloRating.objects.all()
        for r in ratings:
            r.value = None
            r.save()
            
        print('Resetting comp process state')
        comps = Comp.objects.all()
        for c in comps:
            if c.process_state == Comp.ELO_RATINGS_UPDATED:
                c.process_state = Comp.RESULTS_RESOLVED
                c.save()
                
        print('Clearing heat elo status')        
        heats = Heat.objects.all()
        for h in heats:
            if h.elo_applied:
                h.elo_applied = False
                h.save()
                
        print('Clearing heat entry elo adjustments')
        entries = Heat_Entry.objects.all()
        for e in entries:
            if e.elo_adjust is not None:
                e.elo_adjust = None
                e.save()
                
