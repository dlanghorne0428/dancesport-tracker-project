from django.core import serializers
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from comps.models.comp import Comp
from comps.tasks import process_scoresheet_task

def load_scoresheets(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    comp_objects = Comp.objects.filter(pk=comp_id)
    if len(comp_objects) == 1:
        comp=comp_objects[0]

    comp_data = serializers.serialize("json", comp_objects)

    result = process_scoresheet_task.delay(comp_data)

    # the rankings will have changed after loading these scoresheets, so clear out any cached rankings
    cache.clear()

    return render(request, 'comps/load_scoresheets.html', context={'task_id': result.task_id, 'comp': comp})
