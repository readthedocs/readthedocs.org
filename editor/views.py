from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from editor.forms import FileForm, PullRequestForm
from editor.models import Branch
from editor.tasks import push_branch
from projects.models import Project
import os

def _project_404(request, project):
    ctx = RequestContext(request)
    ctx['project'] = project
    return render_to_response('404.html', ctx)

def _get_rel_filepath(project, filename):
    doc_base = os.path.join(project.user_doc_path, project.slug)
    abs_doc_root = project.full_doc_path
    rel = os.path.relpath(abs_doc_root, doc_base)
    if rel == '.':
        rel = ''
    return os.path.join(rel, filename)

def _replace_ext(filename, newext):
    return '%s%s' % (os.path.splitext(filename)[0], newext)

@login_required
def editor_pick(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if not project.contribution_backend:
        return _project_404(request, project)
    filepaths = [os.path.relpath(fp, project.full_doc_path) for fp in project.find('*%s' % project.suffix)]
    files = [(filepath, _replace_ext(filepath, '.html')) for filepath in filepaths]
    ctx = RequestContext(request)
    ctx['files'] = files
    ctx['project'] = project
    return render_to_response('editor/editor_pick.html', ctx)

@login_required
def editor_file(request, project_slug, filename):
    """
    Edits a file in a project
    """
    project = get_object_or_404(Project, slug=project_slug)
    if not filename:
        filename = "index.html"
    filename = filename.rstrip('/')
    repo_file = _replace_ext(_get_rel_filepath(project, filename), project.suffix)
    if not project.contribution_backend:
        return _project_404(request, project)
    branch = Branch.objects.get_branch(request.user, project)
    current_data = project.contribution_backend.get_branch_file(branch, repo_file)
    if not current_data:
        return _project_404(request, project)
    if request.method == 'POST':
        form = FileForm(request.POST)
        if form.is_valid():
            body = form.cleaned_data['body']
            comment = form.cleaned_data['comment']
            with project.repo_lock(5):
                project.contribution_backend.set_branch_file(
                    branch, repo_file, body, comment
                )
    else:
        initial = {
            'body': current_data
        }
        form = FileForm(initial=initial)
    ctx = RequestContext(request)
    ctx['form'] = form
    ctx['filename'] = repo_file
    ctx['project'] = project
    return render_to_response('editor/editor_file.html', ctx)
    
@login_required
def editor_push(request, project_slug):
    """
    Push changes upstream
    """
    project = get_object_or_404(Project, slug=project_slug)
    if not project.contribution_backend:
        return _project_404(request, project)
    branch = Branch.objects.get_branch(request.user, project)
    if request.method == 'POST':
        form = PullRequestForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            comment = form.cleaned_data['comment']
            branch.active = False
            branch.comment = comment
            branch.title = title
            branch.save()
            push_branch.delay(pk=branch.pk)
            return HttpResponseRedirect(reverse(editor_pick, args=(project.slug,)))
    else:
        form = PullRequestForm()
    ctx = RequestContext(request)
    ctx['form'] = form
    ctx['project'] = project
    return render_to_response('editor/editor_push.html', ctx)