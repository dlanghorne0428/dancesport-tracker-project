from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from rankings.models.couple import Couple
from rankings.models.dancer import Dancer
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from rankings.forms import CoupleForm, CoupleTypeForm
from rankings.rating_stats import couple_stats

################################################
# CRUD Views for Couple objects
# C:  create_couple
# R:  all_couples and view_couples
# U: edit_couple and combine_couples
# D: delete_couple
################################################

def create_couple(request, couple_type = None, dancer_pk=None, dancer_position= None, partner_pk=None):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    if request.method == "GET":
        if dancer_position is None:
            f = CoupleForm()
        elif partner_pk is None:
            #print("partner id is None")
            dancer = get_object_or_404(Dancer, pk=dancer_pk)
            f = CoupleForm(couple_type=couple_type, dancer_position= dancer_position, dancer_id = dancer_pk, dancer_type = dancer.dancer_type)
        else:
            #print("Partner ID: " + str(partner_pk))
            dancer = get_object_or_404(Dancer, pk=dancer_pk)
            partner = get_object_or_404(Dancer, pk=partner_pk)
            f = CoupleForm(couple_type=couple_type, dancer_position= dancer_position, dancer_id = dancer_pk, dancer_type = dancer.dancer_type, partner_id = partner_pk)

        return render(request, 'rankings/create_couple.html', {'form':f})
    else:
        try:
            form = CoupleForm(data=request.POST)
            couple_instance = form.save()
            return redirect('view_dancer', couple_instance.dancer_1.id)
        except ValueError:
            return render(request, 'rankings/create_couple.html', {'form':CoupleForm(), 'error': "Invalid data submitted."})


def all_couples(request):
    # only show add button for valid users
    show_admin_buttons = request.user.is_superuser

    couples = Couple.objects.order_by("dancer_1")
    paginator = Paginator(couples, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/all_couples.html', {'page_obj': page_obj, 'show_admin_buttons': show_admin_buttons})


def view_couple(request, couple_pk):
    # only show edit button for valid users
    show_admin_buttons = request.user.is_superuser

    couple = get_object_or_404(Couple, pk=couple_pk)
    all_comps = Comp.objects.all().order_by('-start_date')
    stats = couple_stats(couple)
    comps_for_couple = list()
    comps_with_mismatches = list()
    for comp in all_comps:
        if Heat_Entry.objects.filter(heat__comp=comp).filter(couple=couple).count() > 0:
            comps_for_couple.append(comp)
        if comp.process_state in [Comp.HEATS_LOADED, Comp.SCORESHEETS_LOADED]:
            comps_with_mismatches.append(comp)
    return render(request, 'rankings/view_couple.html', {'couple': couple, 'comps_for_couple': comps_for_couple, 'rating': stats['rating'],
                                                         'comps_with_mismatches': comps_with_mismatches,'show_admin_buttons': show_admin_buttons})


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


def flip_couple(request, couple_pk):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    couple = get_object_or_404(Couple, pk=couple_pk)
    temp = couple.dancer_1
    couple.dancer_1 = couple.dancer_2
    couple.dancer_2 = temp
    print(couple)
    couple.save()
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
                form = CoupleForm(data=request.POST, instance=couple)
                form.save()
                return redirect('view_couple', couple_pk)
                #return redirect('all_couples')
            except ValueError:
                return render(request, 'rankings/view_couple.html', {'couple': couple, 'form': form, 'error': "Invalid data submitted."})
        elif submit == "Delete Couple":
            print("Deleting " + str(couple))
            couple.delete()
            return redirect ('all_couples')


def change_couple_type(request, couple_pk):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    couple = get_object_or_404(Couple, pk=couple_pk)
    if request.method == "GET":
        form = CoupleTypeForm(instance=couple)
        return render(request, 'rankings/change_couple_type.html', {'couple': couple, 'form': form})
    else:
        submit = request.POST.get("submit")
        try:
            form = CoupleTypeForm(data=request.POST, instance=couple)
            form.save()
            return redirect('view_couple', couple_pk)
            #return redirect('all_couples')
        except ValueError:
            return render(request, 'rankings/change_couple_type.html', {'couple': couple, 'form': form, 'error': "Invalid data submitted."})


def delete_couple(request, couple_pk):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    couple = get_object_or_404(Couple, pk=couple_pk)
    couple.delete()
    return redirect ('all_couples')
