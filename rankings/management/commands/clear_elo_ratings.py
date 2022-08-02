from django.core.management.base import BaseCommand
from rankings.models.elo_rating import EloRating


class Command(BaseCommand):
    def handle(self, *args, **options):
        ratings = EloRating.objects.all()
        for r in ratings:
            r.value = None
            r.save()
