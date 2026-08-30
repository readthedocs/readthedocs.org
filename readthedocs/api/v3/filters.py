import django_filters.rest_framework as filters

from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.notifications.models import Notification
from readthedocs.oauth.models import RemoteOrganization
from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects.models import Project
from django.db.models.functions import Length


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


class VersionOrderingFilter(filters.OrderingFilter):
    """
    Custom ordering filter for versions.

    This is needed to support ordering by the length of the verbose_name field,
    so it can be annotated in the queryset only when needed.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "fields",
            (
                ('verbose_name', "verbose_name"),
                ('verbose_name_length', 'verbose_name_length'),
            ),
        )
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        for value_name in value or []:
            if value_name in ["verbose_name_length", "-verbose_name_length"]:
                qs = qs.annotate(verbose_name_length=Length("verbose_name"))
                break

        return super().filter(qs, value)


class VersionFilter(filters.FilterSet):
    slug = filters.CharFilter(lookup_expr="icontains")
    verbose_name = filters.CharFilter(lookup_expr="icontains")
    sort = VersionOrderingFilter()

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
