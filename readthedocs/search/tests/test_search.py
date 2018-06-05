import mock

import django_dynamic_fixture as fixture
from django.test import TestCase, RequestFactory

from readthedocs.projects.models import Project
from readthedocs.search.docsearch import DocSearch


@mock.patch('readthedocsext.search.docsearch.execute_version_search')
class SearchTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.project = fixture.get(Project, slug='test')

    def test_subversions(self, execute_version_search):
        execute_version_search.return_value = {'fake': True}
        request = self.factory.get(
            '/api/v2/docsearch',
            {'project': 'test', 'version': 'latest', 'q': 'query'}
        )
        view = DocSearch.as_view()
        resp = view(request).render()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('fake' in resp.content)
