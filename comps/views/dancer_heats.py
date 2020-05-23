from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat
from rankings.models import Dancer
from comps.filters import HeatFilter


def dancer_heats(request, comp_id, dancer_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    dancer = get_object_or_404(Dancer, pk=dancer_id)

    heats = Heat.objects.filter(comp=comp).filter(Q(heat_entry__couple__dancer_1=dancer) | Q(heat_entry__couple__dancer_2=dancer)).distinct().order_by('time')
    paginator = Paginator(heats, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/dancer_heats.html", {'comp': comp, 'page_obj': page_obj, 'dancer': dancer})
