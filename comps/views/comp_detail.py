from django.shortcuts import render, get_object_or_404
from comps.models.comp import Comp

def comp_detail(request, comp_id):
    # only show load dancer, load heat buttons for valid users
    print(comp_id)
    show_load_buttons = False
    print(show_load_buttons)
    if request.user.is_authenticated:
        if request.user.is_superuser:
            show_load_buttons = True
            print(show_load_buttons)

    comp = get_object_or_404(Comp, pk=comp_id)
    print(comp.id)
    
    show_load_time = False
    print(show_load_time)
    if comp.heatsheet_load_time is not None:
        if comp.heatsheet_load_time > Comp.default_time:
            show_load_time = True
            print(show_load_time)

    return render(request, "rankings/edit_comp.html", comp.id)
    #return render(request, "comps/comp_detail.html", {'comp':comp, 'show_load_buttons': show_load_buttons, 'show_load_time': show_load_time})
