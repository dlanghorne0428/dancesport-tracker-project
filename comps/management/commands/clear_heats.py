from django.core.management.base import BaseCommand
from comps.models import Heat

class Command(BaseCommand):
    def handle(self, *args, **options):
        Heat.objects.all().delete()
