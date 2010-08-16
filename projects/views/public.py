import simplejson

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list, object_detail

from projects.models import Project

from taggit.models import Tag, TaggedItem

def project_index(request, username=None, tag=None):
    queryset = Project.objects.live()
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
        page=int(request.GET.get('page', 1)),
        template_object_name='project',
    )

def project_detail(request, username, project_slug):
    user = get_object_or_404(User, username=username)
    queryset = user.projects.live()
    
    return object_detail(
        request,
        queryset=queryset,
        slug_field='slug',
        slug=project_slug,
        extra_context={'user': user},
        template_object_name='project',
    )

def tag_index(request):
    tag_qs = Project.tags.most_common()
    return object_list(
        request,
        queryset=tag_qs,
        page=int(request.GET.get('page', 1)),
        template_object_name='tag',
        template_name='projects/tag_list.html',
    )

def search(request):
    term = request.GET['q']
    queryset = Project.objects.live(name__icontains=term)
    if queryset.count() == 1:
        return HttpResponseRedirect(queryset[0].get_absolute_url())
    
    return object_list(
        request,
        queryset=queryset,
        template_object_name='term',
        extra_context={'term': term},
        template_name='projects/search.html',
    )

def search_autocomplete(request):
    term = request.GET['term']
    queryset = Project.objects.live(name__icontains=term)[:20]

    project_names = queryset.values_list('name', flat=True)
    json_response = simplejson.dumps(list(project_names))

    return HttpResponse(json_response, mimetype='text/javascript')
