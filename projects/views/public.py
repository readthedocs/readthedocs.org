import simplejson

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import (HttpResponse, HttpResponseRedirect,
                         Http404, HttpResponsePermanentRedirect)
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list, object_detail
from django.views.static import serve

from projects.models import Project
from core.views import serve_docs

from taggit.models import Tag

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
    version_slug = 'latest'
    if not filename:
        filename = "index.html"
    split_filename = filename.split('/')
    if len(split_filename) > 1:
        version = split_filename[1]
        proj = get_object_or_404(Project, slug=project_slug)
        valid_version = proj.versions.filter(slug=version).count()
        if valid_version:
            version_slug = version
            filename = '/'.join(split_filename[1:])
    return serve_docs(request=request, project_slug=project_slug, version_slug=version, filename=filename)

def project_detail(request, project_slug):
    """
    A detail view for a project with various dataz
    """
    queryset = Project.objects.live()
    projects = Project.objects.filter(slug=project_slug)
    if not projects.count():
        #Handle old User URLs if possible.
        #/projects/<user>/ used to be the user list, moved to
        #/profiles/<user>/ and made projects top-level.
        users = User.objects.filter(username=project_slug)
        if users.count():
            return HttpResponseRedirect(users[0].get_absolute_url())
    return object_detail(
        request,
        queryset=queryset,
        slug_field='slug',
        slug=project_slug,
        template_object_name='project',
    )

def legacy_project_detail(request, username, project_slug):
    queryset = Project.objects.live()
    return HttpResponsePermanentRedirect(reverse(
        project_detail, kwargs = {
            'project_slug': project_slug,
        }
    ))

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



def subdomain_handler(request, subdomain, filename):
    """
    This provides the fall-back routing for subdomain requests.

    This was made primarily to redirect old subdomain's to their version'd brothers.
    """
    if not filename:
        filename = "index.html"
    split_filename = filename.split('/')
    #A correct URL, with a language and version.
    proj = get_object_or_404(Project, slug=subdomain)
    if len(split_filename) > 2:
        language = split_filename[0]
        version = split_filename[1]
        valid_version = proj.versions.filter(slug=version).count()
        #Hard code this for now.
        if valid_version or version == 'latest' and language == 'en':
            version_slug = version
            filename = '/'.join(split_filename[2:])
            return serve_docs(request=request,
                              project_slug=subdomain,
                              lang_slug='en',
                              version_slug=version_slug,
                              filename=filename)
    elif len(split_filename) == 2:
        version = split_filename[0]
        valid_version = proj.versions.filter(slug=version).count()
        if valid_version:
            return HttpResponseRedirect('/en/%s/%s' %
                                        (version,
                                         '/'.join(split_filename[1:])))

    default_version = proj.get_default_version()
    return HttpResponseRedirect('/en/%s/%s' % (default_version, filename))
