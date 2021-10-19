from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.organizations.models import Organization, Team, TeamInvite
from readthedocs.rtd_tests.tests.test_privacy_urls import URLAccessMixin


class OrganizationMixin(URLAccessMixin):

    def setUp(self):
        super().setUp()
        self.user = get(User)
        self.member = get(User)
        self.organization = get(Organization, owners=[self.user])
        self.org_owner = self.organization.owners.first()
        self.team = get(Team, organization=self.organization, members=[self.member])
        self.team_member = self.team.members.first()
        self.invite = get(TeamInvite, organization=self.organization, team=self.team)
        self.default_kwargs.update(
            {
                'slug': self.organization.slug,
                'team': self.team.slug,
                'hash': self.invite.hash,
                'owner': self.org_owner.pk,
                'member': self.team_member.pk,
            }
        )

        self.another_user = get(User)

    def get_url_path_ctx(self):
        return self.default_kwargs


@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
class NoOrganizationsTest(OrganizationMixin, TestCase):

    """Organization views aren't available if organizations aren't allowed."""

    default_status_code = 404

    def login(self):
        return self.client.force_login(self.user)

    def test_public_urls(self):
        from readthedocs.organizations.urls.public import urlpatterns
        self._test_url(urlpatterns)

    def test_private_urls(self):
        from readthedocs.organizations.urls.private import urlpatterns
        self._test_url(urlpatterns)


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class AuthUserOrganizationsTest(OrganizationMixin, TestCase):

    """All views are available for the owner of the organization."""

    response_data = {
        # Places where we 302 on success.
        '/organizations/invite/{hash}/redeem/': {'status_code': 302},

        # 405's where we should be POST'ing
        '/organizations/{slug}/owners/{owner}/delete/': {'status_code': 405},
        '/organizations/{slug}/teams/{team}/members/{member}/revoke/': {'status_code': 405},
    }

    def login(self):
        self.client.force_login(self.user)

    def test_public_urls(self):
        from readthedocs.organizations.urls.public import urlpatterns
        self._test_url(urlpatterns)

    def test_private_urls(self):
        from readthedocs.organizations.urls.private import urlpatterns
        self._test_url(urlpatterns)


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    ALLOW_PRIVATE_REPOS=False,
)
class AnonymousUserWithPublicOrganizationsTest(OrganizationMixin, TestCase):

    """If organizations are public, an anonymous user can access the public views."""

    response_data = {
        # Places where we 302 on success.
        '/organizations/invite/{hash}/redeem/': {'status_code': 302},
    }

    def login(self):
        pass

    def test_public_urls(self):
        from readthedocs.organizations.urls.public import urlpatterns
        self._test_url(urlpatterns)


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    ALLOW_PRIVATE_REPOS=True,
)
class AnonymousUserWithPrivateOrganizationsTest(OrganizationMixin, TestCase):

    """If organizations are private, an anonymous user can't access the public views."""

    default_status_code = 404
    response_data = {
        # Places where we 302 on success.
        '/organizations/invite/{hash}/redeem/': {'status_code': 302},
    }

    def login(self):
        pass

    def test_public_urls(self):
        from readthedocs.organizations.urls.public import urlpatterns
        self._test_url(urlpatterns)


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    ALLOW_PRIVATE_REPOS=False,
)
class AnonymousUserWithPublicOrganizationsPrivateViewsTest(OrganizationMixin, TestCase):

    """If organizations are public, an anonymous user can't access the private views."""

    # We get redirected to the login page.
    default_status_code = 302

    def login(self):
        pass

    def test_private_urls(self):
        from readthedocs.organizations.urls.private import urlpatterns
        self._test_url(urlpatterns)


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    ALLOW_PRIVATE_REPOS=True,
)
class AnonymousUserWithPrivateOrganizationsPrivateViewsTest(OrganizationMixin, TestCase):

    """If organizations are private, an anonymous user can't access the private views."""

    # We get redirected to the login page.
    default_status_code = 302

    def login(self):
        pass

    def test_private_urls(self):
        from readthedocs.organizations.urls.private import urlpatterns
        self._test_url(urlpatterns)


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    ALLOW_PRIVATE_REPOS=False,
)
class AnotherUserWithPublicOrganizationsTest(OrganizationMixin, TestCase):

    """If organizations are public, an user outside the organization can access the public views."""

    response_data = {
        # Places where we 302 on success.
        '/organizations/invite/{hash}/redeem/': {'status_code': 302},
    }

    def login(self):
        self.client.force_login(self.another_user)

    def test_public_urls(self):
        from readthedocs.organizations.urls.public import urlpatterns
        self._test_url(urlpatterns)


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    ALLOW_PRIVATE_REPOS=True,
)
class AnotherUserWithPrivateOrganizationsTest(OrganizationMixin, TestCase):

    """If organizations are private, an user outside the organization can't access the public views."""

    default_status_code = 404
    response_data = {
        # Places where we 302 on success.
        '/organizations/invite/{hash}/redeem/': {'status_code': 302},
    }

    def login(self):
        self.client.force_login(self.another_user)

    def test_public_urls(self):
        from readthedocs.organizations.urls.public import urlpatterns
        self._test_url(urlpatterns)


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    ALLOW_PRIVATE_REPOS=False,
)
class AnotherUserWithPublicOrganizationsPrivateViewsTest(OrganizationMixin, TestCase):

    """If organizations are public, an user outside the organization can access the public views."""

    default_status_code = 404
    response_data = {
        # All users have access to these views.
        '/organizations/': {'status_code': 200},
        '/organizations/create/': {'status_code': 200},
        '/organizations/verify-email/': {'status_code': 200},

        # 405's where we should be POST'ing
        '/organizations/{slug}/owners/{owner}/delete/': {'status_code': 405},
        '/organizations/{slug}/teams/{team}/members/{member}/revoke/': {'status_code': 405},
    }

    def login(self):
        self.client.force_login(self.another_user)

    def test_private_urls(self):
        from readthedocs.organizations.urls.private import urlpatterns
        self._test_url(urlpatterns)


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=True,
    ALLOW_PRIVATE_REPOS=True,
)
class AnotherUserWithPrivateOrganizationsPrivateViewsTest(OrganizationMixin, TestCase):

    """If organizations are private, an user outside the organization can't access the private views."""

    default_status_code = 404
    response_data = {
        # All users have access to these views.
        '/organizations/': {'status_code': 200},
        '/organizations/create/': {'status_code': 200},
        '/organizations/verify-email/': {'status_code': 200},

        # 405's where we should be POST'ing
        '/organizations/{slug}/owners/{owner}/delete/': {'status_code': 405},
        '/organizations/{slug}/teams/{team}/members/{member}/revoke/': {'status_code': 405},
    }

    def login(self):
        self.client.force_login(self.another_user)

    def test_private_urls(self):
        from readthedocs.organizations.urls.private import urlpatterns
        self._test_url(urlpatterns)
