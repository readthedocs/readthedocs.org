from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.audit.models import AuditLog
from readthedocs.organizations.models import Organization, OrganizationOwner
from readthedocs.projects.models import Project


class TestAuditModels(TestCase):

    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user])
        self.organization = get(Organization, projects=[self.project])
        get(OrganizationOwner, organization=self.organization, owner=self.user)
        self.auditlog = get(
            AuditLog,
            user=self.user,
            project=self.project,
            organization=self.organization,
        )

    def test_user_deletion(self):
        id = self.user.id
        username = self.user.username
        self.user.delete()
        self.auditlog.refresh_from_db()
        self.assertIsNone(self.auditlog.user)
        self.assertEqual(self.auditlog.log_user_id, id)
        self.assertEqual(self.auditlog.log_user_username, username)

    def test_project_deletion(self):
        id = self.project.id
        slug = self.project.slug
        self.project.delete()
        self.auditlog.refresh_from_db()
        self.assertIsNone(self.auditlog.project)
        self.assertEqual(self.auditlog.log_project_id, id)
        self.assertEqual(self.auditlog.log_project_slug, slug)

    def test_organization_deletion(self):
        id = self.organization.id
        slug = self.organization.slug
        self.organization.delete()
        self.auditlog.refresh_from_db()
        self.assertIsNone(self.auditlog.organization)
        self.assertEqual(self.auditlog.log_organization_id, id)
        self.assertEqual(self.auditlog.log_organization_slug, slug)
