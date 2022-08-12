from django.shortcuts import render, redirect, get_object_or_404
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from comps.models.heatlist_error import Heatlist_Error
from comps.models.result_error import Result_Error
from comps.forms import HeatForm


def edit_heat(request, heat_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    heat = get_object_or_404(Heat, pk=heat_id)
    
    error = None
    errors = Heatlist_Error.objects.filter(heat=heat_id)
    if len(errors) > 0:
        heat_error = errors.first()
        error = heat_error
    else:
        heat_error = None
        errors = Result_Error.objects.filter(heat=heat_id)
        if len(errors) > 0:
            result_error = errors.first()
            error = result_error
        else:
            result_error = None
            
    comp_id = heat.comp_id
    if request.method == "GET":
        form = HeatForm(instance=heat)
        return render(request, 'comps/edit_heat.html', {'heat': heat, 'error': error, 'form': form})
    else: # POST
        submit = request.POST.get("submit")
        if submit == "Save":
            form = HeatForm(request.POST, instance=heat)
            try:
                form.save()
                if heat_error is not None:
                    return redirect('comps:check_heatlist_error', heat_error.id)
                elif result_error is not None:
                    return redirect('comps:repair_scoresheet_error', result_error.id)
                else:
                    return redirect('comps:heat', heat_id)
            except ValueError:
                return render(request, 'comps/edit_heat.html', {'heat': heat, 'heat_error': error, 'form': form, 'form_error': "Invalid data submitted."})
            
        elif submit == "Delete Heat":
            print("Deleting " + str(heat) + " " + heat.info)
            heat.delete()
            return redirect ('comps:comp_heats', comp_id)
