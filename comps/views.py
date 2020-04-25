from django.core import serializers
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from .models import Comp, Heat, HeatEntry, UnmatchedHeatEntry, HeatlistDancer
from .forms import CompForm
from .tasks import my_task, process_heatlist_task
from .comp_mngr_heatlist import CompMngrHeatlist
from .comp_organizer_heatlist import CompOrgHeatlist

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
    unmatched_entries = UnmatchedHeatEntry.objects.all().order_by('entry')
    if request.method == "GET":
        comp = get_object_or_404(Comp, pk=comp_id)
        if unmatched_entries.count() == 0:
            # all unmatched entries resolved, delete heatlist_dancer entries from database
            heatlist_dancers = HeatlistDancer.objects.all().delete()
            return redirect("comps:heats", comp_id)
        else:
            first_unmatched = unmatched_entries.first()
            first_set = unmatched_entries.filter(entry=first_unmatched.entry).order_by('couple__dancer_1')
            return render(request, "comps/resolve_mismatches.html", {'comp':comp, 'first_entry': first_unmatched, 'unmatched_entries': first_set})
    else: # POST
        submit = request.POST.get("submit")
        if submit == "Reset":
            return redirect('comps:heats', comp_id)
        elif submit == "Submit":
            couple = request.POST.get("couple")
            first_entry = unmatched_entries.first()
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
        elif submit == "Delete":
            first_entry = unmatched_entries.first()
            # deleting the heat entry that this unmatched entry points to will also delete all the unmatched entries
            # that point to the same entry.
            first_entry.entry.delete()
            return redirect("comps:heat_entries", first_entry.entry.heat.id)


def resolve_dancers(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    #TODO: if no heatlist dancers, obtain list of dancers from this comp's heats?
    names_to_format = HeatlistDancer.objects.filter(formatting_needed = True)
    current_name = names_to_format.first()

    if request.method == "POST":
        submit = request.POST.get("submit")
        # determine what page to show
        heatlist_dancers = HeatlistDancer.objects.all().order_by('pk')
        for index in range(len(heatlist_dancers)):
            if current_name.name == heatlist_dancers[index].name:
                page_number = index // 16 + 1
                print("Page Number is", page_number)
                break
        if submit == "Delete":
            current_name.formatting_needed = False
            current_name.save()
        elif submit == "Submit":
            new_name = request.POST.get("spelling")
            current_name.name = new_name
            current_name.formatting_needed = False
            print(current_name.name)
            current_name.save()

        # find next name to format
        names_to_format = HeatlistDancer.objects.filter(formatting_needed = True)
        current_name = names_to_format.first()
    else: # GET
        page_number = request.GET.get('page')

    # do this for either GET or POST
    heatlist_dancers = HeatlistDancer.objects.all().order_by('pk')
    paginator = Paginator(heatlist_dancers, 16)
    page_obj = paginator.get_page(page_number)

    possible_formats = list()
    if current_name is not None:
        fields = current_name.name.split()
        for field in range(1, len(fields)):
            possible_formats.append(current_name.format_name(current_name.name, simple=False, split_on=field))

    return render(request, 'comps/dancers.html', {'comp': comp, 'page_obj': page_obj, 'current_name': current_name, 'possible_formats': possible_formats })


def load_dancers(request, comp_id):
    #comp = get_object_or_404(Comp, pk=comp_id)
    comp_objects = Comp.objects.filter(pk=comp_id)
    if len(comp_objects) == 1:
        comp=comp_objects[0]

    #if HeatlistDancer.objects.count() > 0:
    #    heatlist_dancers = HeatlistDancer.objects.all().delete()

    if comp.url_data_format == Comp.COMP_MNGR:
        heatlist = CompMngrHeatlist()
    else: # CompOrganizer for now
        heatlist = CompOrgHeatlist()

    heatlist.open(comp.heatsheet_url)

    for d in heatlist.dancers:
        in_database = HeatlistDancer.objects.filter(name = d.name)
        if in_database.count() == 0:
            d.save()

    return redirect("comps:resolve_dancers", comp.id)


def load_heats(request, comp_id):
    comp_objects = Comp.objects.filter(pk=comp_id)
    if len(comp_objects) == 1:
        comp=comp_objects[0]

    heatlist_dancers = HeatlistDancer.objects.all()

    comp_data = serializers.serialize("json", comp_objects)
    heatlist_dancer_data = serializers.serialize("json", heatlist_dancers)

    result = process_heatlist_task.delay(comp_data, heatlist_dancer_data)
    return render(request, 'comps/process_heatlist.html', context={'task_id': result.task_id, 'comp': comp})
