from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.forms import CompForm, CompTitleForm


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


def this_year_comp(request, comp_id):
    from datetime import date, timedelta
    
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    comp = get_object_or_404(Comp, pk=comp_id)
    current_title = comp.title

    if request.method == "GET":
        current_year = date.today().year
        
        # create fom to rename last year's comp
        comp.title = current_title + ' - ' + str(current_year - 1)
        form = CompTitleForm(instance=comp)
        return render(request, 'comps/edit_comp.html', {'form':form, 'custom_title': 'Edit Competition Title for Previous Year'})
    else:
        submit = request.POST.get("submit")
        if submit == "Save":
            try:
                form = CompTitleForm(request.POST, instance=comp)
                form.save()
            except ValueError:
                return render(request, 'comps/edit_comp.html', {'form': form, 'custom_title': 'Edit Competition Title for Previous Year', 'error': "Invalid data submitted."})
                                
            # create future comp with specific fields from current comp
            future_comp = Comp()
            future_comp.title = current_title
            future_comp.location = comp.location
            future_comp.start_date = comp.start_date + timedelta(days=364)
            future_comp.end_date = comp.end_date + timedelta(days=364)       
            future_comp.logo = comp.logo
            future_comp.url_data_format = comp.url_data_format
            future_comp.save()
            return redirect('comps:edit_comp', future_comp.id)  
                        
        elif submit == "Cancel":
            return redirect('comps:comp_detail', comp.id)
        else:
            return redirect('comps:all_comps')