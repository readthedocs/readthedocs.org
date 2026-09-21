import django_filters.rest_framework as filters
from django.db.models import BooleanField
from django.db.models import Exists
from django.db.models import ExpressionWrapper
from django.db.models import OuterRef
from django.db.models import Q

from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.notifications.models import Notification
from readthedocs.oauth.models import RemoteOrganization
from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects.models import Project


class ProjectFilter(filters.FilterSet):
    # TODO this is copying the patterns from other filter sets, where the fields
    # are all ``icontains`` lookups by default. We discussed reversing this
    # pattern in the future though, see:
    # https://github.com/readthedocs/readthedocs.org/issues/9862
    name = filters.CharFilter(lookup_expr="icontains")
    slug = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Project
        fields = [
            "name",
            "slug",
            "language",
            "programming_language",
        ]


class VersionFilter(filters.FilterSet):
    slug = filters.CharFilter(lookup_expr="icontains")
    verbose_name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Version
        fields = [
            "verbose_name",
            "privacy_level",
            "active",
            "built",
            "uploaded",
            "slug",
            "type",
        ]


class BuildFilter(filters.FilterSet):
    running = filters.BooleanFilter(method="get_running")

    class Meta:
        model = Build
        fields = [
            "commit",
            "running",
        ]

    def get_running(self, queryset, name, value):
        if value:
            return queryset.exclude(state__in=BUILD_FINAL_STATES)

        return queryset.filter(state__in=BUILD_FINAL_STATES)


class NotificationFilter(filters.FilterSet):
    class Meta:
        model = Notification
        fields = {
            "state": ["in", "exact"],
        }


class RemoteRepositoryFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    full_name = filters.CharFilter(field_name="full_name", lookup_expr="icontains")
    organization = filters.CharFilter(field_name="organization__slug")
    ordering = filters.ChoiceFilter(
        label="Ordering",
        choices=[("import", "Repositories most likely to be imported first")],
        method="order_repositories",
    )

    class Meta:
        model = RemoteRepository
        fields = [
            "name",
            "full_name",
            "vcs_provider",
            "organization",
        ]

    def order_repositories(self, queryset, name, value):
        """
        Order repositories by how likely they are to be imported next.

        Used by the dashboard's add project page: repositories the user can
        import come first, repositories that already have a project sink to
        the bottom of their group, and documentation-looking names get a
        boost, keeping the default alphabetical order as the tiebreak.
        """
        if value != "import":
            return queryset
        return queryset.annotate(
            _has_project=Exists(Project.objects.filter(remote_repository=OuterRef("pk"))),
            _looks_like_docs=ExpressionWrapper(
                Q(name__icontains="doc"),
                output_field=BooleanField(),
            ),
        ).order_by(
            "-_admin",
            "_has_project",
            "-_looks_like_docs",
            "organization__name",
            "full_name",
        )


class RemoteOrganizationFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = RemoteOrganization
        fields = [
            "name",
            "vcs_provider",
        ]
