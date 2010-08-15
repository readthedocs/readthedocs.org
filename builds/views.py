import simplejson

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list, object_detail

from builds.models import Build

from taggit.models import Tag, TaggedItem

def build_list(request, username=None, tag=None):
    queryset = Build.objects.all()
    if username:
        user = get_object_or_404(User, username=username)
        queryset = queryset.filter(user=user)
    else:
        user = None
    if tag:
        tag = get_object_or_404(Tag, slug=tag)
        queryset = queryset.filter(tags__in=[tag.slug])
    else:
        tag = None

    return object_list(
        request,
        queryset=queryset,
        extra_context={'person': user, 'tag': tag},
        template_object_name='build',
    )

def build_detail(request, username, project_slug, pk):
    user = get_object_or_404(User, username=username)
    queryset = user.projects.all()

    return object_detail(
        request,
        queryset=queryset,
        object_id=pk,
        extra_context={'user': user},
        template_object_name='build',
    )
