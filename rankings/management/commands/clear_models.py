from django.core.management.base import BaseCommand
from rankings.models import Dancer, Couple

class Command(BaseCommand):
    def handle(self, *args, **options):
        Couple.objects.all().delete()
        Dancer.objects.all().delete()
