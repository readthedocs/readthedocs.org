from django.contrib.admindocs.views import extract_views_from_urlpatterns
from django.test import TestCase
from django.core.urlresolvers import reverse

from readthedocs.builds.models import Build, VersionAlias
from readthedocs.projects.models import Project, Domain
from readthedocs.rtd_tests.utils import create_user

from django_dynamic_fixture import get
from taggit.models import Tag


class URLAccessMixin(object):

    url_responses = {}
    default_status_code = 200

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

        additional_bits = self.url_responses.get(path, {}).copy()
        if 'data' in additional_bits:
            data.update(additional_bits['data'])
            del additional_bits['data']

        response = method(path, data=data)

        response_attrs = {
            'status_code': kwargs.pop('status_code', self.default_status_code),
        }
        response_attrs.update(kwargs)
        response_attrs.update(additional_bits)
        for (key, val) in response_attrs.items():
            self.assertEqual(getattr(response, key), val)
        return response

    def _test_url(self, urlpatterns):
        deconstructed_urls = extract_views_from_urlpatterns(urlpatterns)
        added_kwargs = {}
        for (view, regex, namespace, name) in deconstructed_urls:
            for kwarg in self.test_kwargs:
                if kwarg in regex:
                    added_kwargs[kwarg] = self.test_kwargs[kwarg]
            path = reverse(name, kwargs=added_kwargs)
            print "Tested %s (%s)" % (name, path)
            self.assertResponse(path)
            print "Passed %s (%s)" % (name, path)
            added_kwargs = {}

    def setUp(self):
        # Previous Fixtures
        self.owner = create_user(username='owner', password='test')
        self.tester = create_user(username='tester', password='test')
        self.pip = get(Project, slug='pip', users=[self.owner])


class ProjectMixin(URLAccessMixin):

    def setUp(self):
        super(ProjectMixin, self).setUp()
        self.build = get(Build, project=self.pip)
        self.tag = get(Tag, slug='coolness')
        self.alias = get(VersionAlias, slug='that_alias', project=self.pip)
        self.subproject = get(Project, slug='sub', language='ja', users=[self.owner])
        self.pip.add_subproject(self.subproject)
        self.pip.translations.add(self.subproject)
        self.domain = get(Domain, url='http://docs.foobar.com', project=self.pip)
        self.test_kwargs = {
            'project_slug': self.pip.slug,
            'version_slug': self.pip.versions.all()[0].slug,
            'filename': 'index.html',
            'type_': 'pdf',
            'tag': self.tag.slug,
            'alias_id': self.alias.pk,
            'child_slug': self.subproject.slug,
            'build_pk': self.build.pk,
            'domain_pk': self.domain.pk,
        }


class PublicProjectMixin(ProjectMixin):

    url_responses = {
        # Public
        '/projects/search/autocomplete/': {'data': {'term': 'pip'}},
        '/projects/autocomplete/version/pip/': {'data': {'term': 'pip'}},
        '/projects/pip/autocomplete/file/': {'data': {'term': 'pip'}},
        '/projects/pip/downloads/pdf/latest/': {'status_code': 302},
        '/projects/pip/badge/': {'status_code': 302},
    }

    def test_public_urls(self):
        from readthedocs.projects.urls.public import urlpatterns
        self._test_url(urlpatterns)


class PrivateProjectMixin(ProjectMixin):

    def test_private_urls(self):
        from readthedocs.projects.urls.private import urlpatterns
        self._test_url(urlpatterns)

# ## Public Project Testing ###


class PublicProjectAdminAccessTest(PublicProjectMixin, TestCase):

    def login(self):
        return self.client.login(username='owner', password='test')

    def is_admin(self):
        return True


class PublicProjectUserAccessTest(PublicProjectMixin, TestCase):

    def login(self):
        return self.client.login(username='tester', password='test')

    def is_admin(self):
        return False


class PublicProjectUnauthAccessTest(PublicProjectMixin, TestCase):

    def login(self):
        pass

    def is_admin(self):
        return False

# ## Private Project Testing ###


class PrivateProjectAdminAccessTest(PrivateProjectMixin, TestCase):

    url_responses = {
        # Places where we 302 on success -- These delete pages should probably be 405'ing
        '/dashboard/import/manual/demo/': {'status_code': 302},
        '/dashboard/pip/': {'status_code': 302},
        '/dashboard/pip/subprojects/delete/sub/': {'status_code': 302},
        '/dashboard/pip/translations/delete/sub/': {'status_code': 302},

        # This depends on an inactive project
        '/dashboard/pip/version/latest/delete_html/': {'status_code': 400},

        # 405's where we should be POST'ing
        '/dashboard/pip/users/delete/': {'status_code': 405},
        '/dashboard/pip/notifications/delete/': {'status_code': 405},
        '/dashboard/pip/redirects/delete/': {'status_code': 405},
    }

    def login(self):
        return self.client.login(username='owner', password='test')

    def is_admin(self):
        return True


class PrivateProjectUserAccessTest(PrivateProjectMixin, TestCase):

    url_responses = {
        # Auth'd users can import projects, have no perms on pip
        '/dashboard/': {'status_code': 200},
        '/dashboard/import/': {'status_code': 200},
        '/dashboard/import/manual/': {'status_code': 200},
        '/dashboard/import/manual/demo/': {'status_code': 302},
        '/dashboard/import/github/': {'status_code': 200},
        '/dashboard/import/bitbucket/': {'status_code': 200},

        # Unauth access redirect for non-owners
        '/dashboard/pip/': {'status_code': 302},

        # 405's where we should be POST'ing
        '/dashboard/pip/users/delete/': {'status_code': 405},
        '/dashboard/pip/notifications/delete/': {'status_code': 405},
        '/dashboard/pip/redirects/delete/': {'status_code': 405},
    }

    # Filtered out by queryset on projects that we don't own.
    default_status_code = 404

    def login(self):
        return self.client.login(username='tester', password='test')

    def is_admin(self):
        return False


class PrivateProjectUnauthAccessTest(PrivateProjectMixin, TestCase):

    # Auth protected
    default_status_code = 302

    def login(self):
        pass

    def is_admin(self):
        return False
