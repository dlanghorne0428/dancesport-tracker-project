from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from comps.models.heatlist_dancer import Heatlist_Dancer
from rankings.couple_matching import split_name
from rankings.models import Dancer


def alias_dancers(request, level=2):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    alias_dancers = Heatlist_Dancer.objects.exclude(alias__isnull=True).order_by('name')
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

    # remove all matching heatlist_dancer objects
    aliases_to_remove = Heatlist_Dancer.objects.filter(name=heatlist_dancer.name).filter(alias=heatlist_dancer.alias)
    for a in aliases_to_remove:
        hld_object = a
        hld_object.delete()

    return redirect('alias_dancers', 2)
