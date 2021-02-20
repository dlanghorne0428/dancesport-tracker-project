from django.shortcuts import render, redirect
from comps.models.comp import Comp
from comps.models.heatlist_dancer import Heatlist_Dancer
from comps.models.unmatched_heat_entry import Unmatched_Heat_Entry
from comps.heatlist.file_based_heatlist import FileBasedHeatlist
from comps.heatlist.comp_mngr_heatlist import CompMngrHeatlist
from comps.heatlist.comp_organizer_heatlist import CompOrgHeatlist
from comps.heatlist.ndca_prem_heatlist import NdcaPremHeatlist
from comps.heatlist.o2cm_heatlist import O2cmHeatlist


def load_dancers(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    comp_objects = Comp.objects.filter(pk=comp_id)
    if len(comp_objects) == 1:
        comp=comp_objects[0]

    if Heatlist_Dancer.objects.count() > 0:
        Heatlist_Dancer.objects.all().delete()

    if Unmatched_Heat_Entry.objects.count() > 0:
        Unmatched_Heat_Entry.objects.all().delete()

    if comp.heatsheet_file:
            heatlist = FileBasedHeatlist()
            heatlist.open(comp.heatsheet_file)
    else:
        if comp.url_data_format == Comp.COMP_MNGR:
            heatlist = CompMngrHeatlist()
        elif comp.url_data_format == Comp.NDCA_PREM:
            heatlist = NdcaPremHeatlist()
        elif comp.url_data_format == Comp.O2CM:
            heatlist = O2cmHeatlist()
        else: # CompOrganizer for now
            heatlist = CompOrgHeatlist()

        heatlist.open(comp.heatsheet_url)

    for d in heatlist.dancers:
        in_database = Heatlist_Dancer.objects.filter(name = d.name)
        if in_database.count() == 0:
            d.save()

    comp.process_state = Comp.DANCERS_LOADED
    comp.save()

    return redirect("comps:resolve_dancers", comp.id)
