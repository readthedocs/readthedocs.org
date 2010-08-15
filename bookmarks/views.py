from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.generic.list_detail import object_list

from bookmarks.models import Bookmark
from projects.models import Project

@login_required
def bookmark_list(request):
    queryset = Bookmark.objects.all()
    queryset = queryset.filter(user=request.user)

    return object_list(
        request,
        queryset=queryset,
        template_object_name='bookmark',
    )

@login_required
def bookmark_add(request, url):
    bookmark = Bookmark.objects.create(user=request.user, url=url)
    return HttpResponse('OK', )



