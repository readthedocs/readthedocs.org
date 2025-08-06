import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from readthedocs.projects.models import Project
from readthedocs.analytics.models import PageView
from django.utils import timezone
from django.conf import settings
from django_dynamic_fixture import get

@pytest.mark.django_db
def test_project_delete_triggers_pageview_cleanup(settings):

    settings.CELERY_TASK_ALWAYS_EAGER = True  # Run Celery tasks eagerly
    user = get(User)
    project = get(Project, users=[user], slug="test-project")
    project.save()

    # Create some PageViews for the project
    get(
        PageView,
        project=project,
        path="/index.html",
        full_path="/en/latest/index.html",
        view_count=5,
        date=timezone.now().date(),
        status=200,
    )
    get(
        PageView,
        project=project,
        path="/about.html",
        full_path="/en/latest/about.html",
        view_count=2,
        date=timezone.now().date(),
        status=200,
    )

    # The PageViews should be deleted by the background task
    assert PageView.objects.filter(project__slug='test-project').count() == 2

    # Delete the project
    project.delete()

    # The PageViews should be deleted by the background task
    assert PageView.objects.filter(project__slug='test-project').count() == 0
