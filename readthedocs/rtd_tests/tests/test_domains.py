import json

from django.conf import settings
from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.projects.forms import DomainForm
from readthedocs.projects.models import Domain, Project


class ModelTests(TestCase):

    def setUp(self):
        self.project = get(Project, slug='kong')

    def test_save_parsing(self):
        domain = get(Domain, domain='google.com')
        self.assertEqual(domain.domain, 'google.com')

        domain.domain = 'google.com'
        self.assertEqual(domain.domain, 'google.com')

        domain.domain = 'https://google.com'
        domain.save()
        self.assertEqual(domain.domain, 'google.com')

        domain.domain = 'www.google.com'
        domain.save()
        self.assertEqual(domain.domain, 'www.google.com')


class FormTests(TestCase):

    def setUp(self):
        self.project = get(Project, slug='kong')

    def test_https(self):
        """Make sure https is an admin-only attribute."""
        form = DomainForm(
            {'domain': 'example.com', 'canonical': True},
            project=self.project,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertFalse(domain.https)
        form = DomainForm(
            {
                'domain': 'example.com', 'canonical': True,
                'https': True,
            },
            project=self.project,
        )
        self.assertFalse(form.is_valid())

    def test_production_domain_not_allowed(self):
        """Make sure user can not enter production domain name."""
        form = DomainForm(
            {'domain': settings.PRODUCTION_DOMAIN},
            project=self.project,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['domain'][0],
            f'{settings.PRODUCTION_DOMAIN} is not a valid domain.'
        )

        form2 = DomainForm(
            {'domain': 'test.' + settings.PRODUCTION_DOMAIN},
            project=self.project,
        )
        self.assertFalse(form2.is_valid())
        self.assertEqual(
            form2.errors['domain'][0],
            f'{settings.PRODUCTION_DOMAIN} is not a valid domain.'
        )

    @override_settings(PUBLIC_DOMAIN='readthedocs.io')
    def test_public_domain_not_allowed(self):
        """Make sure user can not enter public domain name."""
        form = DomainForm(
            {'domain': settings.PUBLIC_DOMAIN},
            project=self.project,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['domain'][0],
            f'{settings.PUBLIC_DOMAIN} is not a valid domain.'
        )

        form2 = DomainForm(
            {'domain': 'docs.' + settings.PUBLIC_DOMAIN},
            project=self.project,
        )
        self.assertFalse(form2.is_valid())
        self.assertEqual(
            form2.errors['domain'][0],
            f'{settings.PUBLIC_DOMAIN} is not a valid domain.'
        )

    def test_domain_with_path(self):
        form = DomainForm(
            {'domain': 'domain.com/foo/bar'},
            project=self.project,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertEqual(domain.domain, 'domain.com')

    def test_valid_domains(self):
        domains = [
            'python.org',
            'a.io',
            'a.e.i.o.org',
            'my.domain.com.edu',
            'my-domain.fav',
        ]
        for domain in domains:
            form = DomainForm(
                {'domain': domain},
                project=self.project,
            )
            self.assertTrue(form.is_valid(), domain)

    def test_invalid_domains(self):
        domains = [
            'python..org',
            '****.foo.com',
            'domain',
            'domain.com.',
            'My domain.org',
            'i.o',
            '[special].com',
            'some_thing.org',
            'invalid-.com',
        ]
        for domain in domains:
            form = DomainForm(
                {'domain': domain},
                project=self.project,
            )
            self.assertFalse(form.is_valid(), domain)

    def test_canonical_change(self):
        """Make sure canonical can be properly changed."""
        form = DomainForm(
            {'domain': 'example.com', 'canonical': True},
            project=self.project,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertEqual(domain.domain, 'example.com')

        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertEqual(domain.domain, 'example.com')

        form = DomainForm(
            {'domain': 'example2.com', 'canonical': True},
            project=self.project,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['canonical'][0], 'Only one domain can be canonical at a time.')

        form = DomainForm(
            {'canonical': False},
            project=self.project,
            instance=domain,
        )
        self.assertTrue(form.is_valid())
        domain = form.save()
        self.assertEqual(domain.domain, 'example.com')
        self.assertFalse(domain.canonical)


class TestAPI(TestCase):

    def setUp(self):
        self.project = get(Project)
        self.domain = self.project.domains.create(domain='djangokong.com')

    def test_basic_api(self):
        resp = self.client.get('/api/v2/domain/')
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['results'][0]['domain'], 'djangokong.com')
        self.assertEqual(obj['results'][0]['canonical'], False)
        self.assertNotIn('https', obj['results'][0])
