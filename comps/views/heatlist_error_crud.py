from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heatlist_error import Heatlist_Error


def delete_heatlist_error(request, error_id):
    heatlist_error = get_object_or_404(Heatlist_Error, pk=error_id)
    comp = heatlist_error.comp
    heatlist_error.delete()
    return redirect("comps:show_heatlist_errors", comp.id)


def show_heatlist_errors(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    heatlist_errors = Heatlist_Error.objects.filter(comp=comp).order_by('error', 'dancer', 'heat__heat_number')
    paginator = Paginator(heatlist_errors, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/show_heatlist_errors.html", {'comp': comp, 'page_obj': page_obj, })
