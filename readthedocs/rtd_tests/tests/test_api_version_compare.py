from django.test import TestCase

from readthedocs.api.v2.views.footer_views import get_version_compare_data
from readthedocs.builds.constants import LATEST
from readthedocs.projects.models import Project


class VersionCompareTests(TestCase):
    fixtures = ['eric.json', 'test_data.json']

    def setUp(self):
        Project.objects.update(show_version_warning=True)

    def test_not_highest(self):
        project = Project.objects.get(slug='read-the-docs')
        version = project.versions.get(slug='0.2.1')

        data = get_version_compare_data(project, version)
        self.assertEqual(data['is_highest'], False)

    def test_latest_version_highest(self):
        project = Project.objects.get(slug='read-the-docs')

        data = get_version_compare_data(project)
        self.assertEqual(data['is_highest'], True)

        version = project.versions.get(slug=LATEST)
        data = get_version_compare_data(project, version)
        self.assertEqual(data['is_highest'], True)

    def test_real_highest(self):
        project = Project.objects.get(slug='read-the-docs')
        version = project.versions.get(slug='0.2.2')

        data = get_version_compare_data(project, version)
        self.assertEqual(data['is_highest'], True)
