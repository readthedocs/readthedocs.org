from unittest import mock

import pytest
from django.db.models.query import QuerySet
from django_dynamic_fixture import get

from readthedocs.api.v2.views.integrations import ExternalVersionData
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Version
from readthedocs.core.views.hooks import get_or_create_external_version
from readthedocs.projects.models import Project


@pytest.mark.django_db
def test_concurrent_webhooks_reuse_external_version():
    project = get(Project)
    existing = get(Version, project=project, type=EXTERNAL, verbose_name="2100")
    version_data = ExternalVersionData(
        id="2100", commit="abc123", source_branch="feature", base_branch="main"
    )

    # Simulate another webhook creating the version after our lookup missed it.
    original_get = QuerySet.get
    calls = []

    def racing_get(self, *args, **kwargs):
        if not calls:
            calls.append(1)
            raise Version.DoesNotExist
        return original_get(self, *args, **kwargs)

    with mock.patch.object(QuerySet, "get", racing_get):
        version = get_or_create_external_version(project, version_data)

    assert version.pk == existing.pk
    assert version.identifier == "abc123"
    assert project.versions.filter(type=EXTERNAL, verbose_name="2100").count() == 1
