from django.core import serializers
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from .models import Comp, Heat, HeatEntry, UnmatchedHeatEntry, HeatlistDancer
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
    entries = HeatEntry.objects.filter(heat=heat).order_by('shirt_number')
    return render(request, "comps/heat_entries.html", {'comp_title': heat.comp.title, 'comp_id': heat.comp.id, 'heat': heat, 'entries': entries})


def resolve_mismatches(request, comp_id):
    if request.method == "GET":
        comp = get_object_or_404(Comp, pk=comp_id)
        unmatched_entries = UnmatchedHeatEntry.objects.all().order_by('entry')
        if unmatched_entries.count() == 0:
            # all unmatched entries resolved, delete heatlist_dancer entries from database
            heatlist_dancers = HeatlistDancer.objects.all().delete()
            return redirect("comps:heats", comp_id)
        else:
            first_unmatched = unmatched_entries.first()
            first_set = unmatched_entries.filter(entry=first_unmatched.entry)
            return render(request, "comps/resolve_mismatches.html", {'comp':comp, 'first_entry': first_unmatched, 'unmatched_entries': first_set})
    else: # POST
        submit = request.POST.get("submit")
        if submit == "Submit":
            couple = request.POST.get("couple")
            first_entry = UnmatchedHeatEntry.objects.first()
            first_set = UnmatchedHeatEntry.objects.filter(dancer=first_entry.dancer, partner=first_entry.partner)
            for e in first_set:
                if str(e.couple) == couple:
                    # update the heat entry with the selected couple
                    e.entry.couple = e.couple
                    e.entry.code = e.code
                    #print("Heat Entry", e.entry, e.entry.heat.category, e.entry.heat.heat_number, "being set to", couple, "with code", e.entry.code)
                    e.entry.save()
                # delete the heat entries that have been resolved
                #print("deleting unmatched entry", e.couple)
                e.delete()
            return redirect("comps:heat_entries", first_entry.entry.heat.id)
        else:
            return redirect('comps:heats', comp_id)


def process_heatlists(request, comp_id):
    #comp = get_object_or_404(Comp, pk=comp_id)
    comp_objects = Comp.objects.filter(pk=comp_id)
    if len(comp_objects) == 1:
        comp=comp_objects[0]
    comp_data = serializers.serialize("json", comp_objects)
    #heats_to_delete = Heat.objects.filter(comp=comp).delete()

    result = process_heatlist_task.delay(comp_data)
    return render(request, 'comps/process_heatlist.html', context={'task_id': result.task_id, 'comp': comp})
