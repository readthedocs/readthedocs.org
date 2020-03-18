import logging

from unittest import mock
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.projects.forms import UpdateProjectForm
from readthedocs.projects.models import Project


log = logging.getLogger(__name__)


@mock.patch('readthedocs.projects.tasks.clean_build', new=mock.MagicMock)
@mock.patch('readthedocs.projects.tasks.update_docs_task.signature', new=mock.MagicMock)
class PrivacyTests(TestCase):

    def setUp(self):
        self.eric = User(username='eric')
        self.eric.set_password('test')
        self.eric.save()

        self.tester = User(username='tester')
        self.tester.set_password('test')
        self.tester.save()

    def _create_kong(
        self, privacy_level='private',
        version_privacy_level='private',
    ):
        self.client.login(username='eric', password='test')
        log.info(
            'Making kong with privacy: %s and version privacy: %s',
            privacy_level,
            version_privacy_level,
        )
        # Create project via project form, simulate import wizard without magic
        form = UpdateProjectForm(
            data={
                'repo_type': 'git',
                'repo': 'https://github.com/ericholscher/django-kong',
                'name': 'Django Kong',
                'language': 'en',
                'default_branch': '',
                'project_url': 'http://django-kong.rtfd.org',
                'default_version': LATEST,
                'python_interpreter': 'python',
                'description': 'OOHHH AH AH AH KONG SMASH',
                'documentation_type': 'sphinx',
            },
            user=User.objects.get(username='eric'),
        )
        proj = form.save()
        # Update these directly, no form has all the fields we need
        proj.privacy_level = privacy_level
        proj.version_privacy_level = version_privacy_level
        proj.save()

        latest = proj.versions.get(slug='latest')
        latest.privacy_level = version_privacy_level
        latest.save()

        self.assertAlmostEqual(Project.objects.count(), 1)
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 200)
        return Project.objects.get(slug='django-kong')

    def test_private_repo(self):
        """Check that private projects don't show up in: builds, downloads,
        detail, homepage

        """
        self._create_kong('private', 'private')

        self.client.login(username='eric', password='test')
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 200)
        # Build button should appear here
        self.assertContains(r, 'Build a version')
        r = self.client.get('/projects/django-kong/builds/')
        self.assertEqual(r.status_code, 200)
        # Build button should appear here
        self.assertContains(r, 'Build Version:')
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)

        self.client.login(username='tester', password='test')
        r = self.client.get('/')
        self.assertNotContains(r, 'Django Kong')
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 404)
        r = self.client.get('/projects/django-kong/builds/')
        self.assertEqual(r.status_code, 404)
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 404)

    def test_public_repo(self):
        """Check that public projects show up in: builds, downloads, detail,
        homepage

        """
        self._create_kong('public', 'public')

        self.client.login(username='eric', password='test')
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 200)
        # Build button should appear here
        self.assertContains(r, 'Build a version')
        r = self.client.get('/projects/django-kong/builds/')
        self.assertEqual(r.status_code, 200)
        # Build button should appear here
        self.assertContains(r, 'Build Version:')
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)

        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/')
        self.assertEqual(r.status_code, 200)
        # Build button shouldn't appear here
        self.assertNotContains(r, 'Build a version')
        r = self.client.get('/projects/django-kong/builds/')
        self.assertEqual(r.status_code, 200)
        # Build button shouldn't appear here
        self.assertNotContains(r, 'Build Version:')
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)

    def test_private_branch(self):
        kong = self._create_kong('public', 'private')

        self.client.login(username='eric', password='test')
        Version.objects.create(
            project=kong, identifier='test id',
            verbose_name='test verbose', privacy_level='private', slug='test-slug', active=True,
        )
        self.assertEqual(Version.objects.count(), 2)
        self.assertEqual(Version.objects.get(slug='test-slug').privacy_level, 'private')
        r = self.client.get('/projects/django-kong/')
        self.assertContains(r, 'test-slug')
        r = self.client.get('/projects/django-kong/builds/')
        self.assertContains(r, 'test-slug')

        # Make sure it doesn't show up as tester
        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/')
        self.assertNotContains(r, 'test-slug')
        r = self.client.get('/projects/django-kong/builds/')
        self.assertNotContains(r, 'test-slug')

    def test_public_branch(self):
        kong = self._create_kong('public', 'public')

        self.client.login(username='eric', password='test')
        Version.objects.create(
            project=kong, identifier='test id',
            verbose_name='test verbose', slug='test-slug',
            active=True, built=True,
        )
        self.assertEqual(Version.objects.count(), 2)
        self.assertEqual(Version.objects.all()[0].privacy_level, 'public')
        r = self.client.get('/projects/django-kong/')
        self.assertContains(r, 'test-slug')

        # Make sure it does show up as tester
        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/')
        self.assertContains(r, 'test-slug')

    def test_private_doc_serving(self):
        kong = self._create_kong('public', 'private')

        self.client.login(username='eric', password='test')
        Version.objects.create(
            project=kong, identifier='test id',
            verbose_name='test verbose', privacy_level='private', slug='test-slug', active=True,
        )
        self.client.post(
            '/dashboard/django-kong/versions/',
            {
                'version-test-slug': 'on',
                'privacy-test-slug': 'private',
            },
        )
        r = self.client.get('/docs/django-kong/en/test-slug/')
        self.client.login(username='eric', password='test')
        self.assertEqual(r.status_code, 404)

        # Make sure it doesn't show up as tester
        self.client.login(username='tester', password='test')
        r = self.client.get('/docs/django-kong/en/test-slug/')
        self.assertEqual(r.status_code, 401)

