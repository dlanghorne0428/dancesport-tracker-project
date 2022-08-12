from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from rankings.couple_matching import split_name
from rankings.models.couple import Couple
from rankings.models.dancer import Dancer
from rankings.forms import DancerForm
from rankings.filters import DancerFilter
from rankings.models import EloRating

################################################
# CRUD Views for Dancer objects
# C:  create_dancer
# R:  all_dancers and view_dancer
# UD: edit_dancer
################################################

def create_dancer(request, name_str=None, comp_pk=None):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    if request.method == "GET":
        if name_str is None:
            return render(request, 'rankings/create_dancer.html', {'form':DancerForm()})
        else:
            name_last, name_first, name_middle = split_name(name_str)
            data = {
                'name_last': name_last,
                'name_first': name_first,
                'name_middle': name_middle
            }
            f = DancerForm(data)
            return render(request, 'rankings/create_dancer.html', {'form':f})
    else:
        try:
            form = DancerForm(request.POST)
            dancer_instance = form.save()
            if comp_pk is None:
                return redirect('view_dancer', dancer_instance.id)
            else:
                return redirect('comps:resolve_mismatches', comp_pk)
        except ValueError:
            return render(request, 'rankings/create_dancer.html', {'form':DancerForm(), 'error': "Invalid data submitted."})


def all_dancers(request):
    # only show add and edit buttons for valid users
    show_admin_buttons = request.user.is_superuser

    f = DancerFilter(request.GET, queryset=Dancer.objects.all())
    paginator = Paginator(f.qs, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/all_dancers.html', {'page_obj': page_obj, 'filter': f, 'show_admin_buttons': show_admin_buttons})


def view_dancer(request, dancer_pk):
    # only show add and edit buttons for valid users
    show_admin_buttons = request.user.is_superuser
    all_comps = Comp.objects.all().order_by('-start_date')
    comps_with_mismatches = list()
    for comp in all_comps:
        if comp.process_state in [Comp.HEATS_LOADED, Comp.SCORESHEETS_LOADED]:
            comps_with_mismatches.append(comp)

    dancer = get_object_or_404(Dancer, pk=dancer_pk)

    couples = Couple.objects.filter(Q(dancer_1=dancer) | Q(dancer_2=dancer)).order_by('dancer_1', 'dancer_2')
    partnerships = list()
    for c in couples:
        ratings = EloRating.objects.filter(couple=c).order_by('-value')
        if len(ratings) > 0:
            partnership = {'couple': c, 'rating': ratings[0]}
        else:
            partnership = {'couple': c}
        partnerships.append(partnership)
    return render(request, 'rankings/view_dancer.html', {'dancer': dancer, 'partnerships': partnerships,
                                                         'comps_with_mismatches': comps_with_mismatches, 'show_admin_buttons': show_admin_buttons})


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
                return redirect('view_dancer', dancer.id)
            except ValueError:
                return render(request, 'rankings/edit_dancer.html', {'dancer': dancer, 'form': form, 'error': "Invalid data submitted."})
        elif submit == "Delete Dancer":
            print("Deleting " +  str(dancer))
            dancer.delete()
            return redirect ('all_dancers')
