import django_dynamic_fixture as fixture
from allauth.socialaccount.models import SocialAccount
from django import urls
from django.contrib.auth.models import User
from django.test import TestCase

from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.models import RemoteRepositoryRelation
from readthedocs.projects.models import Project


class OAuthAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = fixture.get(User, is_staff=True, is_superuser=True)
        cls.user = fixture.get(User, username="owner")
        cls.account = fixture.get(
            SocialAccount,
            user=cls.user,
            provider="github",
            uid="owner-account",
        )
        cls.remote_repository = fixture.get(
            RemoteRepository,
            name="zephyrdocs",
            full_name="organization/zephyrdocs",
            remote_id="100",
            html_url=None,
        )
        cls.other_remote_repository = fixture.get(
            RemoteRepository,
            name="telescope",
            full_name="organization/telescope",
            remote_id="101",
            html_url=None,
        )
        cls.project = fixture.get(
            Project,
            slug="manualhub",
            name="Manualhub",
            remote_repository=cls.remote_repository,
            main_language_project=None,
        )
        cls.other_project = fixture.get(
            Project,
            slug="telescopeapi",
            name="Telescopeapi",
            remote_repository=cls.other_remote_repository,
            main_language_project=None,
        )
        cls.remote_repository_relation = fixture.get(
            RemoteRepositoryRelation,
            remote_repository=cls.remote_repository,
            user=cls.user,
            account=cls.account,
            admin=True,
        )
        cls.other_user = fixture.get(User, username="other-owner")
        cls.other_account = fixture.get(
            SocialAccount,
            user=cls.other_user,
            provider="github",
            uid="other-account",
        )
        cls.other_remote_repository_relation = fixture.get(
            RemoteRepositoryRelation,
            remote_repository=cls.other_remote_repository,
            user=cls.other_user,
            account=cls.other_account,
            admin=False,
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_remote_repository_admin_searches_by_project_slug(self):
        response = self.client.get(
            urls.reverse("admin:oauth_remoterepository_changelist"),
            {"q": self.project.slug},
        )

        self.assertContains(response, self.remote_repository.full_name)
        self.assertNotContains(response, self.other_remote_repository.full_name)

    def test_remote_repository_change_view_links_to_filtered_relations(self):
        response = self.client.get(
            urls.reverse(
                "admin:oauth_remoterepository_change",
                args=[self.remote_repository.pk],
            ),
        )

        changelist_url = urls.reverse("admin:oauth_remoterepositoryrelation_changelist")
        self.assertContains(
            response,
            f'{changelist_url}?remote_repository__id__exact={self.remote_repository.pk}',
        )
        self.assertContains(response, "1 remote repository relation")

    def test_remote_repository_relation_admin_searches_by_project_name(self):
        response = self.client.get(
            urls.reverse("admin:oauth_remoterepositoryrelation_changelist"),
            {"q": self.project.name},
        )

        self.assertContains(response, self.remote_repository.full_name)
        self.assertNotContains(response, self.other_remote_repository.full_name)

    def test_remote_repository_relation_admin_searches_by_remote_repository(self):
        response = self.client.get(
            urls.reverse("admin:oauth_remoterepositoryrelation_changelist"),
            {"q": self.remote_repository.name},
        )

        self.assertContains(response, self.remote_repository.full_name)
        self.assertNotContains(response, self.other_remote_repository.full_name)
