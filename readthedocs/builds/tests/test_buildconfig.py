"""Tests for BuildConfig model and Build.readthedocs_yaml_config field."""

import django_dynamic_fixture as fixture
import pytest

from readthedocs.builds.models import Build
from readthedocs.builds.models import BuildConfig
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestBuildReadthedocsYamlData:
    """Test Build.readthedocs_yaml_config field and integration."""

    def test_build_saves_with_config_creates_buildconfig(self):
        """Test that saving a Build with config creates BuildConfig."""
        project = fixture.get(Project)
        config_data = {"build": {"os": "ubuntu-22.04"}, "python": {"version": "3.11"}}

        build = fixture.get(Build, project=project)
        build.config = config_data
        build.save()

        assert BuildConfig.objects.count() == 1
        assert BuildConfig.objects.filter(data=config_data).count() == 1

        build.refresh_from_db()
        assert build.readthedocs_yaml_config.data == config_data

    def test_build_with_same_config_reuses_buildconfig(self):
        """Test that builds with same config reuse the same BuildConfig."""
        project = fixture.get(Project)
        config_data = {"build": {"os": "ubuntu-22.04"}, "python": {"version": "3.11"}}

        # Create first build
        build1 = fixture.get(Build, project=project)
        build1.config = config_data
        build1.save()

        # Create second build with same config
        build2 = fixture.get(Build, project=project)
        build2.config = config_data
        build2.save()

        # Both should reference the same BuildConfig
        assert build1.readthedocs_yaml_config.pk == build2.readthedocs_yaml_config.pk
        assert BuildConfig.objects.count() == 1

    def test_build_with_different_config_creates_new_buildconfig(self):
        """Test that builds with different configs create separate BuildConfigs."""
        project = fixture.get(Project)
        config_data1 = {"build": {"os": "ubuntu-22.04"}, "python": {"version": "3.11"}}
        config_data2 = {"build": {"os": "ubuntu-20.04"}, "python": {"version": "3.10"}}

        # Create first build
        build1 = fixture.get(Build, project=project)
        build1.config = config_data1
        build1.save()

        # Create second build with different config
        build2 = fixture.get(Build, project=project)
        build2.config = config_data2
        build2.save()

        # Should have different BuildConfigs
        assert build1.readthedocs_yaml_config.pk != build2.readthedocs_yaml_config.pk
        assert BuildConfig.objects.count() == 2

    def test_build_without_config_does_not_create_buildconfig(self):
        """Test that a Build without config doesn't create a BuildConfig."""
        project = fixture.get(Project)
        build = fixture.get(Build, project=project)

        # Build has no config set
        build.save()

        assert build.readthedocs_yaml_config is None
        assert BuildConfig.objects.count() == 0

    def test_build_with_config_reference_uses_same_buildconfig(self):
        """Test that a Build with config reference (old style) reuses the same BuildConfig."""
        project = fixture.get(Project)
        version = fixture.get(Version, project=project)
        config_data = {"build": {"os": "ubuntu-22.04"}}

        # Create a build with actual config
        build1 = fixture.get(Build, project=project, version=version)
        build1.config = config_data
        build1.save()

        # Create a build with same config on the same version
        # (which will use the reference style in _config)
        build2 = fixture.get(Build, project=project, version=version)
        build2.config = config_data
        build2.save()

        # Both builds should have the same BuildConfig
        assert build1.readthedocs_yaml_config is not None
        assert build2.readthedocs_yaml_config is not None
        assert build1.readthedocs_yaml_config.pk == build2.readthedocs_yaml_config.pk
        # There should only be one BuildConfig created
        assert BuildConfig.objects.count() == 1
