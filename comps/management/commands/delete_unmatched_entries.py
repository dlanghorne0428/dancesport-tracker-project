from django.core.management.base import BaseCommand
from comps.models.unmatched_heat_entry import Unmatched_Heat_Entry

class Command(BaseCommand):
    def handle(self, *args, **options):
        Unmatched_Heat_Entry.objects.all().delete()
