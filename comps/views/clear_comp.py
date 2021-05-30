from django.core import serializers
from django.shortcuts import render
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heatlist_error import Heatlist_Error
from comps.tasks import clear_comp_task

def clear_comp(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    comp_objects = Comp.objects.filter(pk=comp_id)
    if len(comp_objects) == 1:
        comp=comp_objects[0]

    # delete any heatlist errors associated with this comp
    Heatlist_Error.objects.filter(comp=comp).delete()

    # find all the heats in this comp
    heats = Heat.objects.filter(comp=comp)

    comp_data = serializers.serialize("json", comp_objects)
    heat_data = serializers.serialize("json", heats)

    result = clear_comp_task.delay(comp_data, heat_data)

    return render(request, 'comps/process_clear_comp.html', context={'task_id': result.task_id, 'comp': comp})
