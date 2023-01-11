from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.comp_couple import Comp_Couple
from comps.models.heat_entry import Heat_Entry
from comps.models.heatlist_dancer import Heatlist_Dancer
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
        
        # create form to rename last year's comp
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
            
            # remove heatlist_dancer objects from last year's comp
            last_year_dancers = Heatlist_Dancer.objects.filter(comp=comp)
            print("Deleting " + str(len(last_year_dancers)) + " alias dancers from last year comp.")
            for d in last_year_dancers:
                d.delete()
                
            # remove comp_couples with no heats from last year's comp
            couples = Comp_Couple.objects.filter(comp=comp).order_by('couple')
            count = 0
            for c in couples:
                num_heats = Heat_Entry.objects.filter(heat__comp=comp, couple=c.couple).count()
                if num_heats == 0:
                    count += 1
                    c.delete()
            print(str(count) + " couples with no heats deleted from last year's comp.")
                    
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