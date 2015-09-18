from django.contrib.admindocs.views import extract_views_from_urlpatterns
from django.test import TestCase
from django.core.urlresolvers import reverse

from readthedocs.builds.models import Build, VersionAlias
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.utils import create_user

from django_dynamic_fixture import get
from taggit.models import Tag


class URLAccessMixin(object):

    url_responses = {}

    def login(self):
        raise NotImplementedError

    def is_admin(self):
        raise NotImplementedError

    def assertResponse(self, path, method=None, data=None, **kwargs):
        self.login()
        if method is None:
            method = self.client.get
        if data is None:
            data = {}

        additional_bits = self.url_responses.get(path, {})
        if 'data' in additional_bits:
            data.update(additional_bits['data'])
            del additional_bits['data']

        response = method(path, data=data)

        response_attrs = {
            'status_code': kwargs.pop('status_code', 200),
        }
        response_attrs.update(kwargs)
        response_attrs.update(additional_bits)
        for (key, val) in response_attrs.items():
            self.assertEqual(getattr(response, key), val)
        return response

    def setUp(self):
        # Previous Fixtures
        self.owner = create_user(username='owner', password='test')
        self.tester = create_user(username='tester', password='test')
        self.pip = get(Project, slug='pip', users=[self.owner])


class AdminAccessTest(URLAccessMixin, TestCase):

    url_responses = {
        # Public
        '/projects/search/autocomplete/': {'data': {'term': 'pip'}},
        '/projects/autocomplete/version/pip/': {'data': {'term': 'pip'}},
        '/projects/pip/autocomplete/file/': {'data': {'term': 'pip'}},
        '/projects/pip/downloads/pdf/latest/': {'status_code': 302},
        '/projects/pip/badge/': {'status_code': 302},
        # Private
        '/dashboard/import/manual/demo/': {'status_code': 302},
        '/dashboard/pip/': {'status_code': 302},
        # This depends on an inactive project, we should make it not 404 here, but 400
        '/dashboard/pip/version/latest/delete_html/': {'status_code': 404},
    }

    def setUp(self):
        super(AdminAccessTest, self).setUp()
        self.build = get(Build, project=self.pip)
        self.tag = get(Tag, slug='coolness')
        self.alias = get(VersionAlias, slug='that_alias', project=self.pip)
        self.test_kwargs = {
            'project_slug': self.pip.slug,
            'version_slug': self.pip.versions.all()[0].slug,
            'filename': 'index.html',
            'pk': self.build.pk,
            'type_': 'pdf',
            'tag': self.tag.slug,
            'alias_id': self.alias.pk,
        }

    def _test_url(self, urlpatterns):
        deconstructed_urls = extract_views_from_urlpatterns(urlpatterns)
        added_kwargs = {}
        for (view, regex, namespace, name) in deconstructed_urls:
            for kwarg in self.test_kwargs:
                if kwarg in regex:
                    added_kwargs[kwarg] = self.test_kwargs[kwarg]
            path = reverse(name, kwargs=added_kwargs)
            print "Tested %s (%s)" % (name, path)
            self.assertResponse(path, status_code=200)
            print "Passed %s (%s)" % (name, path)
            added_kwargs = {}

    def test_public_urls(self):
        from readthedocs.projects.urls.public import urlpatterns
        self._test_url(urlpatterns)

    def test_private_urls(self):
        from readthedocs.projects.urls.private import urlpatterns
        self._test_url(urlpatterns)

    def login(self):
        return self.client.login(username='owner', password='test')

    def is_admin(self):
        return True
