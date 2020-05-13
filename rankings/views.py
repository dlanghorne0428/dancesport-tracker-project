from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from .models import Dancer, Couple
from comps.models import Comp, Heat, HeatEntry
from .forms import DancerForm, CoupleForm
from .filters import DancerFilter
from operator import itemgetter

# Create your views here.
def home(request):
    couple_types = Couple.COUPLE_TYPE_CHOICES
    heat_couple_type = couple_types[0][0]
    styles = Heat.DANCE_STYLE_CHOICES
    heat_style = styles[0][0]

    url_string = "rankings/?type=" + heat_couple_type + "&style=" + heat_style
    print(url_string)

    return redirect(url_string)


def all_dancers(request):
    #dancers = Dancer.objects.order_by('name_last')
    f = DancerFilter(request.GET, queryset=Dancer.objects.order_by('name_last'))
    paginator = Paginator(f.qs, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/all_dancers.html', {'page_obj': page_obj, 'filter': f})

def createdancer(request):
    if request.method == "GET":
        return render(request, 'rankings/createdancer.html', {'form':DancerForm()})
    else:
        try:
            form = DancerForm(request.POST)
            form.save()
            return redirect('all_dancers')
        except ValueError:
            return render(request, 'rankings/createdancer.html', {'form':DancerForm(), 'error': "Invalid data submitted."})

def viewdancer(request, dancer_pk):
    dancer = get_object_or_404(Dancer, pk=dancer_pk)
    if request.method == "GET":
        form = DancerForm(instance=dancer)
        couples = Couple.objects.filter(Q(dancer_1=dancer) | Q(dancer_2=dancer)).order_by('dancer_1')
        return render(request, 'rankings/viewdancer.html', {'dancer': dancer, 'form': form, 'couples': couples})
    else:
        submit = request.POST.get("submit")
        if submit == "Save":
            try:
                form = DancerForm(request.POST, instance=dancer)
                form.save()
                return redirect('all_dancers')
            except ValueError:
                return render(request, 'rankings/viewdancer.html', {'dancer': dancer, 'form': form, 'error': "Invalid data submitted."})
        elif submit == "Delete Dancer":
            print("Deleting", str(dancer))
            dancer.delete()
            return redirect ('all_dancers')

def all_couples(request):
    couples = Couple.objects.order_by("dancer_1__name_last")
    paginator = Paginator(couples, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/all_couples.html', {'page_obj': page_obj})

def createcouple(request):
    if request.method == "GET":
        return render(request, 'rankings/createcouple.html', {'form':CoupleForm()})
    else:
        try:
            form = CoupleForm(request.POST)
            form.save()
            return redirect('all_couples')
        except ValueError:
            return render(request, 'rankings/createcouple.html', {'form':CoupleForm(), 'error': "Invalid data submitted."})

def viewcouple(request, couple_pk):
    couple = get_object_or_404(Couple, pk=couple_pk)
    all_comps = Comp.objects.all().order_by('-start_date')
    comps_for_couple = list()
    for comp in all_comps:
        if HeatEntry.objects.filter(heat__comp=comp).filter(couple=couple).count() > 0:
            comps_for_couple.append(comp)
    if request.method == "GET":
        form = CoupleForm(instance=couple)
        return render(request, 'rankings/viewcouple.html', {'couple': couple, 'form': form, 'comps_for_couple': comps_for_couple})
    else:
        submit = request.POST.get("submit")
        if submit == "Save":
            try:
                form = CoupleForm(request.POST, instance=couple)
                form.save()
                return redirect('all_couples')
            except ValueError:
                return render(request, 'rankings/viewcouple.html', {'couple': couple, 'form': form, 'error': "Invalid data submitted."})
        elif submit == "Delete Couple":
            print("Deleting", str(couple))
            couple.delete()
            return redirect ('all_couples')


def rankings(request):
    couple_types = Couple.COUPLE_TYPE_CHOICES
    couple_type_choices = list()
    for c in couple_types:
        couple_type_choices.append(c[0])
    couple_type_labels = list()
    for c in couple_types:
        couple_type_labels.append(c[1])

    styles = Heat.DANCE_STYLE_CHOICES
    style_choices = list()
    for s in styles:
        style_choices.append(s[0])
    style_labels = list()
    for s in styles:
        style_labels.append(s[1])

    if request.method == "GET":
        page_number = request.GET.get('page')
        print("Page Number is", page_number)
        heat_couple_type = request.GET.get('type')
        index = couple_type_choices.index(heat_couple_type)
        couple_type = couple_type_labels[index]
        print("Couple_Type is", heat_couple_type, couple_type)
        heat_style = request.GET.get('style')
        index = style_choices.index(heat_style)
        style = style_labels[index]
        print("Style is", heat_style, style)
    else:
        page_number = 1
        couple_type = request.POST.get("couple_type")
        index = couple_type_labels.index(couple_type)
        heat_couple_type = Couple.COUPLE_TYPE_CHOICES[index][0]
        style = request.POST.get("style")
        index = style_labels.index(style)
        heat_style = Heat.DANCE_STYLE_CHOICES[index][0]
        current_url = request.path
        url_string = current_url +"?type=" + heat_couple_type + "&style=" + heat_style
        print(url_string)
        return redirect(url_string)

    couples = Couple.objects.filter(couple_type=heat_couple_type)
    couple_stats = list()
    for c in couples:
        stats = {'couple': c, 'event_count': 0, 'total_points': 0.0, 'rating': 0.0}
        couple_stats.append(stats)

    for cs in couple_stats:
        entries = HeatEntry.objects.filter(couple=cs['couple']).filter(heat__style=heat_style)
        for e in entries:
            if e.points is not None:
                cs['event_count'] += 1
                cs['total_points'] += e.points
        if cs['event_count'] > 0:
            cs['total_points'] = round(cs['total_points'], 2)
            cs['rating'] = round(cs['total_points'] / cs['event_count'], 2)

    #couples = couples.filter(event_count__gte=1).order_by('-rating')
    couple_stats.sort(key=itemgetter('rating'), reverse=True)
    while couple_stats[-1]['event_count'] == 0:
        couple_stats.pop()
    paginator = Paginator(couple_stats, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/rankings.html', {'page_obj': page_obj, 'styles': style_labels, 'selected_style': style,
                                                      'couple_types': couple_type_labels, 'selected_couple_type': couple_type})
