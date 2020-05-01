from django.shortcuts import render, get_object_or_404
from comps.models import Comp

def comp_detail(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    return render(request, "comps/comp_detail.html", {'comp':comp})
