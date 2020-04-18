from django.core.management.base import BaseCommand
from comps.models import Heat, HeatResult

class Command(BaseCommand):
    def handle(self, *args, **options):
        HeatResult.objects.all().delete()
        Heat.objects.all().delete()
