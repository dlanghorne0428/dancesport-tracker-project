from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat
from rankings.models.couple import Couple
from comps.filters import HeatFilter


def couple_heats(request, comp_id, couple_id):
    # only show add button for valid users
    show_add_button = request.user.is_superuser

    comp = get_object_or_404(Comp, pk=comp_id)
    couple = get_object_or_404(Couple, pk=couple_id)

    heats = Heat.objects.filter(comp=comp).filter(heat_entry__couple=couple).distinct().order_by('time')
    paginator = Paginator(heats, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/couple_heats.html", {'comp': comp, 'page_obj': page_obj, 'couple': couple, 'show_add_button': show_add_button})
