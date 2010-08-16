from django.views.generic.list_detail import object_list

from watching.models import PageView

def pageview_list(request, queryset=PageView.objects.all()):
    return object_list(
        request,
        queryset=queryset,
        template_object_name='pageview',
    )

