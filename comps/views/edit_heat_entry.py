from django.shortcuts import render, redirect, get_object_or_404
from comps.models import Comp, Heat, HeatEntry
from comps.forms import HeatEntryForm


def edit_heat_entry(request, entry_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
        
    entry = get_object_or_404(HeatEntry, pk=entry_id)
    if request.method == "GET":
        form = HeatEntryForm(instance=entry)
        return render(request, 'comps/edit_heat_entry.html', {'entry': entry, 'form':form})
    else:
        try:
            form = HeatEntryForm(request.POST, instance=entry)
            form.save()
            return redirect('comps:heat', entry.heat.id)
        except ValueError:
            return render(request, 'comps/edit_heat_entry.html', {'form':form, 'error': "Invalid data submitted."})
