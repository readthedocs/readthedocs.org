import datetime
import urllib

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from rest_flex_fields import FlexFieldsModelSerializer
from rest_flex_fields.serializers import FlexFieldsSerializerMixin
from rest_framework import serializers

from readthedocs.builds.models import Build, Version
from readthedocs.projects.constants import LANGUAGES, PROGRAMMING_LANGUAGES
from readthedocs.projects.models import Project
from readthedocs.redirects.models import Redirect


class UserSerializer(FlexFieldsModelSerializer):

    created = serializers.DateTimeField(source='date_joined')

    class Meta:
        model = User
        fields = [
            'username',
            'created',
        ]


class BaseLinksSerializer(serializers.Serializer):

    def _absolute_url(self, path):
        scheme = 'http' if settings.DEBUG else 'https'
        domain = settings.PRODUCTION_DOMAIN
        return urllib.parse.urlunparse((scheme, domain, path, '', '', ''))


class BuildCreateSerializer(serializers.ModelSerializer):

    """
    Used when triggering (create action) a ``Build`` for a specific ``Version``.

    This serializer validates that no field is sent at all in the request.
    """

    class Meta:
        model = Build
        fields = []


class BuildLinksSerializer(BaseLinksSerializer):
    _self = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()

    def get__self(self, obj):
        path = reverse(
            'projects-builds-detail',
            kwargs={
                'parent_lookup_project__slug': obj.project.slug,
                'build_pk': obj.pk,
            },
        )
        return self._absolute_url(path)

    def get_version(self, obj):
        path = reverse(
            'projects-versions-detail',
            kwargs={
                'parent_lookup_project__slug': obj.project.slug,
                'version_slug': obj.version.slug,
            },
        )
        return self._absolute_url(path)

    def get_project(self, obj):
        path = reverse(
            'projects-detail',
            kwargs={
                'project_slug': obj.project.slug,
            },
        )
        return self._absolute_url(path)


class BuildConfigSerializer(FlexFieldsSerializerMixin, serializers.Serializer):

    """
    Render ``Build.config`` property without modifying it.

    .. note::

       Any change on the output of that property will be reflected here,
       which may produce incompatible changes in the API.
    """

    def to_representation(self, instance):
        # For now, we want to return the ``config`` object as it is without
        # manipulating it.
        return instance


class BuildStateSerializer(serializers.Serializer):
    code = serializers.CharField(source='state')
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.state.title()


class BuildSerializer(FlexFieldsModelSerializer):

    project = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    version = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    created = serializers.DateTimeField(source='date')
    finished = serializers.SerializerMethodField()
    success = serializers.SerializerMethodField()
    duration = serializers.IntegerField(source='length')
    state = BuildStateSerializer(source='*')
    _links = BuildLinksSerializer(source='*')

    expandable_fields = dict(
        config=(
            BuildConfigSerializer,
            dict(
                source='config',
            ),
        ),
    )

    class Meta:
        model = Build
        fields = [
            'id',
            'version',
            'project',
            'created',
            'finished',
            'duration',
            'state',
            'success',
            'error',
            'commit',
            '_links',
        ]

    def get_finished(self, obj):
        if obj.date and obj.length:
            return obj.date + datetime.timedelta(seconds=obj.length)

    def get_success(self, obj):
        """
        Return ``None`` if the build is not finished.

        This is needed becase ``default=True`` in the model field.
        """
        if obj.finished:
            return obj.success

        return None


class PrivacyLevelSerializer(serializers.Serializer):
    code = serializers.CharField(source='privacy_level')
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.privacy_level.title()


