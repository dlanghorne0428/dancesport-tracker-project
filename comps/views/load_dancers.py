from django.core import serializers
from django.shortcuts import render, redirect
from comps.models.comp import Comp
from comps.models.heatlist_dancer import Heatlist_Dancer
from comps.models.unmatched_heat_entry import Unmatched_Heat_Entry
from comps.heatlist.file_based_heatlist import FileBasedHeatlist
from comps.heatlist.comp_mngr_heatlist import CompMngrHeatlist
from comps.heatlist.comp_organizer_heatlist import CompOrgHeatlist
from comps.heatlist.dance_comp_heatlist import DanceCompHeatlist
from comps.heatlist.ndca_prem_feed_heatlist import NdcaPremFeedHeatlist
from comps.heatlist.o2cm_heatlist import O2cmHeatlist
from comps.tasks import process_dancers_task


def load_dancers(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    comp_objects = Comp.objects.filter(pk=comp_id)
    if len(comp_objects) == 1:
        comp=comp_objects[0]

    #if Heatlist_Dancer.objects.count() > 0:
    #    Heatlist_Dancer.objects.all().delete()

    if Unmatched_Heat_Entry.objects.count() > 0:
        Unmatched_Heat_Entry.objects.all().delete()

    if comp.heatsheet_file:
            heatlist = FileBasedHeatlist()
            heatlist.open(comp)
    else:
        if comp.url_data_format == Comp.COMP_MNGR:
            heatlist = CompMngrHeatlist()
        elif comp.url_data_format == Comp.DANCE_COMP:
            heatlist = DanceCompHeatlist()
        elif comp.url_data_format == Comp.NDCA_FEED:
            heatlist = NdcaPremFeedHeatlist()
        elif comp.url_data_format == Comp.O2CM:
            heatlist = O2cmHeatlist()
        else: # CompOrganizer for now
            heatlist = CompOrgHeatlist()

        heatlist.open(comp)

        # add special "dancer" for partnerless events
        d = Heatlist_Dancer()
        d.name = "{No, Partner}"
        d.code = "0"
        d.comp = comp
        heatlist.dancers.append(d)

    comp_data = serializers.serialize("json", comp_objects)
    heatlist_dancer_data = serializers.serialize("json", heatlist.dancers)
    
    result = process_dancers_task.delay(comp_data, heatlist_dancer_data)
    return render(request, 'comps/process_dancers.html', context={'task_id': result.task_id, 'comp': comp})
