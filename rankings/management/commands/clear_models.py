from django.core.management.base import BaseCommand
from rankings.models.couple import Couple
from rankings.models.dancer import Dancer
from rankings.models.elo_rating import EloRating


class Command(BaseCommand):
    def handle(self, *args, **options):
        Couple.objects.all().delete()
        Dancer.objects.all().delete()
