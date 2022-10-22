from django.shortcuts import render, get_object_or_404
from comps.models.comp import Comp

def comp_detail(request, comp_id):
    # only show load dancer, load heat buttons for valid users
    show_load_buttons = False
    if request.user.is_authenticated:
        if request.user.is_superuser:
            show_load_buttons = True

    comp = get_object_or_404(Comp, pk=comp_id)
    
    show_load_time = False
    if comp.heatsheet_load_time is not None:
        if comp.heatsheet_load_time > Comp.default_time:
            show_load_time = True

    return render(request, "comps/comp_detail.html", {'comp':comp, 'show_load_buttons': show_load_buttons, 'show_load_time': show_load_time})
