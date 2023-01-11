from django.contrib import admin
from .models.comp import Comp
from .models.comp_couple import Comp_Couple
from .models.heat import Heat
from .models.heatlist_dancer import Heatlist_Dancer

admin.site.register(Comp)
admin.site.register(Comp_Couple)
admin.site.register(Heat)
admin.site.register(Heatlist_Dancer)
