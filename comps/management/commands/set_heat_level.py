from django.core.management.base import BaseCommand
from comps.models.heat import Heat

class Command(BaseCommand):
    def handle(self, *args, **options):
        heats = Heat.objects.all()
        for heat in heats:
            print('.', end="")
            heat.set_level()
            if heat.base_value == 0:
                print(heat.comp.title, "Heat", heat.heat_number, heat.base_value)
                heat.save()
