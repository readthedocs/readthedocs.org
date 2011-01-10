"""Tasks related to projects, including fetching repository code, cleaning
``conf.py`` files, and rebuilding documentation.
"""

from builds.models import Branch
from celery.decorators import task


@task
def push_branch(pk):
    """
    A Celery task that updates the documentation for a project.
    """
    branch = Branch.objects.get(pk=pk)
    with branch.project.repo_lock(30):
        branch.project.contribution_backend.push_branch(branch, branch.title, branch.comment)
    branch.pushed = True
    branch.save()