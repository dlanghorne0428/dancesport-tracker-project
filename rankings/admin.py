from django.contrib import admin
from .models import Dancer, Couple

# Register your models here.
# class CoupleAdmin(admin.ModelAdmin):
#     list_display = ('couple_type', 'dancer_1_name')
#
#     def dancer_1_name(self, instance):
#         return instance.dancer_1.name_last

admin.site.register(Dancer)
admin.site.register(Couple)
