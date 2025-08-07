from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import TestCase
from readthedocs.projects.models import Project
from readthedocs.builds.models import Version
from readthedocs.analytics.models import PageView
from django.utils import timezone
from django.conf import settings
from django_dynamic_fixture import get

class PageViewTaskTests(TestCase):

    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user], slug="test-project")
        self.project.save()

        # Create some PageViews for the project
        get(
            PageView,
            project=self.project,
            path="/index.html",
            full_path="/en/latest/index.html",
            view_count=5,
            date=timezone.now().date(),
            status=200,
        )
        get(
            PageView,
            project=self.project,
            path="/about.html",
            full_path="/en/latest/about.html",
            view_count=2,
            date=timezone.now().date(),
            status=200,
        )

    def test_pageview_cleanup(self):
        # The PageViews should be present initially
        self.assertEqual(PageView.objects.filter(project__slug='test-project').count(), 2)

        # Delete the project
        self.project.delete()

        # The PageViews should be deleted by the background task
        self.assertEqual(PageView.objects.filter(project__slug='test-project').count(), 0)

    def test_pageview_cleanup_on_version_delete(self):
        # Create a version for the project
        version = get(Version, project=self.project, slug="v1.0", verbose_name="v1.0")
        version.save()

        # Create PageViews for this version
        get(
            PageView,
            project=self.project,
            version=version,
            path="/v1.0/index.html",
            full_path="/en/v1.0/index.html",
            view_count=3,
            date=timezone.now().date(),
            status=200,
        )

        # There should be 3 PageViews now (2 from setUp, 1 for version)
        self.assertEqual(PageView.objects.filter(project__slug='test-project').count(), 3)
        self.assertEqual(PageView.objects.filter(version__slug=version.slug).count(), 1)

        # Delete the version
        version.delete()

        # The PageView for this version should be deleted, others remain
        self.assertEqual(PageView.objects.filter(project__slug='test-project').count(), 2)
        self.assertEqual(PageView.objects.filter(version__slug=version.slug).count(), 0)
