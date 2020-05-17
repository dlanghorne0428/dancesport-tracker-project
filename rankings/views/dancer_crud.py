from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from rankings.models import Dancer, Couple
from rankings.forms import DancerForm
from rankings.filters import DancerFilter

################################################
# CRUD Views for Dancer objects
# C:  create_dancer
# R:  all_dancers and view_dancer
# UD: edit_dancer
################################################

def create_dancer(request):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    if request.method == "GET":
        return render(request, 'rankings/create_dancer.html', {'form':DancerForm()})
    else:
        try:
            form = DancerForm(request.POST)
            form.save()
            return redirect('all_dancers')
        except ValueError:
            return render(request, 'rankings/create_dancer.html', {'form':DancerForm(), 'error': "Invalid data submitted."})


def all_dancers(request):
    f = DancerFilter(request.GET, queryset=Dancer.objects.order_by('name_last'))
    paginator = Paginator(f.qs, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/all_dancers.html', {'page_obj': page_obj, 'filter': f})


def view_dancer(request, dancer_pk):
    dancer = get_object_or_404(Dancer, pk=dancer_pk)
    couples = Couple.objects.filter(Q(dancer_1=dancer) | Q(dancer_2=dancer)).order_by('dancer_1')
    return render(request, 'rankings/view_dancer.html', {'dancer': dancer, 'couples': couples})


def edit_dancer(request, dancer_pk):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    dancer = get_object_or_404(Dancer, pk=dancer_pk)
    if request.method == "GET":
        form = DancerForm(instance=dancer)
        return render(request, 'rankings/edit_dancer.html', {'dancer': dancer, 'form': form})
    else:
        submit = request.POST.get("submit")
        if submit == "Save":
            try:
                form = DancerForm(request.POST, instance=dancer)
                form.save()
                return redirect('all_dancers')
            except ValueError:
                return render(request, 'rankings/edit_dancer.html', {'dancer': dancer, 'form': form, 'error': "Invalid data submitted."})
        elif submit == "Delete Dancer":
            print("Deleting", str(dancer))
            dancer.delete()
            return redirect ('all_dancers')
