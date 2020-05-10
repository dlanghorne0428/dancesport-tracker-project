from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from .models import Dancer, Couple
from comps.models import Comp, Heat, HeatEntry
from .forms import DancerForm, CoupleForm
from .filters import DancerFilter

# Create your views here.
def home(request):
    pro_couples = Couple.objects.filter(couple_type=Couple.PRO_COUPLE)
    if request.method == "POST":
        # submit = request.POST.get("submit")
        # print("Submit is", submit)
        style = request.POST.get("style")
        print("Style is", style)
        if style == "Rhythm":
            heat_style = Heat.RHYTHM
        elif style == "Latin":
            heat_style = Heat.LATIN
        elif style == "Standard":
            heat_style = Heat.STANDARD
        else:
            heat_style = Heat.SMOOTH
        for c in pro_couples:
            entries = HeatEntry.objects.filter(couple=c).filter(heat__style=heat_style)
            event_count = 0
            total_points = 0.0
            for e in entries:
                if e.points is not None:
                    event_count += 1
                    total_points += e.points
            if event_count > 0:
                c.event_count = event_count
                c.total_points = round(total_points, 2)
                c.rating = round(total_points / event_count, 2)
            else:
                c.event_count = 0
                c.total_points = 0.0
                c.rating = 0.0
            c.save()
    pro_couples = pro_couples.filter(event_count__gte=1).order_by('-rating')
    return render(request, "rankings/home.html", {'couples': pro_couples, 'styles': Heat.DANCE_STYLE_CHOICES})


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
    all_comps = Comp.objects.all()
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
