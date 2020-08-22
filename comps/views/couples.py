from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat_entry import Heat_Entry
from rankings.models import Dancer, Couple
from rankings.filters import DancerFilter

def couples(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    print(comp.process_state)
    if comp.process_state in [Comp.DANCERS_LOADED, Comp.DANCER_NAMES_FORMATTED, Comp.HEATS_LOADED]:
        return redirect ('comps:resolve_dancers', comp_id)
    else:
        couples = Couple.objects.filter(heat_entry__heat__comp=comp).distinct().order_by('dancer_1__name_last')
        paginator = Paginator(couples,16)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'comps/couples.html', {'comp': comp, 'page_obj': page_obj})
