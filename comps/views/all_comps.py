from django.core.paginator import Paginator
from django.shortcuts import render
from comps.models.comp import Comp
from comps.filters import CompFilter

def all_comps(request):
    # only show add button for valid users
    show_add_button = request.user.is_superuser

    # get the list of comps, potentially filtered
    f = CompFilter(request.GET, queryset=Comp.objects.all().order_by('-start_date', 'title'))
    
    paginator = Paginator(f.qs, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/all_comps.html", {'page_obj': page_obj, 'show_add_button': show_add_button, 'filter': f})
