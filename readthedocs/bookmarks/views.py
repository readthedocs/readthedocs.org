import simplejson

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic import ListView
from django.core.urlresolvers import reverse
from django.template import RequestContext

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
def bookmark_remove(request, **kwargs):
    """Delete a previously-saved bookmark
    """
    bookmark = get_object_or_404(Bookmark, pk = kwargs['bookmark_pk'])

    if request.user != bookmark.user:
        return HttpResponseRedirect(reverse('user_bookmarks'))

    if request.method == 'POST':
        bookmark.delete()
        return HttpResponseRedirect(reverse('user_bookmarks'))

    return render_to_response('bookmarks/bookmark_delete.html',
                            # {'bookmark_pk': bookmark.pk},
                            context_instance=RequestContext(request))
