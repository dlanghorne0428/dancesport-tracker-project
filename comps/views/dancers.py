from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.comp_couple import Comp_Couple
from comps.models.heat_entry import Heat_Entry
from rankings.models import Dancer
from rankings.filters import DancerFilter

def dancers(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    if comp.process_state in [Comp.DANCERS_LOADED, Comp.DANCER_NAMES_FORMATTED, Comp.HEATS_LOADED]:
        return redirect ('comps:resolve_dancers', comp_id)
    else:
        comp_couples = Comp_Couple.objects.filter(comp=comp)
        if len(comp_couples) == 0:
            dancers = Dancer.objects.filter(Q(follower_or_instructor__heat_entry__heat__comp=comp) | Q(leader_or_student__heat_entry__heat__comp=comp)).distinct().order_by('name_last')
        else:
            dancers = Dancer.objects.filter(Q(follower_or_instructor__comp_couple__comp=comp) | Q(leader_or_student__comp_couple__comp=comp)).distinct().order_by('name_last')

        f = DancerFilter(request.GET, queryset=dancers)
        paginator = Paginator(f.qs, 16)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'comps/dancers.html', {'comp': comp, 'page_obj': page_obj, 'filter': f})
