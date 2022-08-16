from django.core.management.base import BaseCommand
from comps.models.heat import Heat

class Command(BaseCommand):
    def handle(self, *args, **options):
        heats = Heat.objects.filter(category=Heat.PRO_HEAT)
        for h in heats:
            if 'CLOSED' in h.info.upper():
                print(str(h) + ' ' + h.info)

