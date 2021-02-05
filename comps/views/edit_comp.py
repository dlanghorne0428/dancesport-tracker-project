from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.forms import CompForm


def edit_comp(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    comp = get_object_or_404(Comp, pk=comp_id)

    if request.method == "GET":
        form = CompForm(instance=comp)
        return render(request, 'comps/edit_comp.html', {'form':form})
    else:
        submit = request.POST.get("submit")
        if submit == "Save":
            try:
                form = CompForm(request.POST, instance=comp)
                form.save()
                return redirect('comps:comp_detail', comp.id)
            except ValueError:
                return render(request, 'comps/edit_comp.html', {'form': form, 'error': "Invalid data submitted."})
        elif submit == "Cancel":
            return redirect('comps:comp_detail', comp.id)
        else:
            return redirect('comps:all_comps')
