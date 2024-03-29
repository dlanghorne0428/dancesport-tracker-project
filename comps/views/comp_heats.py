from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.filters import HeatFilter


def comp_heats(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    
    # only show elo column for valid users
    show_elo = request.user.is_superuser
    
    f = HeatFilter(request.GET, queryset=Heat.objects.filter(comp=comp).order_by('time', 'heat_number', 'info'))
    paginator = Paginator(f.qs, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/comp_heats.html", {'comp': comp, 'page_obj': page_obj, 'show_elo': show_elo, 'filter': f})
