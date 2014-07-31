import simplejson

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.generic.list_detail import object_list

from bookmarks.models import Bookmark


def bookmark_list(request, queryset=Bookmark.objects.all()):
    return object_list(
        request,
        queryset=queryset,
        template_object_name='bookmark',
    )


@login_required
def user_bookmark_list(request):
    """Show a list of the current user's bookmarks.
    """
    queryset = Bookmark.objects.all()
    queryset = queryset.filter(user=request.user)
    return bookmark_list(request, queryset=queryset)


@login_required
def bookmark_add(request, url):
    """Add a new bookmark for the current user to ``url``.
    """
    bookmark, _ = Bookmark.objects.get_or_create(user=request.user, url=url)

    payload = simplejson.dumps({'added': True})

    return HttpResponse(payload, mimetype='text/javascript')


@login_required
def bookmark_remove(request, url):
    """Remove the current user's bookmark to ``url``.
    """
    try:
        bookmark = Bookmark.objects.get(user=request.user, url=url)
    except Bookmark.DoesNotExist:
        pass
    else:
        bookmark.delete()

    payload = simplejson.dumps({'removed': True})

    return HttpResponse(payload, mimetype='text/javascript')
