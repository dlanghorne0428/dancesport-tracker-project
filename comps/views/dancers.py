from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from comps.models import Comp, HeatEntry
from rankings.models import Dancer


def dancers(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    print(comp.process_state)
    if comp.process_state in [Comp.DANCERS_LOADED, Comp.DANCER_NAMES_FORMATTED, Comp.HEATS_LOADED]:
        return redirect ('comps:resolve_dancers', comp_id)
    else:
        dancers = Dancer.objects.filter(Q(follower_or_instructor__heatentry__heat__comp=comp) | Q(leader_or_student__heatentry__heat__comp=comp)).distinct().order_by('name_last')
        paginator = Paginator(dancers, 16)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'comps/dancers.html', {'comp': comp, 'page_obj': page_obj})
