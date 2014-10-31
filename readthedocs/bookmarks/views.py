
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic import ListView
from django.core.urlresolvers import reverse
from django.template import RequestContext
import simplejson


from bookmarks.models import Bookmark
from projects.models import Project


class BookmarkList(ListView):
    model = Bookmark

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)


@login_required
def bookmark_add(request):
    """Add a new bookmark for the current user to point at
    ``project``, ``version``, ``page``, and ``url``.
    """
    if request.method == 'POST':
        post_json = simplejson.loads(request.body)
        try:
            project_slug = post_json['project']
            version_slug = post_json['version']
            page_slug = post_json['page']
            url = post_json['url']
        except KeyError:
            return HttpResponse(simplejson.dumps(
             {'error': "Invalid parameters"}   
            ))

        project = Project.objects.get(slug=project_slug)
        version = project.versions.get(slug=version_slug)

        Bookmark.objects.get_or_create(
            user=request.user,
            url=url,
            project=project,
            version=version,
            page=page_slug,
        )

        payload = simplejson.dumps({'added': True})
        return HttpResponse(
            payload,
            status=201,
            mimetype='text/javascript'
        )
    else:
        return HttpResponse(
            simplejson.dumps(
                {'error': 'You must POST!'}
            ),
            mimetype='text/javascript'
        )


@login_required
def bookmark_remove(request, **kwargs):
    """Delete a previously-saved bookmark
    """
    if request.method == 'POST':
        if 'bookmark_pk' in kwargs:
            bookmark = get_object_or_404(Bookmark, pk=kwargs['bookmark_pk'])
            bookmark.delete()
            return HttpResponseRedirect(reverse('bookmark_list'))
        else:
            try:
                post_json = simplejson.loads(request.body)
                project = Project.objects.get(slug=post_json['project'])
                version = project.versions.get(slug=post_json['version'])
            except KeyError:
                return HttpResponse(simplejson.dumps(
                 {'error': "Invalid parameters"}   
                ))

            bookmark = get_object_or_404(
                Bookmark,
                user=request.user,
                url=post_json['url'],
                project=project,
                version=version,
                page=post_json['page']
            )
            bookmark.delete()

            return HttpResponse(
                simplejson.dumps({'removed': True}),
                status=200,
                mimetype="/text/javascript"
            )

    return render_to_response(
        'bookmarks/bookmark_delete.html',
        context_instance=RequestContext(request)
    )
