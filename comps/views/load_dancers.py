from django.shortcuts import render, redirect
from comps.models import Comp, HeatlistDancer, UnmatchedHeatEntry
from comps.heatlist.file_based_heatlist import FileBasedHeatlist
from comps.heatlist.comp_mngr_heatlist import CompMngrHeatlist
from comps.heatlist.comp_organizer_heatlist import CompOrgHeatlist
from comps.heatlist.ndca_prem_heatlist import NdcaPremHeatlist


def load_dancers(request, comp_id):
    #comp = get_object_or_404(Comp, pk=comp_id)
    comp_objects = Comp.objects.filter(pk=comp_id)
    if len(comp_objects) == 1:
        comp=comp_objects[0]

    if HeatlistDancer.objects.count() > 0:
        HeatlistDancer.objects.all().delete()

    if UnmatchedHeatEntry.objects.count() > 0:
        UnmatchedHeatEntry.objects.all().delete()

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
