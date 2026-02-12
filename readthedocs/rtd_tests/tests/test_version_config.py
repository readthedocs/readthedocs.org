from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_BUILDING, BUILD_STATE_FINISHED
from readthedocs.builds.models import Build, Version, BuildConfig
from readthedocs.projects.models import Project


class VersionConfigTests(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, project=self.project)

    def test_get_correct_config(self):
        bc1 = BuildConfig.objects.create(data={"version": 1})
        bc2 = BuildConfig.objects.create(data={"version": 2})
        bc3 = BuildConfig.objects.create(data={"version": 3})
        bc4 = BuildConfig.objects.create(data={"version": 4})

        build_old = Build.objects.create(
            project=self.project,
            version=self.version,
            readthedocs_yaml_config=bc1,
            state=BUILD_STATE_FINISHED,
        )
        build_new = Build.objects.create(
            project=self.project,
            version=self.version,
            readthedocs_yaml_config=bc2,
            state=BUILD_STATE_FINISHED,
        )
        build_new_error = Build.objects.create(
            project=self.project,
            version=self.version,
            success=False,
            readthedocs_yaml_config=bc3,
            state=BUILD_STATE_FINISHED,
        )
        build_new_unfinish = Build.objects.create(
            project=self.project,
            version=self.version,
            readthedocs_yaml_config=bc4,
            state=BUILD_STATE_BUILDING,
        )
        self.assertEqual(self.version.config, {"version": 2})

    def test_get_correct_config_when_same_config(self):
        build_old = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_FINISHED,
        )
        build_old.config = {"version": 1}
        build_old.save()

        build_new = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_FINISHED,
        )
        build_new.config = {"version": 1}
        build_new.save()

        build_new_error = get(
            Build,
            project=self.project,
            version=self.version,
            success=False,
            state=BUILD_STATE_FINISHED,
        )
        build_new_error.config = {"version": 3}
        build_new_error.save()

        build_new_unfinish = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_BUILDING,
        )
        build_new_unfinish.config = {"version": 1}
        build_new_unfinish.save()

        config = self.version.config
        self.assertEqual(config, {"version": 1})