class VersionLinksSerializer(BaseLinksSerializer):
    _self = serializers.SerializerMethodField()
    builds = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()

    def get__self(self, obj):
        path = reverse(
            'projects-versions-detail',
            kwargs={
                'parent_lookup_project__slug': obj.project.slug,
                'version_slug': obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_builds(self, obj):
        path = reverse(
            'projects-versions-builds-list',
            kwargs={
                'parent_lookup_project__slug': obj.project.slug,
                'parent_lookup_version__slug': obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_project(self, obj):
        path = reverse(
            'projects-detail',
            kwargs={
                'project_slug': obj.project.slug,
            },
        )
        return self._absolute_url(path)


class VersionURLsSerializer(serializers.Serializer):
    documentation = serializers.SerializerMethodField()
    vcs = serializers.URLField(source='vcs_url')

    def get_documentation(self, obj):
        return obj.project.get_docs_url(version_slug=obj.slug,)


class VersionSerializer(FlexFieldsModelSerializer):

    privacy_level = PrivacyLevelSerializer(source='*')
    ref = serializers.CharField()
    downloads = serializers.SerializerMethodField()
    urls = VersionURLsSerializer(source='*')
    _links = VersionLinksSerializer(source='*')

    expandable_fields = dict(
        last_build=(
            BuildSerializer,
            dict(
                source='last_build',
            ),
        ),
    )

    class Meta:
        model = Version
        fields = [
            'id',
            'slug',
            'verbose_name',
            'identifier',
            'ref',
            'built',
            'active',
            'privacy_level',
            'type',
            'downloads',
            'urls',
            '_links',
        ]

    def get_downloads(self, obj):
        downloads = obj.get_downloads()
        data = {}

        for k, v in downloads.items():
            if k in ('htmlzip', 'pdf', 'epub'):
                data[k] = ('http:' if settings.DEBUG else 'https:') + v

        return data


class VersionUpdateSerializer(serializers.ModelSerializer):

    """
    Used when modifying (update action) a ``Version``.

    It only allows to make the Version active/non-active and private/public.
    """

    class Meta:
        model = Version
        fields = [
            'active',
            'privacy_level',
        ]


class LanguageSerializer(serializers.Serializer):

    code = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_code(self, language):
        return language

    def get_name(self, language):
        for code, name in LANGUAGES:
            if code == language:
                return name
        return 'Unknown'


class ProgrammingLanguageSerializer(serializers.Serializer):

    code = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_code(self, programming_language):
        return programming_language

    def get_name(self, programming_language):
        for code, name in PROGRAMMING_LANGUAGES:
            if code == programming_language:
                return name
        return 'Unknown'


class ProjectURLsSerializer(serializers.Serializer):
    documentation = serializers.CharField(source='get_docs_url')
    project_homepage = serializers.SerializerMethodField()

    def get_project_homepage(self, obj):
        # Overridden only to return ``None`` when the description is ``''``
        return obj.project_url or None


class RepositorySerializer(serializers.Serializer):

    url = serializers.CharField(source='repo')
    type = serializers.CharField(source='repo_type')


class ProjectLinksSerializer(BaseLinksSerializer):

    _self = serializers.SerializerMethodField()

    versions = serializers.SerializerMethodField()
    builds = serializers.SerializerMethodField()
    redirects = serializers.SerializerMethodField()
    subprojects = serializers.SerializerMethodField()
    superproject = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()

    def get__self(self, obj):
        path = reverse('projects-detail', kwargs={'project_slug': obj.slug})
        return self._absolute_url(path)

    def get_versions(self, obj):
        path = reverse(
            'projects-versions-list',
            kwargs={
                'parent_lookup_project__slug': obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_redirects(self, obj):
        path = reverse(
            'projects-redirects-list',
            kwargs={
                'parent_lookup_project__slug': obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_builds(self, obj):
        path = reverse(
            'projects-builds-list',
            kwargs={
                'parent_lookup_project__slug': obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_subprojects(self, obj):
        path = reverse(
            'projects-subprojects-list',
            kwargs={
                'parent_lookup_superprojects__parent__slug': obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_superproject(self, obj):
        path = reverse(
            'projects-superproject',
            kwargs={
                'project_slug': obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_translations(self, obj):
        path = reverse(
            'projects-translations-list',
            kwargs={
                'parent_lookup_main_language_project__slug': obj.slug,
            },
        )
        return self._absolute_url(path)


class ProjectSerializer(FlexFieldsModelSerializer):

    language = LanguageSerializer()
    programming_language = ProgrammingLanguageSerializer()
    repository = RepositorySerializer(source='*')
    privacy_level = PrivacyLevelSerializer(source='*')
    urls = ProjectURLsSerializer(source='*')
    subproject_of = serializers.SerializerMethodField()
    translation_of = serializers.SerializerMethodField()
    default_branch = serializers.CharField(source='get_default_branch')
    tags = serializers.StringRelatedField(many=True)
    users = UserSerializer(many=True)

    description = serializers.SerializerMethodField()

    _links = ProjectLinksSerializer(source='*')

    # TODO: adapt these fields with the proper names in the db and then remove
    # them from here
    created = serializers.DateTimeField(source='pub_date')
    modified = serializers.DateTimeField(source='modified_date')

    expandable_fields = dict(
        active_versions=(
            VersionSerializer,
            dict(
                # NOTE: this has to be a Model method, can't be a
                # ``SerializerMethodField`` as far as I know
                source='active_versions',
                many=True,
            ),
        ),
    )

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'created',
            'modified',
            'language',
            'programming_language',
            'repository',
            'default_version',
            'default_branch',
            'privacy_level',
            'subproject_of',
            'translation_of',
            'users',
            'urls',
            'tags',

            # NOTE: ``expandable_fields`` must not be included here. Otherwise,
            # they will be tried to be rendered and fail
            # 'users',
            # 'active_versions',

            '_links',
        ]

    def get_description(self, obj):
        # Overridden only to return ``None`` when the description is ``''``
        return obj.description or None

    def get_translation_of(self, obj):
        if obj.main_language_project:
            return self.__class__(obj.main_language_project).data

    def get_subproject_of(self, obj):
        try:
            return self.__class__(obj.superprojects.first().parent).data
        except Exception:
            return None


class RedirectLinksSerializer(BaseLinksSerializer):
    _self = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()

    def get__self(self, obj):
        path = reverse(
            'projects-redirects-detail',
            kwargs={
                'parent_lookup_project__slug': obj.project.slug,
                'redirect_pk': obj.pk,
            },
        )
        return self._absolute_url(path)

    def get_project(self, obj):
        path = reverse(
            'projects-detail',
            kwargs={
                'project_slug': obj.project.slug,
            },
        )
        return self._absolute_url(path)


class RedirectSerializer(serializers.ModelSerializer):

    project = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    _links = RedirectLinksSerializer(source='*', read_only=True)

    class Meta:
        model = Redirect
        fields = [
            'pk',
            'project',
            'redirect_type',
            'from_url',
            'to_url',
            '_links',
        ]
