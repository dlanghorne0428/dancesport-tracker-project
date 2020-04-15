from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import Comp
from .forms import CompForm

def all_comps(request):
    comps = Comp.objects.order_by('start_date')
    paginator = Paginator(comps, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/all_comps.html", {'page_obj': page_obj})

def detail(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    print(comp.title)
    return render(request, "comps/detail.html", {'comp':comp})

def createcomp(request):
    if request.method == "GET":
        return render(request, 'comps/createcomp.html', {'form':CompForm()})
    else:
        try:
            form = CompForm(request.POST)
            form.save()
            return redirect('all_comps')
        except ValueError:
            return render(request, 'comps/createcomp.html', {'form':CompForm(), 'error': "Invalid data submitted."})


def process_heatlists(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    print(comp.title)
    return render(request, "comps/process_heatlists.html", {'comp':comp})
