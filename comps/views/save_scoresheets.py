from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry


def save_scoresheets(request, comp_id):        
    '''Save scoresheet results to a common file format.'''
    comp = get_object_or_404(Comp, pk=comp_id)
    if comp.process_state not in [Comp.RESULTS_RESOLVED, Comp.ELO_RATINGS_UPDATED, Comp.COMPLETE]:
        return redirect ('comps:comp_heats', comp_id)

    heats = Heat.objects.filter(comp=comp).order_by('time')
    filename = "./static/" + comp.title + "_scoresheets.txt"
    fp = open(filename, "w", encoding="UTF-8")
    fp.write("Comp Name:" + comp.title + "\n")
    fp.write("Results for" + '\t' + str(len(heats)) + '\tHeats\n')

    for h in heats:
        heat_entries = Heat_Entry.objects.filter(heat=h).order_by('-points')
        fp.write(h.get_category_display() + '\t' + str(h.heat_number) + '\t' + h.time.isoformat() + '\t' + h.info + '\n')
        for e in heat_entries:
            fp.write(str(e.couple) + '\t' + str(e.shirt_number) + '\t' + str(e.result) + ' \t' + str(e.points) + '\n')
            
        fp.write("\n")
    
    fp.write("--End of Results--")
    fp.close()
        
        
    return redirect('comps:comp_heats', comp_id)
