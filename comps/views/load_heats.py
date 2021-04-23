from django.core import serializers
from django.shortcuts import render
from comps.models.comp import Comp
from comps.models.heatlist_dancer import Heatlist_Dancer
from comps.tasks import process_heatlist_task


def load_heats(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    comp_objects = Comp.objects.filter(pk=comp_id)
    if len(comp_objects) == 1:
        comp=comp_objects[0]

    heatlist_dancers = Heatlist_Dancer.objects.filter(comp=comp)

    comp_data = serializers.serialize("json", comp_objects)
    heatlist_dancer_data = serializers.serialize("json", heatlist_dancers)

    result = process_heatlist_task.delay(comp_data, heatlist_dancer_data)
    return render(request, 'comps/process_heatlist.html', context={'task_id': result.task_id, 'comp': comp})
