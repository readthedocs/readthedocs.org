from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from editor.forms import FileForm, PullRequestForm
from projects.models import Project
from projects.tasks import scrape_conf_file
from vcs_support.base import get_backend
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
    basepath = os.path.join(project.rtd_build_path, 'latest')
    if not os.path.exists(os.path.join(basepath, filename)):
        return _project_404(request, project)
    repo_file = _replace_ext(_get_rel_filepath(project, filename), project.suffix)
    backend = get_backend(project.repo_type)
    if not backend:
        return _project_404(request, project)
    working_dir = os.path.join(project.user_doc_path, project.slug)
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
    vcs_repo = backend(project.repo, working_dir)
    vcs_repo.update()
    contributor = vcs_repo.get_contribution_backend()
    if not contributor:
        return _project_404(request, project)
    if request.method == 'POST':
        form = FileForm(request.POST)
        if form.is_valid():
            body = form.cleaned_data['body']
            comment = form.cleaned_data['comment']
            contributor.set_branch_file(request.user, repo_file, body, comment)
    else:
        initial = {
            'body': contributor.get_branch_file(request.user, repo_file)
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
    backend = get_backend(project.repo_type)
    if not backend:
        return _project_404(request, project)
    working_dir = os.path.join(project.user_doc_path, project.slug)
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
    vcs_repo = backend(project.repo, working_dir)
    vcs_repo.update()
    contributor = vcs_repo.get_contribution_backend()
    if not contributor:
        return _project_404(request, project)
    if request.method == 'POST':
        form = PullRequestForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            comment = form.cleaned_data['comment']
            contributor.push_branch(request.user, title, comment)
    else:
        form = PullRequestForm()
    ctx = RequestContext(request)
    ctx['form'] = form
    ctx['project'] = project
    return render_to_response('editor/editor_push.html', ctx)