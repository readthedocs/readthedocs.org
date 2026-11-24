import django_filters.rest_framework as filters
from django.db.models import BooleanField
from django.db.models import Case
from django.db.models import Exists
from django.db.models import ExpressionWrapper
from django.db.models import IntegerField
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Value
from django.db.models import When

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
            "is_uploaded",
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


class RemoteRepositoryOrderingFilter(filters.OrderingFilter):
    """Ordering filter with an ``import`` choice that puts the best import candidates first."""

    def filter(self, qs, value):
        if not value or "import" not in value:
            return super().filter(qs, value)

        # The ``full_name`` search matches the owner too, so rank repositories
        # the query matched on the name (prefix, then anywhere) above the rest.
        query = self.parent.form.cleaned_data.get("full_name")
        search_rank = (
            Case(
                When(name__istartswith=query, then=0),
                When(name__icontains=query, then=1),
                default=2,
                output_field=IntegerField(),
            )
            if query
            else Value(0)
        )

        # Importable repositories first, best search match, nothing imported
        # yet, documentation-looking names, and alphabetical as the tiebreak.
        return qs.annotate(
            _search_rank=search_rank,
            _has_project=Exists(Project.objects.filter(remote_repository=OuterRef("pk"))),
            _looks_like_docs=ExpressionWrapper(
                Q(name__icontains="doc"),
                output_field=BooleanField(),
            ),
        ).order_by(
            "-_admin",
            "_search_rank",
            "_has_project",
            "-_looks_like_docs",
            "organization__name",
            "full_name",
        )


class RemoteRepositoryFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    full_name = filters.CharFilter(field_name="full_name", lookup_expr="icontains")
    organization = filters.CharFilter(field_name="organization__slug")
    ordering = RemoteRepositoryOrderingFilter(
        choices=[("import", "Repositories most likely to be imported first")],
    )

    class Meta:
        model = RemoteRepository
        fields = [
            "name",
            "full_name",
            "vcs_provider",
            "organization",
        ]


class RemoteOrganizationFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = RemoteOrganization
        fields = [
            "name",
            "vcs_provider",
        ]
