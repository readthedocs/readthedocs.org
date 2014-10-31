from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic import ListView, View
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.utils.decorators import method_decorator
import simplejson

from bookmarks.models import Bookmark
from projects.models import Project


class BookmarkListView(ListView):
    model = Bookmark

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)


class BookmarkAddView(View):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BookmarkAddView, self).dispatch(*args, **kwargs)

    def get(self, request):
        return HttpResponse(
            simplejson.dumps(
                {'error': 'You must POST!'}
            ),
            mimetype='text/javascript'
        )

    def post(self, request, *args, **kwargs):
        """Add a new bookmark for the current user to point at
        ``project``, ``version``, ``page``, and ``url``.
        """
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
        return HttpResponse(
            simplejson.dumps({'added': True}),
            status=201,
            mimetype='text/javascript'
        )


class BookmarkRemoveView(View):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BookmarkRemoveView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render_to_response(
            'bookmarks/bookmark_delete.html',
            context_instance=RequestContext(request)
        )

    def post(self, request, *args, **kwargs):
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
