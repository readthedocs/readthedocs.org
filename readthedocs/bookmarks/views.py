from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic import ListView, View
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
import simplejson

from bookmarks.models import Bookmark
from projects.models import Project


class BookmarkExistsView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(BookmarkExistsView, self).dispatch(*args, **kwargs)

    def get(self, request):
        return HttpResponse(
            content=simplejson.dumps(
                {'error': 'You must POST!'}
            ),
            content_type='application/json',
            status=405
        )

    def post(self, request, *args, **kwargs):
        """
        Returns:
            200 response with exists = True in json if bookmark exists.
            404 with exists = False in json if no matching bookmark is found.
            400 if json data is missing any one of: project, version, page.
        """
        post_json = simplejson.loads(request.body)
        try:
            project = post_json['project']
            version = post_json['version']
            page = post_json['page']
        except KeyError:
            return HttpResponseBadRequest(
                content=simplejson.dumps({'error': 'Invalid parameters'})
            )
        try:
            Bookmark.objects.get(
                project__slug=project,
                version__slug=version,
                page=page
            )
        except ObjectDoesNotExist:
            return HttpResponse(
                content=simplejson.dumps({'exists': False}),
                status=404,
                mimetype="application/json"
            )

        return HttpResponse(
            content=simplejson.dumps({'exists': True}),
            status=200,
            mimetype="application/json"
        )


class BookmarkListView(ListView):
    """ Displays all of a logged-in user's bookmarks """
    model = Bookmark

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BookmarkListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)


class BookmarkAddView(View):
    """ Adds bookmarks in response to POST requests """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BookmarkAddView, self).dispatch(*args, **kwargs)

    def get(self, request):
        return HttpResponse(
            content=simplejson.dumps(
                {'error': 'You must POST!'}
            ),
            content_type='application/json',
            status=405
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
            return HttpResponseBadRequest(
                content=simplejson.dumps({'error': "Invalid parameters"})
            )

        try:
            project = Project.objects.get(slug=project_slug)
            version = project.versions.get(slug=version_slug)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest(
                content=simplejson.dumps(
                    {'error': "Project or Version does not exist"}
                )
            )

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
            mimetype='application/json'
        )


class BookmarkRemoveView(View):
    """
    Deletes a user's bookmark in response to a POST request.
    Renders a delete? confirmaton page in response to a GET request.
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BookmarkRemoveView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render_to_response(
            'bookmarks/bookmark_delete.html',
            context_instance=RequestContext(request)
        )

    def post(self, request, *args, **kwargs):
        """
        Will delete bookmark with a primary key from the url
        or using json data in request.
        """
        if 'bookmark_pk' in kwargs:
            bookmark = get_object_or_404(Bookmark, pk=kwargs['bookmark_pk'])
            bookmark.delete()
            return HttpResponseRedirect(reverse('bookmark_list'))
        else:
            try:
                post_json = simplejson.loads(request.body)
                project = Project.objects.get(slug=post_json['project'])
                version = project.versions.get(slug=post_json['version'])
                url = post_json['url']
                page = post_json['page']
            except KeyError:
                return HttpResponseBadRequest(
                    simplejson.dumps({'error': "Invalid parameters"})
                )

            bookmark = get_object_or_404(
                Bookmark,
                user=request.user,
                url=url,
                project=project,
                version=version,
                page=page
            )
            bookmark.delete()

            return HttpResponse(
                simplejson.dumps({'removed': True}),
                status=200,
                mimetype="application/json"
            )
