from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from comps.forms import CompCoupleForm
from comps.models.comp import Comp
from comps.models.comp_couple import Comp_Couple
from comps.models.heat_entry import Heat_Entry
from rankings.models import Dancer, Couple
from rankings.filters import DancerFilter

def couples(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    if comp.process_state in [Comp.DANCERS_LOADED, Comp.DANCER_NAMES_FORMATTED, Comp.HEATS_LOADED]:
        return redirect ('comps:resolve_dancers', comp_id)
    elif request.method == "POST":
        f = CompCoupleForm(request.POST)
        if not f.is_valid():
            return redirect ('comps:comp_detail', comp_id)
        else:
            search_parms = f.cleaned_data
            if len(search_parms['name']) > 0:
                name = search_parms['name'].upper()  # filter on name
                couples = list()
                all_couples = Comp_Couple.objects.filter(comp=comp)
                for c in all_couples:
                    if name in c.couple.dancer_1.name_last.upper() or name in c.couple.dancer_2.name_last.upper():
                        couples.append(c)
            elif len(search_parms['number']) > 0:
                number = search_parms['number']   # filter on number
                couples = Comp_Couple.objects.filter(comp=comp, shirt_number=number).order_by('couple')
            else:
                couples = Comp_Couple.objects.filter(comp=comp).order_by('couple')

    else:  # GET
        f = CompCoupleForm()
        couples = Comp_Couple.objects.filter(comp=comp).order_by('couple')
        if len(couples) == 0:
            all_couples = Couple.objects.filter(heat_entry__heat__comp=comp).distinct().order_by('dancer_1__name_last')
            for c in all_couples:
                comp_couple = Comp_Couple()
                shirt_number = Heat_Entry.objects.filter(couple=c, heat__comp=comp).first().shirt_number
                comp_couple.populate(comp, c, shirt_number)
                comp_couple.save()
            couples = Comp_Couple.objects.filter(comp=comp).order_by('couple')

    paginator = Paginator(couples,16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'comps/couples.html', {'comp': comp, 'page_obj': page_obj, 'form': f})
