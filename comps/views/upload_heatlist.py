from django.shortcuts import render, get_object_or_404
from comps.models.comp import Comp
import cloudinary

def upload_heatlist(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    comp = get_object_or_404(Comp, pk=comp_id)
    path = "media/comps/" + comp.title + "/heatlists.txt"
    public_id = comp.title + "_heatlists.txt"
    comp.heatlist_file = cloudinary.uploader.upload_resource(path, resource_type="raw", public_id=public_id)
    comp.save()
    return render(request, "comps/comp_detail.html", {'comp':comp, 'show_load_buttons': True})
