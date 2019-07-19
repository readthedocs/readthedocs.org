import pytest

from readthedocs.builds.constants import EXTERNAL
from readthedocs.projects.models import HTMLFile
from readthedocs.search.documents import PageDocument


@pytest.mark.django_db
@pytest.mark.search
class TestPageDocument:

    def test_get_queryset_does_not_include_external_versions(self, project):
        # turn version into PR Version
        version = project.versions.all()[0]
        version.type = EXTERNAL
        version.save()

        html_file = HTMLFile.objects.filter(
            project__slug=project.slug, version=version
        )
        qs = PageDocument().get_queryset()

        assert qs.model == HTMLFile
        assert not set(html_file).issubset(set(qs))
