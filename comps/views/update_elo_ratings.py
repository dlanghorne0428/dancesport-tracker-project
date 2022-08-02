from django.shortcuts import redirect, render, get_object_or_404

from multielo import MultiElo
import numpy

from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from rankings.models.elo_rating import EloRating

def initial_elo_rating(category, info):
    if category == "PH":
        return 1500
    info_up = info.upper()
    if 'GOLD' in info_up:
        return 1500
    if 'SILVER' in info_up:
        return 1000
    if 'BRONZE' in info_up or 'NEWCOMER' in info_up or 'NOVICE' in info_up:
        return 500
    if 'PRE-CHAMP' in info_up or 'PRE CHAMP' in info_up or 'PRECHAMP' in info_up or 'RISING STAR' in info_up or 'CLOSED' in info_up:
        return 1000 
    if 'OPEN' in info_up or 'ADVANCED' in info_up or 'SCHOLAR' in info_up or 'CHAMP' in info_up or 'SLAM' in info_up or 'DSS' in info_up or "DANCESPORT SERIES" in info_up:
        return 1500
    else:
        print('Unknown level for ' + info)
        return None
        

def update_elo_ratings(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')    
    
    comp = get_object_or_404(Comp, pk=comp_id)
    if comp.process_state != Comp.RESULTS_RESOLVED:
        return redirect("comps:comp_detail", comp_id)
    
    # initialize the multi-elo entries
    elo = MultiElo(score_function_base=1.25)
    
    heats = Heat.objects.filter(comp=comp).order_by('time')
    # first, ensure we can determine a valid initial elo rating for this heat
    for h in heats:
        # get the entries for this heat in order of their results
        entries = Heat_Entry.objects.filter(heat=h)
        
        # if there are multiple entries, update elo ratings for each entry
        if len(entries) > 1:
            # determine initial elo rating for entries with no previous rating
            if initial_elo_rating(h.category, h.info) is None:
                heat_data = list()
                heat_data.append({'heat': h, 'entries': entries, 'results_available': False, 'error': "Unable to determine initial elo rating"})
                return render(request, 'comps/heat.html', {'comp': comp, 'heat_data': heat_data, 'show_edit_button': True})
    
    # for each heat in this comp
    for h in heats:
        # get the entries for this heat in order of their results
        entries = Heat_Entry.objects.filter(heat=h).order_by('-points')
        
        # if there are multiple entries, update elo ratings for each entry
        if len(entries) > 1:
            # determine initial elo rating for entries with no previous rating
            initial_rating = initial_elo_rating(h.category, h.info)      
            #print(str(h) + ' ' + str(h.time) + ' ' + h.info + ' ' + h.style +  ' ' + str(initial_rating))
            
            rating_list = list()
            elo_inputs = list()
            # for each entry
            for e in entries:
                # get their existing elo rating or create one with initial rating
                try:
                    rating = EloRating.objects.get(couple=e.couple, style=h.style)
                    if rating.value is None:
                        rating.value = initial_rating
                        rating.save()
                except EloRating.DoesNotExist:
                    rating = EloRating()
                    rating.couple = e.couple
                    rating.style = h.style
                    rating.value = initial_rating
                    rating.save()
                    
                rating_list.append(rating)
                elo_inputs.append(rating.value)
            
            new_ratings = elo.get_new_ratings(numpy.array(elo_inputs))
            
            for index in range(len(rating_list)):
                #print('  ' + str(rating_list[index]) + ' ' + str(round(new_ratings[index], 2)))
                rating_list[index].value = new_ratings[index]
                rating_list[index].save()
                
    comp.process_state = Comp.ELO_RATINGS_UPDATED
    comp.save()
        
    return redirect("show_elo_ratings", "PRC", "SMOO")