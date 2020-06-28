from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from rankings.models import Couple
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from rankings.forms import CoupleForm

################################################
# CRUD Views for Couple objects
# C:  create_couple
# R:  all_couples and view_couples
# UD: edit_couple and combine_couples
################################################

def create_couple(request):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    if request.method == "GET":
        return render(request, 'rankings/create_couple.html', {'form':CoupleForm()})
    else:
        try:
            form = CoupleForm(request.POST)
            form.save()
            return redirect('all_couples')
        except ValueError:
            return render(request, 'rankings/create_couple.html', {'form':CoupleForm(), 'error': "Invalid data submitted."})


def all_couples(request):
    # only show add button for valid users
    show_admin_buttons = request.user.is_superuser

    couples = Couple.objects.order_by("dancer_1__name_last")
    paginator = Paginator(couples, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/all_couples.html', {'page_obj': page_obj, 'show_admin_buttons': show_admin_buttons})


def view_couple(request, couple_pk):
    # only show edit button for valid users
    show_admin_buttons = request.user.is_superuser

    couple = get_object_or_404(Couple, pk=couple_pk)
    all_comps = Comp.objects.all().order_by('-start_date')
    comps_for_couple = list()
    for comp in all_comps:
        if Heat_Entry.objects.filter(heat__comp=comp).filter(couple=couple).count() > 0:
            comps_for_couple.append(comp)
    return render(request, 'rankings/view_couple.html', {'couple': couple, 'comps_for_couple': comps_for_couple, 'show_admin_buttons': show_admin_buttons})


def combine_couples(request, couple_pk, couple2_pk):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    couple = get_object_or_404(Couple, pk=couple_pk)
    couple2 = get_object_or_404(Couple, pk=couple2_pk)
    couple2_heat_entries = Heat_Entry.objects.filter(couple=couple2)
    for entry in couple2_heat_entries:
        entry.couple = couple
        entry.save()
    return redirect('view_couple', couple_pk)


def edit_couple(request, couple_pk):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    couple = get_object_or_404(Couple, pk=couple_pk)
    if request.method == "GET":
        form = CoupleForm(instance=couple)
        return render(request, 'rankings/edit_couple.html', {'couple': couple, 'form': form})
    else:
        submit = request.POST.get("submit")
        if submit == "Save":
            try:
                form = CoupleForm(request.POST, instance=couple)
                form.save()
                return redirect('all_couples')
            except ValueError:
                return render(request, 'rankings/view_couple.html', {'couple': couple, 'form': form, 'error': "Invalid data submitted."})
        elif submit == "Delete Couple":
            print("Deleting", str(couple))
            couple.delete()
            return redirect ('all_couples')
