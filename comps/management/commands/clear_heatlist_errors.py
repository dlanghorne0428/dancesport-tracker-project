from django.core.management.base import BaseCommand
from comps.models.heatlist_error import Heatlist_Error

class Command(BaseCommand):
    def handle(self, *args, **options):
        Heatlist_Error.objects.all().delete()
