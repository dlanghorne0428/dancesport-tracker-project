from django.core.paginator import Paginator
from django.shortcuts import render
from comps.models import Comp


def all_comps(request):
    comps = Comp.objects.order_by('start_date')
    paginator = Paginator(comps, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/all_comps.html", {'page_obj': page_obj})
