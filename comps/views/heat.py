from django.shortcuts import render, redirect, get_object_or_404
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from comps.forms import HeatForm
from rankings.rating_stats import couple_stats


def heat(request, heat_id):
    # only show edit button for valid users
    show_edit_button = request.user.is_superuser

    heat = get_object_or_404(Heat, pk=heat_id)

    # get all heats that match this category and time of day
    parallel_heats = Heat.objects.filter(comp=heat.comp).filter(category=heat.category).filter(time=heat.time).order_by('extra', 'info')
    heat_data = list()

    for h in parallel_heats:
        results_available = False
        entries = Heat_Entry.objects.filter(heat=h)
        if entries.count() > 0:
            if entries.first().points is not None:
                entries = entries.order_by('-points')
                results_available = True
            else:
                for e in entries:
                    if h.style is None:
                        stats = couple_stats(e.couple)
                    else:
                        stats = couple_stats(e.couple, h.style)
                    e.rating = stats['rating']
                    e.save()
                entries = entries.order_by('-rating', 'shirt_number')

        next_item = {'heat': h, 'entries': entries, 'results_available': results_available}
        heat_data.append(next_item)

    comp_id = heat.comp_id
    # determine how many different start times match this heat number (could be multiple if there are A or B heats with the same heat_number)
    times = Heat.objects.filter(comp=heat.comp).filter(category=heat.category).filter(heat_number=heat.heat_number).datetimes('time', 'minute')
    # if there's only one start time, use the heat number to determine next heat and previous heat
    if len(times) == 1:
        prev_heat = Heat.objects.filter(comp=heat.comp).filter(category=heat.category).filter(heat_number=heat.heat_number-1).first()
        if prev_heat is not None:
            prev_heat_id = prev_heat.id
        else:
            prev_heat_id = None
        next_heat = Heat.objects.filter(comp=heat.comp).filter(category=heat.category).filter(heat_number=heat.heat_number+1).first()
        if next_heat is not None:
            next_heat_id = next_heat.id
        else:
            next_heat_id = None
    else:
        #print(times)
        # heats at multiple start times for this heat number, search the list for the current heat being displayed
        for index in range(len(times)):
            if times[index] == heat.time:
                print("Found " + str(heat.time))
                if index == 0:
                    # if the current heat is the earliest time, use the heat number to find the previous heat
                    prev_heat = Heat.objects.filter(comp=heat.comp).filter(category=heat.category).filter(heat_number=heat.heat_number-1).first()
                    if prev_heat is not None:
                        prev_heat_id = prev_heat.id
                    else:
                        prev_heat_id = None
                    # the next heat is found by looking at the next index of the time list
                    next_heat_id = Heat.objects.filter(comp=heat.comp).filter(category=heat.category).filter(time=times[index+1]).first().id
                elif index == len(times) - 1:
                    # if the current heat is the latest time, the previous heat is found by looking at the previous index of the time list
                    prev_heat_id = Heat.objects.filter(comp=heat.comp).filter(category=heat.category).filter(time=times[index-1]).first().id
                    # the next heat is found by the heat number
                    next_heat = Heat.objects.filter(comp=heat.comp).filter(category=heat.category).filter(heat_number=heat.heat_number+1).first()
                    if next_heat is not None:
                        next_heat_id = next_heat.id
                    else:
                        next_heat_id = None
                else:
                    # both previous and next heats are found by looking at the list of times
                    #print(str(times[index-1]) + ' ' + str(times[index+1]))
                    prev_heat_id = Heat.objects.filter(comp=heat.comp).filter(time=times[index-1]).first().id
                    #print(prev_heat_id)
                    next_heat_id = Heat.objects.filter(comp=heat.comp).filter(time=times[index+1]).first().id
                    #print(next_heat_id)
                break
        else:  # shouldn't get here, but set both previous and next heat IDs to none
            prev_heat_id = None
            next_heat_id = None

    return render(request, 'comps/heat.html', {'comp': heat.comp, 'heat_data': heat_data, 'prev_heat_id': prev_heat_id, 'next_heat_id': next_heat_id, 'show_edit_button': show_edit_button})
