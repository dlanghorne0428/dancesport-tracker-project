from django.core.paginator import Paginator
from django.shortcuts import render
from comps.models.comp import Comp


def all_comps(request):
    # only show add button for valid users
    show_add_button = request.user.is_superuser

    comps = Comp.objects.order_by('start_date')
    paginator = Paginator(comps, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "comps/all_comps.html", {'page_obj': page_obj, 'show_add_button': show_add_button})
