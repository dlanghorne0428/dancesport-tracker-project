from django.shortcuts import redirect, render, get_object_or_404

from comps.models.comp import Comp
from comps.tasks import update_elo_ratings_for_comps

def recalc_elo_ratings(request):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html') 
    
    comps = Comp.objects.all().order_by('start_date')
    for c in comps:
        if c.process_state != Comp.RESULTS_RESOLVED:
            print("Incorrect state " + str(c))
        #else
            update_elo_ratings_for_comps(c)
            
    return redirect('comps:all_comps')