import simplejson

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list, object_detail
from django.views.static import serve

from projects.models import Project
from core.views import serve_docs

from taggit.models import Tag, TaggedItem

def project_index(request, username=None, tag=None):
    """
    The list of projects, which will optionally filter by user or tag,
    in which case a 'person' or 'tag' will be added to the context
    """
    queryset = Project.objects.live()
    if username:
        user = get_object_or_404(User, username=username)
        queryset = queryset.filter(user=user)
    else:
        user = None

    if tag:
        tag = get_object_or_404(Tag, slug=tag)
        queryset = queryset.filter(tags__name__in=[tag.slug])
    else:
        tag = None

    return object_list(
        request,
        queryset=queryset,
        extra_context={'person': user, 'tag': tag},
        page=int(request.GET.get('page', 1)),
        template_object_name='project',
    )

def slug_detail(request, project_slug, filename):
    """
    A detail view for a project with various dataz
    """
    if not filename:
        filename = "index.html"
    project = get_object_or_404(Project, slug=project_slug)
    return serve_docs(request=request, project_slug=project_slug, version_slug='latest', filename=filename)
    
def project_detail(request, username, project_slug):
    """
    A detail view for a project with various dataz
    """
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
    """
    List of all tags by most common
    """
    tag_qs = Project.tags.most_common()
    return object_list(
        request,
        queryset=tag_qs,
        page=int(request.GET.get('page', 1)),
        template_object_name='tag',
        template_name='projects/tag_list.html',
    )

def search(request):
    """
    our ghetto site search.  see roadmap.
    """
    if 'q' in request.GET:
        term = request.GET['q']
    else:
        raise Http404
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
    """
    return a json list of project names
    """
    if 'term' in request.GET:
        term = request.GET['term']
    else:
        raise Http404
    queryset = Project.objects.live(name__icontains=term)[:20]

    project_names = queryset.values_list('name', flat=True)
    json_response = simplejson.dumps(list(project_names))

    return HttpResponse(json_response, mimetype='text/javascript')

def project_pdf(request, username, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    pdf = project.full_pdf_path.replace(project.full_doc_path, '')
    base = project.full_doc_path
    return serve(request, pdf, base)
