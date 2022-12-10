from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat_entry import Heat_Entry
from comps.models.heatlist_dancer import Heatlist_Dancer
from rankings.couple_matching import split_name
from rankings.models import Dancer


def alias_dancers(request, level=2):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    
    no_comp_list = Heatlist_Dancer.objects.filter(comp=None)
    if len(no_comp_list) > 0:
        print("Removing " + len(no_comp_list) + 'entries')
        for d in no_comp_list:
            d.delete()

    alias_dancers = Heatlist_Dancer.objects.exclude(alias__isnull=True).order_by('name', 'comp__start_date')
    if level == 2:
        doubles = list()
        for i in range(1, len(alias_dancers)):
            if alias_dancers[i-1].name == alias_dancers[i].name and alias_dancers[i-1].alias == alias_dancers[i].alias:
                doubles.append(alias_dancers[i])
        paginator = Paginator(doubles, 16)
    else:
        paginator = Paginator(alias_dancers, 16)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/alias_dancers.html', {'page_obj': page_obj, 'level': level })


def aliases_for_dancer(request, hld_pk):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    # get the heatlist dancer and the dancer by alias
    heatlist_dancer = get_object_or_404(Heatlist_Dancer, pk=hld_pk)
    dancer = get_object_or_404(Dancer, pk=heatlist_dancer.alias.id)
    dancer_aliases = Heatlist_Dancer.objects.filter(alias=heatlist_dancer.alias)

    all_comps = Comp.objects.all().order_by('-start_date')
    comps_for_dancer = list()
    for comp in all_comps:
        # if dancer's name has been corrected after this comp's start date, quit loop
        if comp.start_date < dancer.name_fix_date:
            break
        # if the dancer was in this comp
        if Heat_Entry.objects.filter(heat__comp=comp).filter(Q(couple__dancer_1=dancer) | Q(couple__dancer_2=dancer)).count() > 0:
            # and had an alias in that comp
            matches = dancer_aliases.filter(comp=comp)
            # add the alias to the list
            if matches.count() > 0:
                comps_for_dancer.append(matches.first())
            else: # add a "no name alias" to the list
                no_name_hld = Heatlist_Dancer()
                no_name_hld.name = ""
                no_name_hld.code = "No Code"
                no_name_hld.alias = dancer
                no_name_hld.comp = comp
                comps_for_dancer.append(no_name_hld)

    paginator = Paginator(comps_for_dancer, 16)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/alias_dancers.html', {'page_obj': page_obj, 'level': 1 })


def accept_alias(request, hld_pk):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    # get the heatlist dancer and format the new name
    heatlist_dancer = get_object_or_404(Heatlist_Dancer, pk=hld_pk)
    name_last, name_first, name_middle = split_name(heatlist_dancer.name)

    # get the dancer object referenced by alias
    dancer = heatlist_dancer.alias
    dancer.name_last = name_last
    dancer.name_first = name_first
    dancer.name_middle = name_middle
    dancer.name_fix_date = heatlist_dancer.comp.start_date
    dancer.save()

    # now that dancer object has been updated with a new name, delete these aliases
    aliases_to_remove = Heatlist_Dancer.objects.filter(name=heatlist_dancer.name).filter(alias=heatlist_dancer.alias)
    for a in aliases_to_remove:
        hld_object = a
        hld_object.delete()

    return redirect('view_dancer', dancer.id)


def reject_alias(request, hld_pk):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    # get the heatlist dancer whose alias has been rejected
    heatlist_dancer = get_object_or_404(Heatlist_Dancer, pk=hld_pk)

    # get the dancer object referenced by alias
    dancer = heatlist_dancer.alias
    dancer.name_fix_date = heatlist_dancer.comp.start_date
    dancer.save()

    # remove all matching heatlist_dancer objects
    aliases_to_remove = Heatlist_Dancer.objects.filter(name=heatlist_dancer.name).filter(alias=heatlist_dancer.alias)
    for a in aliases_to_remove:
        hld_object = a
        hld_object.delete()

    return redirect('alias_dancers', 2)
