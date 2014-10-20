import simplejson

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.generic import ListView

from django.views.decorators.csrf import csrf_exempt

from bookmarks.models import Bookmark
from builds.models import Version
from projects.models import Project


class BookmarkList(ListView):
    model = Bookmark

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)


@login_required
@csrf_exempt
def bookmark_add(request):
    """Add a new bookmark for the current user to ``url``.
    """
    if request.method == 'POST':
        post_json = simplejson.loads(request.body)
        project_slug = post_json['project']
        version_slug = post_json['version']
        page_slug = post_json['page']
        url = post_json['url']

        project = Project.objects.get(slug=project_slug)
        version = project.versions.get(slug=version_slug)

        bookmark, _ = Bookmark.objects.get_or_create(
            user=request.user,
            url=url,
            project=project,
            version=version,
            page=page_slug,
        )
        payload = simplejson.dumps({'added': True})
        response = HttpResponse(payload, status=201, mimetype='text/javascript')
        return response
    else:
        return HttpResponse(simplejson.dumps({'error': 'You must POST!'}), mimetype='text/javascript')


@login_required
@csrf_exempt
def bookmark_remove(request):
    """Remove the current user's bookmark to ``url``.
    """
    if request.method == 'POST':
        post_json = simplejson.loads(request.body)
        project = post_json['project']
        version = post_json['version']
        page = post_json['page']
        try:
            bookmark = Bookmark.objects.get(
                user=request.user,
                project__slug=project,
                version__slug=version,
                page=page,
            )
        except Bookmark.DoesNotExist:
            payload = simplejson.dumps({'removed': False})
        else:
            bookmark.delete()
            payload = simplejson.dumps({'removed': True})
        return HttpResponse(payload, mimetype='text/javascript')
    else:
        return HttpResponse(simplejson.dumps({'error': 'You must POST!'}), mimetype='text/javascript')
