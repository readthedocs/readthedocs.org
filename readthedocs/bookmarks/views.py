"""Views for the bookmarks app."""

from __future__ import absolute_import
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
import json

from readthedocs.bookmarks.models import Bookmark
from readthedocs.projects.models import Project


# These views are CSRF exempt because of Django's CSRF middleware failing here
# https://github.com/django/django/blob/stable/1.6.x/django/middleware/csrf.py#L135-L159
# We don't have a valid referrer because we're on a subdomain


class BookmarkExistsView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(BookmarkExistsView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        return HttpResponse(
            content=json.dumps(
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
        post_json = json.loads(request.body)
        try:
            project = post_json['project']
            version = post_json['version']
            page = post_json['page']
        except KeyError:
            return HttpResponseBadRequest(
                content=json.dumps({'error': 'Invalid parameters'})
            )
        try:
            Bookmark.objects.get(
                project__slug=project,
                version__slug=version,
                page=page
            )
        except ObjectDoesNotExist:
            return HttpResponse(
                content=json.dumps({'exists': False}),
                status=404,
                content_type="application/json"
            )

        return HttpResponse(
            content=json.dumps({'exists': True}),
            status=200,
            content_type="application/json"
        )


class BookmarkListView(ListView):

    """Displays all of a logged-in user's bookmarks"""

    model = Bookmark

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BookmarkListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)


class BookmarkAddView(View):

    """Adds bookmarks in response to POST requests"""

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(BookmarkAddView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        return HttpResponse(
            content=json.dumps(
                {'error': 'You must POST!'}
            ),
            content_type='application/json',
            status=405
        )

    def post(self, request, *args, **kwargs):
        """
        Add a new bookmark for the current user.

        Points at ``project``, ``version``, ``page``, and ``url``.
        """
        post_json = json.loads(request.body)
        try:
            project_slug = post_json['project']
            version_slug = post_json['version']
            page_slug = post_json['page']
            url = post_json['url']
        except KeyError:
            return HttpResponseBadRequest(
                content=json.dumps({'error': "Invalid parameters"})
            )

        try:
            project = Project.objects.get(slug=project_slug)
            version = project.versions.get(slug=version_slug)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest(
                content=json.dumps(
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
            json.dumps({'added': True}),
            status=201,
            content_type='application/json'
        )


class BookmarkRemoveView(View):

    """
    Deletes a user's bookmark in response to a POST request.

    Renders a delete? confirmation page in response to a GET request.
    """

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(BookmarkRemoveView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render_to_response(
            'bookmarks/bookmark_delete.html',
            context_instance=RequestContext(request)
        )

    def post(self, request, *args, **kwargs):
        """
        Delete a bookmark.

        Uses the primary key from the URL or JSON data from the request.
        """
        if 'bookmark_pk' in kwargs:
            bookmark = get_object_or_404(Bookmark, pk=kwargs['bookmark_pk'])
            bookmark.delete()
            return HttpResponseRedirect(reverse('bookmark_list'))
        try:
            post_json = json.loads(request.body)
            project = Project.objects.get(slug=post_json['project'])
            version = project.versions.get(slug=post_json['version'])
            url = post_json['url']
            page = post_json['page']
        except KeyError:
            return HttpResponseBadRequest(
                json.dumps({'error': "Invalid parameters"})
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
            json.dumps({'removed': True}),
            status=200,
            content_type="application/json"
        )
