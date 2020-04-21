from django.core import serializers
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from .models import Comp, Heat, HeatResult
from .forms import CompForm
from .tasks import my_task, process_heatlist_task
from .comp_mngr_heatlist import CompMngrHeatlist

def all_comps(request):
    comps = Comp.objects.order_by('start_date')
    paginator = Paginator(comps, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/all_comps.html", {'page_obj': page_obj})

def detail(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    return render(request, "comps/detail.html", {'comp':comp})

def createcomp(request):
    if request.method == "GET":
        return render(request, 'comps/createcomp.html', {'form':CompForm()})
    else:
        try:
            form = CompForm(request.POST)
            form.save()
            return redirect('all_comps')
        except ValueError:
            return render(request, 'comps/createcomp.html', {'form':CompForm(), 'error': "Invalid data submitted."})


def heats(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    heats_from_comp = Heat.objects.filter(comp=comp).order_by('time')
    paginator = Paginator(heats_from_comp, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/heats.html", {'comp': comp, 'page_obj': page_obj})

def heat_entries(request, heat_id):
    heat = get_object_or_404(Heat, pk=heat_id)
    results = HeatResult.objects.filter(heat=heat)
    return render(request, "comps/heat_entries.html", {'comp_title': heat.comp.title, 'heat': heat, 'results': results})


def resolve_mismatches(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    return render(request, "comps/resolve_mismatches.html", {'comp':comp})


def process_heatlists(request, comp_id):
    #comp = get_object_or_404(Comp, pk=comp_id)
    comp_objects = Comp.objects.filter(pk=comp_id)
    if len(comp_objects) == 1:
        comp=comp_objects[0]
    comp_data = serializers.serialize("json", comp_objects)
    #heats_to_delete = Heat.objects.filter(comp=comp).delete()

    result = process_heatlist_task.delay(comp_data)
    return render(request, 'comps/process_heatlist.html', context={'task_id': result.task_id, 'comp': comp})
