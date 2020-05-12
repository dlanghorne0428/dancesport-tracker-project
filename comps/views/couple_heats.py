from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from comps.models import Comp, Heat
from rankings.models import Couple
from comps.filters import HeatFilter


def couple_heats(request, comp_id, couple_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    couple = get_object_or_404(Couple, pk=couple_id)

    heats = Heat.objects.filter(comp=comp).filter(heatentry__couple=couple).distinct().order_by('time')
    paginator = Paginator(heats, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/couple_heats.html", {'comp': comp, 'page_obj': page_obj, 'couple': couple})
