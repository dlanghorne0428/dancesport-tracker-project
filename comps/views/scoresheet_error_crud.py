from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.result_error import Result_Error


def delete_scoresheet_error(request, error_id):
    scoresheet_error = get_object_or_404(Result_Error, pk=error_id)
    comp = scoresheet_error.comp
    scoresheet_error.delete()
    return redirect("comps:show_scoresheet_errors", comp.id)


def show_scoresheet_errors(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    scoresheet_errors = Result_Error.objects.filter(comp=comp).order_by('heat')
    paginator = Paginator(scoresheet_errors, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/show_scoresheet_errors.html", {'comp': comp, 'page_obj': page_obj, })
