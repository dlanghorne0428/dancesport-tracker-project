from django.core import serializers
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from .models import Comp, Heat, HeatEntry, UnmatchedHeatEntry, HeatlistDancer
from .forms import CompForm, HeatForm
from .tasks import process_heatlist_task
from .file_based_heatlist import FileBasedHeatlist
from .comp_mngr_heatlist import CompMngrHeatlist
from .comp_organizer_heatlist import CompOrgHeatlist
from .ndca_prem_heatlist import NdcaPremHeatlist
from .filters import HeatFilter

def all_comps(request):
    comps = Comp.objects.order_by('start_date')
    paginator = Paginator(comps, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/all_comps.html", {'page_obj': page_obj})

def comp_detail(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    return render(request, "comps/comp_detail.html", {'comp':comp})

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


def comp_heats(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    f = HeatFilter(request.GET, queryset=Heat.objects.filter(comp=comp).order_by('time'))
    paginator = Paginator(f.qs, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/comp_heats.html", {'comp': comp, 'page_obj': page_obj, 'filter': f})


def heat(request, heat_id):
    heat = get_object_or_404(Heat, pk=heat_id)
    entries = HeatEntry.objects.filter(heat=heat).order_by('shirt_number')
    comp_id = heat.comp_id
    if request.method == "GET":
        form = HeatForm(instance=heat)
        return render(request, 'comps/heat.html', {'heat': heat, 'form': form, 'entries': entries})
    else:
        try:
            form = HeatForm(request.POST, instance=heat)
            form.save()
            return redirect('comps:comp_heats', comp_id)
        except ValueError:
            return render(request, 'comps/heat.html', {'heat': heat, 'form': form, 'error': "Invalid data submitted."})


def resolve_mismatches(request, comp_id):
    unmatched_entries = UnmatchedHeatEntry.objects.all().order_by('entry')
    if request.method == "GET":
        comp = get_object_or_404(Comp, pk=comp_id)
        if unmatched_entries.count() == 0:
            # all unmatched entries resolved, delete heatlist_dancer entries from database
            heatlist_dancers = HeatlistDancer.objects.all().delete()
            comp.process_state = comp.HEAT_ENTRIES_MATCHED
            comp.save()
            return redirect("comps:comp_heats", comp_id)
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
            return redirect("comps:heat", first_entry.entry.heat.id)
        elif submit == "Delete":
            first_entry = unmatched_entries.first()
            # deleting the heat entry that this unmatched entry points to will also delete all the unmatched entries
            # that point to the same entry.
            first_entry.entry.delete()
            return redirect("comps:heat", first_entry.entry.heat.id)


def combine_heats(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    heats_in_comp = Heat.objects.filter(comp=comp).order_by('heat_number')
    current_heat_number = 0
    heats_to_display = list()
    for heat in heats_in_comp:
        if heat.info_prefix() != heat.info:
            if heat.heat_number != current_heat_number:
                current_heat_number = heat.heat_number
                print("Processing Heat", current_heat_number)
                possible_matches = list()
            for match in possible_matches:
                if heat.info_prefix() == match.info_prefix():
                    heats_to_display.append(match)
                    heats_to_display.append(heat)
                    if request.method == "GET":
                        print("Found ", heat.category, heat.heat_number, heat.info)
                        print("Match!", match.category, match.heat_number, match.info)
                        return render(request, 'comps/combine_heats.html', {'heats': (heat, match)})
                    else:  # POST
                        submit = request.POST.get("submit")
                        if submit == "Skip":
                            return redirect ('comps:heat', heat.id)
                        elif submit == "Submit":
                            heat.remove_info_prefix()
                            print("Combine", heat.category, heat.heat_number, heat.info)
                            heat.save()
                            matching_entries = HeatEntry.objects.filter(heat=match).order_by('shirt_number')
                            for e in matching_entries:
                                print(e.couple, e.code, e.shirt_number)
                                e.heat = heat
                                print(e.heat.info)
                                e.save()
                            match.delete()
                            return redirect ('comps:heat', heat.id)
            else:
                possible_matches.append(heat)

    return redirect ('comps:comp_heats', comp_id)


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
    else:
        comp.process_state = Comp.DANCER_NAMES_FORMATTED
        comp.save()

    return render(request, 'comps/dancers.html', {'comp': comp, 'page_obj': page_obj, 'current_name': current_name, 'possible_formats': possible_formats })


def load_dancers(request, comp_id):
    #comp = get_object_or_404(Comp, pk=comp_id)
    comp_objects = Comp.objects.filter(pk=comp_id)
    if len(comp_objects) == 1:
        comp=comp_objects[0]

    if HeatlistDancer.objects.count() > 0:
        heatlist_dancers = HeatlistDancer.objects.all().delete()

    if comp.heatsheet_file:
            heatlist = FileBasedHeatlist()
            heatlist.open(comp.heatsheet_file)
    else:
        if comp.url_data_format == Comp.COMP_MNGR:
            heatlist = CompMngrHeatlist()
        elif comp.url_data_format == Comp.NDCA_PREM:
            heatlist = NdcaPremHeatlist()
        else: # CompOrganizer for now
            heatlist = CompOrgHeatlist()

        heatlist.open(comp.heatsheet_url)

    for d in heatlist.dancers:
        in_database = HeatlistDancer.objects.filter(name = d.name)
        if in_database.count() == 0:
            d.save()

    comp.process_state = Comp.DANCERS_LOADED
    comp.save()

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
