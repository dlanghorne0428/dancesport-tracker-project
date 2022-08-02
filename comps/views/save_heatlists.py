from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.comp_couple import Comp_Couple
from comps.models.heat_entry import Heat_Entry
from rankings.models import Dancer
from rankings.filters import DancerFilter

def save_heatlists(request, comp_id):        
    '''Save heatsheet data to a common file format.'''
    comp = get_object_or_404(Comp, pk=comp_id)
    if comp.process_state in [Comp.DANCERS_LOADED, Comp.DANCER_NAMES_FORMATTED, Comp.HEATS_LOADED]:
        return redirect ('comps:resolve_dancers', comp_id)

    comp_couples = Comp_Couple.objects.filter(comp=comp)
    if len(comp_couples) == 0:
        dancers = Dancer.objects.filter(Q(follower_or_instructor__heat_entry__heat__comp=comp) | Q(leader_or_student__heat_entry__heat__comp=comp)).distinct().order_by('name_last', 'name_first')
    else:
        dancers = Dancer.objects.filter(Q(follower_or_instructor__comp_couple__comp=comp) | Q(leader_or_student__comp_couple__comp=comp)).distinct().order_by('name_last', 'name_first')
        
    filename = "./static/" + comp.title + "_heatlists.txt"
    fp = open(filename, "w", encoding="UTF-8")
    fp.write("Comp Name:" + comp.title + "\n")
    #print("Comp Name:" + comp.title)
    fp.write("Dancers" + "\n")
    #print("Dancers")
    for d in dancers:
        first_heat = Heat_Entry.objects.filter(heat__comp=comp).filter(couple__dancer_1=d).first()
        if first_heat is None:
            fp.write(str(d) + ":0" + "\n")
            #print(str(d) + ":0")
        else:
            fp.write(str(d) + ":" + str(first_heat.code) + '\n')  
            #print(str(d) + ":" + str(first_heat.code))  
        
    fp.write("Heats" + "\n")
    #print("Heats")
    for d in dancers:
        heat_entries = Heat_Entry.objects.filter(heat__comp=comp).filter(Q(couple__dancer_1=d) | Q(couple__dancer_2=d)).distinct().order_by('heat__time')
        fp.write("Dancer:" + str(d) + ":Heats:" + str(len(heat_entries)) + "\n")
        #print("Dancer:" + str(d) + ":Heats:" + str(len(heat_entries)))
        for h in heat_entries:
            #print(h.heat.get_category_display() + ' ' + str(h.heat.heat_number) + ' ' + h.heat.time.isoformat() + ' ' + h.heat.info + ' ' + str(h.shirt_number) + ' ' + str(h.couple) + ' x')
            fp.write(h.heat.get_category_display() + '\t' + str(h.heat.heat_number) + '\t' + h.heat.time.isoformat() + '\t' + h.heat.info + '\t' + str(h.shirt_number) + '\t' + str(h.couple) + '\tx\n')
            
        #print()
        fp.write("\n")
        
    fp.close()
        
        
    return redirect('comps:comp_heats', comp_id)