# Private download tests

    @override_settings(DEFAULT_PRIVACY_LEVEL='private')
    def test_private_repo_downloading(self):
        self._create_kong('private', 'private')

        # Unauth'd user
        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 404)
        r = self.client.get('/projects/django-kong/downloads/pdf/latest/')
        self.assertEqual(r.status_code, 404)

        # Auth'd user
        self.client.login(username='eric', password='test')
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/downloads/pdf/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/pdf/django-kong/latest/django-kong.pdf')

    @override_settings(DEFAULT_PRIVACY_LEVEL='private')
    def test_private_public_repo_downloading(self):
        self._create_kong('public', 'public')

        # Unauth'd user
        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/downloads/pdf/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/pdf/django-kong/latest/django-kong.pdf')

        # Auth'd user
        self.client.login(username='eric', password='test')
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/downloads/pdf/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/pdf/django-kong/latest/django-kong.pdf')

    @override_settings(
        DEFAULT_PRIVACY_LEVEL='private',
        PUBLIC_DOMAIN='readthedocs.io',
        USE_SUBDOMAIN=True,
    )
    def test_private_download_filename(self):
        self._create_kong('private', 'private')

        self.client.login(username='eric', password='test')
        r = self.client.get('/projects/django-kong/downloads/pdf/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/pdf/django-kong/latest/django-kong.pdf')
        self.assertEqual(r._headers['content-disposition'][1], 'filename=django-kong-readthedocs-io-en-latest.pdf')

        r = self.client.get('/projects/django-kong/downloads/epub/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/epub/django-kong/latest/django-kong.epub')
        self.assertEqual(r._headers['content-disposition'][1], 'filename=django-kong-readthedocs-io-en-latest.epub')

        r = self.client.get('/projects/django-kong/downloads/htmlzip/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/htmlzip/django-kong/latest/django-kong.zip')
        self.assertEqual(r._headers['content-disposition'][1], 'filename=django-kong-readthedocs-io-en-latest.zip')

# Public download tests
    @override_settings(
        DEFAULT_PRIVACY_LEVEL='public',
        PUBLIC_DOMAIN='readthedocs.io',
        USE_SUBDOMAIN=True,
    )
    def test_public_repo_downloading(self):
        self._create_kong('public', 'public')

        # Unauth'd user
        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/downloads/pdf/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/pdf/django-kong/latest/django-kong.pdf')
        self.assertEqual(r._headers['content-disposition'][1], 'filename=django-kong-readthedocs-io-en-latest.pdf')

        # Auth'd user
        self.client.login(username='eric', password='test')
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/downloads/pdf/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/pdf/django-kong/latest/django-kong.pdf')
        self.assertEqual(r._headers['content-disposition'][1], 'filename=django-kong-readthedocs-io-en-latest.pdf')

    @override_settings(
        DEFAULT_PRIVACY_LEVEL='public',
        PUBLIC_DOMAIN='readthedocs.io',
        USE_SUBDOMAIN=True,
    )
    def test_public_private_repo_downloading(self):
        self._create_kong('private', 'private')

        # Unauth'd user
        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 404)
        r = self.client.get('/projects/django-kong/downloads/pdf/latest/')
        self.assertEqual(r.status_code, 404)

        # Auth'd user
        self.client.login(username='eric', password='test')
        r = self.client.get('/projects/django-kong/downloads/')
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/projects/django-kong/downloads/pdf/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/pdf/django-kong/latest/django-kong.pdf')
        self.assertEqual(r._headers['content-disposition'][1], 'filename=django-kong-readthedocs-io-en-latest.pdf')

    @override_settings(
        DEFAULT_PRIVACY_LEVEL='public',
        PUBLIC_DOMAIN='readthedocs.io',
        USE_SUBDOMAIN=True,
    )
    def test_public_download_filename(self):
        self._create_kong('public', 'public')

        self.client.login(username='eric', password='test')
        r = self.client.get('/projects/django-kong/downloads/pdf/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/pdf/django-kong/latest/django-kong.pdf')
        self.assertEqual(r._headers['content-disposition'][1], 'filename=django-kong-readthedocs-io-en-latest.pdf')

        r = self.client.get('/projects/django-kong/downloads/epub/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/epub/django-kong/latest/django-kong.epub')
        self.assertEqual(r._headers['content-disposition'][1], 'filename=django-kong-readthedocs-io-en-latest.epub')

        r = self.client.get('/projects/django-kong/downloads/htmlzip/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r._headers['x-accel-redirect'][1], '/proxito/media/htmlzip/django-kong/latest/django-kong.zip')
        self.assertEqual(r._headers['content-disposition'][1], 'filename=django-kong-readthedocs-io-en-latest.zip')

# Build Filtering

    def test_build_filtering(self):
        kong = self._create_kong('public', 'private')

        self.client.login(username='eric', password='test')
        ver = Version.objects.create(
            project=kong, identifier='test id',
            verbose_name='test verbose', privacy_level='private', slug='test-slug', active=True,
        )

        r = self.client.get('/projects/django-kong/builds/')
        self.assertContains(r, 'test-slug')

        Build.objects.create(project=kong, version=ver)
        r = self.client.get('/projects/django-kong/builds/')
        self.assertContains(r, 'test-slug')

        # Make sure it doesn't show up as tester
        self.client.login(username='tester', password='test')
        r = self.client.get('/projects/django-kong/builds/')
        self.assertNotContains(r, 'test-slug')

    def test_queryset_chaining(self):
        """Test that manager methods get set on related querysets."""
        kong = self._create_kong('public', 'private')
        self.assertEqual(
            kong.versions.private().get(slug='latest').slug,
            'latest',
        )
