from django.shortcuts import redirect, render, get_object_or_404

from comps.models.comp import Comp
from comps.tasks import update_elo_ratings_for_comps
from rankings.models.elo_rating import EloRating

def recalc_elo_ratings(request):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html') 
    
    comp_list = list()
    comps = Comp.objects.all().order_by('start_date')
    for c in comps:
        if c.process_state in [Comp.RESULTS_RESOLVED, Comp.ELO_RATINGS_UPDATED, Comp.COMPLETE]:
            comp_list.append(c.id)
            
    result = update_elo_ratings_for_comps.delay(comp_list)
    
    return render(request, 'comps/update_elo_ratings.html', context={'task_id': result.task_id })