from django.shortcuts import render, redirect
from comps.models.comp import Comp
from comps.forms import CompForm


def createcomp(request):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    if request.method == "GET":
        return render(request, 'comps/createcomp.html', {'form':CompForm()})
    else:
        try:
            form = CompForm(request.POST)
            form.save()
            return redirect('all_comps')
        except ValueError:
            return render(request, 'comps/createcomp.html', {'form':CompForm(), 'error': "Invalid data submitted."})
