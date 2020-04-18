from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import Comp
from .forms import CompForm
from .comp_mngr_heatlist import CompMngrHeatlist

def all_comps(request):
    comps = Comp.objects.order_by('start_date')
    paginator = Paginator(comps, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/all_comps.html", {'page_obj': page_obj})

def detail(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
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
    print(comp.heatsheet_url)

    heatlist = CompMngrHeatlist()
    heatlist.open(comp.heatsheet_url)
    print(heatlist.comp_name)

    for index in range(len(heatlist.dancers)):
        the_name = heatlist.get_next_dancer(index, comp)
        #print(the_name)
    heatlist.complete_processing()

    return render(request, "comps/process_heatlists.html", {'comp':comp})
