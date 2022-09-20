from django.shortcuts import redirect, render, get_object_or_404

from comps.models.comp import Comp
from comps.tasks import update_elo_ratings_for_comps
                

def update_elo_ratings(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')    
    
    comp = get_object_or_404(Comp, pk=comp_id)
    if comp.process_state != Comp.RESULTS_RESOLVED:
        return redirect("comps:comp_detail", comp_id)
    
    comp_list = list()
    comp_list.append(comp_id)
    
    result = update_elo_ratings_for_comps.delay(comp_list)
    
    return render(request, 'comps/update_elo_ratings.html', context={'task_id': result.task_id, 'comp': comp})
    