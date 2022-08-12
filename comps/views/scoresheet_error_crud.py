from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from comps.models.result_error import Result_Error


def delete_scoresheet_error(request, error_id):
    scoresheet_error = get_object_or_404(Result_Error, pk=error_id)
    comp = scoresheet_error.comp
    scoresheet_error.delete()
    return redirect("comps:show_scoresheet_errors", comp.id)


def repair_scoresheet_error(request, error_id):
    scoresheet_error = get_object_or_404(Result_Error, pk=error_id)
    if scoresheet_error.error == Result_Error.NO_COUPLE_RESULT:
        heat_entry = Heat_Entry.objects.filter(heat=scoresheet_error.heat).filter(couple=scoresheet_error.couple)
        if heat_entry is not None:
            heat_entry.delete()
    elif scoresheet_error.error == Result_Error.NO_ENTRIES_FOUND:
        heat = scoresheet_error.heat
        if heat is not None:
            heat.delete()
    elif scoresheet_error.error == Result_Error.UNKNOWN_ELO_VALUE:
        heat = scoresheet_error.heat
        if heat.initial_elo_value is None:
            return redirect("comps:heat", heat.id)

    comp = scoresheet_error.comp
    scoresheet_error.delete()
    return redirect("comps:show_scoresheet_errors", comp.id)


def show_scoresheet_errors(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    scoresheet_errors = Result_Error.objects.filter(comp=comp).order_by('heat__time')
    paginator = Paginator(scoresheet_errors, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/show_scoresheet_errors.html", {'comp': comp, 'page_obj': page_obj, })
