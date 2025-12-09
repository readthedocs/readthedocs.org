"""Tests for BuildConfig model and Build.readthedocs_yaml_data field."""

import django_dynamic_fixture as fixture
import pytest
from django.db import IntegrityError

from readthedocs.builds.models import Build
from readthedocs.builds.models import BuildConfig
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestBuildConfig:
    """Test BuildConfig model functionality."""

    def test_buildconfig_creation(self):
        """Test that BuildConfig can be created with data."""
        config_data = {"build": {"os": "ubuntu-22.04"}, "python": {"version": "3.11"}}
        build_config = BuildConfig.objects.create(data=config_data)
        
        assert build_config.pk is not None
        assert build_config.data == config_data

    def test_buildconfig_unique_constraint(self):
        """Test that BuildConfig enforces unique constraint on data."""
        config_data = {"build": {"os": "ubuntu-22.04"}, "python": {"version": "3.11"}}
        
        # Create first BuildConfig
        BuildConfig.objects.create(data=config_data)
        
        # Try to create another with the same data - should raise IntegrityError
        with pytest.raises(IntegrityError):
            BuildConfig.objects.create(data=config_data)

    def test_buildconfig_get_or_create(self):
        """Test that get_or_create works correctly for deduplication."""
        config_data = {"build": {"os": "ubuntu-22.04"}, "python": {"version": "3.11"}}
        
        # First call creates
        build_config1, created1 = BuildConfig.objects.get_or_create(data=config_data)
        assert created1 is True
        
        # Second call gets existing
        build_config2, created2 = BuildConfig.objects.get_or_create(data=config_data)
        assert created2 is False
        assert build_config1.pk == build_config2.pk


@pytest.mark.django_db
class TestBuildReadthedocsYamlData:
    """Test Build.readthedocs_yaml_data field and integration."""

    def test_build_saves_with_config_creates_buildconfig(self):
        """Test that saving a Build with config creates BuildConfig."""
        project = fixture.get(Project)
        config_data = {"build": {"os": "ubuntu-22.04"}, "python": {"version": "3.11"}}
        
        build = fixture.get(Build, project=project)
        build.config = config_data
        build.save()
        
        # Check that both old and new fields are populated
        assert build._config == config_data
        assert build.readthedocs_yaml_data is not None
        assert build.readthedocs_yaml_data.data == config_data

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
        assert build1.readthedocs_yaml_data.pk == build2.readthedocs_yaml_data.pk
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
        assert build1.readthedocs_yaml_data.pk != build2.readthedocs_yaml_data.pk
        assert BuildConfig.objects.count() == 2

    def test_build_without_config_does_not_create_buildconfig(self):
        """Test that a Build without config doesn't create a BuildConfig."""
        project = fixture.get(Project)
        build = fixture.get(Build, project=project)
        
        # Build has no config set
        build.save()
        
        assert build._config is None
        assert build.readthedocs_yaml_data is None
        assert BuildConfig.objects.count() == 0

    def test_build_with_config_reference_uses_same_buildconfig(self):
        """Test that a Build with config reference (old style) doesn't create a new BuildConfig."""
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
        
        # build2 should have a reference in _config, not actual data
        assert Build.CONFIG_KEY in build2._config
        # build1 should have created a BuildConfig
        assert build1.readthedocs_yaml_data is not None
        # build2 should not create a new BuildConfig since it uses reference style
        assert build2.readthedocs_yaml_data is None
        # There should only be one BuildConfig created
        assert BuildConfig.objects.count() == 1

    def test_buildconfig_related_builds(self):
        """Test that BuildConfig.builds related manager works."""
        project = fixture.get(Project)
        config_data = {"build": {"os": "ubuntu-22.04"}}
        
        # Create BuildConfig
        build_config = BuildConfig.objects.create(data=config_data)
        
        # Create builds that reference it
        build1 = fixture.get(Build, project=project, readthedocs_yaml_data=build_config)
        build2 = fixture.get(Build, project=project, readthedocs_yaml_data=build_config)
        
        # Check related manager
        assert build_config.builds.count() == 2
        assert build1 in build_config.builds.all()
        assert build2 in build_config.builds.all()
