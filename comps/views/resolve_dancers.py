from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.heatlist_dancer import Heatlist_Dancer


def resolve_dancers(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    comp = get_object_or_404(Comp, pk=comp_id)
    names_to_format = Heatlist_Dancer.objects.filter(formatting_needed = True)
    current_name = names_to_format.first()

    if request.method == "POST":
        submit = request.POST.get("submit")
        # determine what page to show
        heatlist_dancers = Heatlist_Dancer.objects.all().order_by('pk')
        for index in range(len(heatlist_dancers)):
            if current_name.name == heatlist_dancers[index].name:
                page_number = index // 16 + 1
                print("Page Number is", page_number)
                break
        if submit == "Delete":
            current_name.formatting_needed = False
            current_name.save()
        elif submit == "Submit":
            new_name = request.POST.get("spelling")
            current_name.name = new_name
            current_name.formatting_needed = False
            print(current_name.name)
            current_name.save()

        # find next name to format
        names_to_format = Heatlist_Dancer.objects.filter(formatting_needed = True)
        current_name = names_to_format.first()
    else: # GET
        page_number = request.GET.get('page')

    # do this for either GET or POST
    heatlist_dancers = Heatlist_Dancer.objects.all().order_by('pk')
    paginator = Paginator(heatlist_dancers, 16)
    page_obj = paginator.get_page(page_number)

    possible_formats = list()
    if current_name is not None:
        fields = current_name.name.split()
        for field in range(1, len(fields)):
            possible_formats.append(current_name.format_name(current_name.name, simple=False, split_on=field))
    else:
        comp.process_state = Comp.DANCER_NAMES_FORMATTED
        comp.save()

    return render(request, 'comps/resolve_dancers.html', {'comp': comp, 'page_obj': page_obj, 'current_name': current_name, 'possible_formats': possible_formats })
