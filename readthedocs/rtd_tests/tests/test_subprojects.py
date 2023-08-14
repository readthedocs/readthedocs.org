import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase

from readthedocs.projects.forms import ProjectRelationshipForm
from readthedocs.projects.models import Project, ProjectRelationship


class SubprojectFormTests(TestCase):
    def setUp(self):
        self.user = fixture.get(User)
        self.project = fixture.get(Project, users=[self.user])
        self.subproject = fixture.get(Project, users=[self.user])
        self.project.add_subproject(self.subproject, "subproject")
        self.relation = self.subproject.superprojects.first()

    def test_empty_child(self):
        user = fixture.get(User)
        project = fixture.get(Project, slug="mainproject")
        form = ProjectRelationshipForm(
            {},
            project=project,
            user=user,
        )
        form.full_clean()
        self.assertEqual(len(form.errors["child"]), 1)
        self.assertRegex(
            form.errors["child"][0],
            r"This field is required.",
        )

    def test_nonexistent_child(self):
        user = fixture.get(User)
        project = fixture.get(Project, slug="mainproject")
        self.assertFalse(Project.objects.filter(pk=9999).exists())
        form = ProjectRelationshipForm(
            {"child": 9999},
            project=project,
            user=user,
        )
        form.full_clean()
        self.assertEqual(len(form.errors["child"]), 1)
        self.assertRegex(
            form.errors["child"][0],
            r"Select a valid choice.",
        )

    def test_adding_subproject_fails_when_user_is_not_admin(self):
        user = fixture.get(User)
        project = fixture.get(Project, slug="mainproject")
        project.users.add(user)
        subproject = fixture.get(Project, slug="subproject")
        self.assertQuerySetEqual(
            Project.objects.for_admin_user(user),
            [project],
            transform=lambda n: n,
            ordered=False,
        )
        form = ProjectRelationshipForm(
            {"child": subproject.pk},
            project=project,
            user=user,
        )
        form.full_clean()
        self.assertEqual(len(form.errors["child"]), 1)
        self.assertRegex(
            form.errors["child"][0],
            r"Select a valid choice.",
        )
        self.assertEqual(
            [proj_id for (proj_id, _) in form.fields["child"].choices],
            [""],
        )

    def test_adding_subproject_passes_when_user_is_admin(self):
        user = fixture.get(User)
        project = fixture.get(Project, slug="mainproject")
        project.users.add(user)
        subproject = fixture.get(Project, slug="subproject")
        subproject.users.add(user)
        self.assertQuerySetEqual(
            Project.objects.for_admin_user(user),
            [project, subproject],
            transform=lambda n: n,
            ordered=False,
        )
        form = ProjectRelationshipForm(
            {"child": subproject.pk},
            project=project,
            user=user,
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(
            [r.child for r in project.subprojects.all()],
            [subproject],
        )

    def test_subproject_form_cant_create_sub_sub_project(self):
        user = fixture.get(User)
        project = fixture.get(Project, users=[user])
        subproject = fixture.get(Project, users=[user])
        subsubproject = fixture.get(Project, users=[user])
        relation = fixture.get(
            ProjectRelationship,
            parent=project,
            child=subproject,
        )
        self.assertQuerySetEqual(
            Project.objects.for_admin_user(user),
            [project, subproject, subsubproject],
            transform=lambda n: n,
            ordered=False,
        )
        form = ProjectRelationshipForm(
            {"child": subsubproject.pk},
            project=subproject,
            user=user,
        )
        # The subsubproject is valid here, as far as the child check is
        # concerned, but the parent check should fail.
        self.assertEqual(
            [proj_id for (proj_id, _) in form.fields["child"].choices],
            ["", subsubproject.pk],
        )
        form.full_clean()
        self.assertEqual(len(form.errors["parent"]), 1)
        self.assertRegex(
            form.errors["parent"][0],
            r"Subproject nesting is not supported",
        )

    def test_excludes_existing_subprojects(self):
        user = fixture.get(User)
        project = fixture.get(Project, users=[user])
        subproject = fixture.get(Project, users=[user])
        relation = fixture.get(
            ProjectRelationship,
            parent=project,
            child=subproject,
        )
        self.assertQuerySetEqual(
            Project.objects.for_admin_user(user),
            [project, subproject],
            transform=lambda n: n,
            ordered=False,
        )
        form = ProjectRelationshipForm(
            {"child": subproject.pk},
            project=project,
            user=user,
        )
        self.assertEqual(
            [proj_id for (proj_id, _) in form.fields["child"].choices],
            [""],
        )

    def test_subproject_cant_be_subproject(self):
        user = fixture.get(User)
        project = fixture.get(Project, users=[user])
        another_project = fixture.get(Project, users=[user])
        subproject = fixture.get(Project, users=[user])
        relation = fixture.get(
            ProjectRelationship,
            parent=project,
            child=subproject,
        )

        form = ProjectRelationshipForm(
            {"child": subproject.pk},
            project=project,
            user=user,
        )
        self.assertFalse(form.is_valid())
        self.assertRegex(
            form.errors["child"][0],
            "Select a valid choice",
        )

        form = ProjectRelationshipForm(
            {"child": subproject.pk},
            project=another_project,
            user=user,
        )
        self.assertFalse(form.is_valid())
        self.assertRegex(
            form.errors["child"][0],
            "Select a valid choice",
        )

    def test_superproject_cant_be_subproject(self):
        user = fixture.get(User)
        project = fixture.get(Project, users=[user])
        another_project = fixture.get(Project, users=[user])
        subproject = fixture.get(Project, users=[user])
        relation = fixture.get(
            ProjectRelationship,
            parent=project,
            child=subproject,
        )

        form = ProjectRelationshipForm(
            {"child": project.pk},
            project=another_project,
            user=user,
        )
        self.assertFalse(form.is_valid())
        self.assertRegex(
            form.errors["child"][0],
            "Select a valid choice",
        )

    def test_exclude_self_project_as_subproject(self):
        user = fixture.get(User)
        project = fixture.get(Project, users=[user])

        form = ProjectRelationshipForm(
            {"child": project.pk},
            project=project,
            user=user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Select a valid choice",
            form.errors["child"][0],
        )
        self.assertNotIn(
            project.id,
            [proj_id for (proj_id, __) in form.fields["child"].choices],
        )

    def test_alias_already_exists_for_a_project(self):
        user = fixture.get(User)
        project = fixture.get(Project, users=[user])
        subproject = fixture.get(Project, users=[user])
        subproject_2 = fixture.get(Project, users=[user])
        relation = fixture.get(
            ProjectRelationship, parent=project, child=subproject, alias="subproject"
        )
        form = ProjectRelationshipForm(
            {"child": subproject_2.id, "alias": "subproject"},
            project=project,
            user=user,
        )
        self.assertFalse(form.is_valid())
        error_msg = "A subproject with this alias already exists"
        self.assertDictEqual(form.errors, {"alias": [error_msg]})

    def test_edit_only_lists_instance_project_in_child_choices(self):
        user = fixture.get(User)
        project = fixture.get(Project, users=[user])
        subproject = fixture.get(Project, users=[user])
        relation = fixture.get(
            ProjectRelationship, parent=project, child=subproject, alias="subproject"
        )
        form = ProjectRelationshipForm(
            instance=relation,
            project=project,
            user=user,
        )
        self.assertEqual(
            [proj_id for (proj_id, __) in form.fields["child"].choices],
            ["", relation.child.id],
        )

    def test_change_alias(self):
        subproject_2 = fixture.get(Project, users=[self.user])
        self.project.add_subproject(subproject_2, "another-subproject")

        relation = subproject_2.superprojects.first()

        # Change alias to an existing alias
        form = ProjectRelationshipForm(
            {"child": subproject_2.id, "alias": "subproject"},
            instance=relation,
            project=self.project,
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        error_msg = "A subproject with this alias already exists"
        self.assertDictEqual(form.errors, {"alias": [error_msg]})

        # Change alias to a new alias
        form = ProjectRelationshipForm(
            {"child": subproject_2.id, "alias": "other-subproject"},
            instance=relation,
            project=self.project,
            user=self.user,
        )
        self.assertTrue(form.is_valid())
        form.save()
        relation.refresh_from_db()
        self.assertEqual(relation.alias, "other-subproject")

    def test_change_alias_to_same_alias(self):
        form = ProjectRelationshipForm(
            {"child": self.subproject.id, "alias": "subproject"},
            instance=self.relation,
            project=self.project,
            user=self.user,
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.relation.refresh_from_db()
        self.assertEqual(self.relation.alias, "subproject")
