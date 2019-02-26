import datetime

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from rest_framework import serializers
from readthedocs.projects.constants import LANGUAGES, PROGRAMMING_LANGUAGES
from readthedocs.projects.models import Project
from readthedocs.builds.models import Build, Version
from readthedocs.projects.version_handling import determine_stable_version
from readthedocs.builds.constants import STABLE

from rest_framework_serializer_extensions.serializers import SerializerExtensionsMixin


class UserSerializer(serializers.ModelSerializer):

    # TODO: return ``null`` when ``last_name`` or ``first_name`` are `''``. I'm
    # thinking on writing a decorator or similar that dynamically creates the
    # methods based on a field with a list

    class Meta:
        model = User
        fields = [
            'username',
            'date_joined',
            'last_login',
            'first_name',
            'last_name',
        ]


class BuildSerializer(serializers.ModelSerializer):

    created = serializers.DateTimeField(source='date')
    finished = serializers.SerializerMethodField()
    duration = serializers.IntegerField(source='length')

    class Meta:
        model = Build
        expandable_fields = dict(
            version='readthedocs.v3.serializers.VersionSerializer',
            project='readthedocs.v3.serializers.ProjectSerializer',
            # config=BuildConfigSerializer,
        )
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
            'builder',
            'cold_storage',
            'config',
            # 'links',
        ]

    def get_finished(self, obj):
        if obj.date and obj.length:
            return obj.date + datetime.timedelta(seconds=obj.length)


class PrivacyLevelSerializer(serializers.Serializer):
    code = serializers.CharField(source='privacy_level')
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.privacy_level.title()


class VersionURLsSerializer(serializers.Serializer):
    documentation = serializers.SerializerMethodField()
    vcs = serializers.SerializerMethodField()

    def get_documentation(self, obj):
        return obj.project.get_docs_url(
            version_slug=obj.slug,
        )

    def get_vcs(self, obj):
        # TODO: make this method to work properly
        if obj.project.repo_type == 'git':
            return obj.project.repo + f'/tree/{obj.slug}'


class VersionSerializer(serializers.ModelSerializer):

    privacy_level = PrivacyLevelSerializer(source='*')
    ref = serializers.SerializerMethodField()
    last_build = serializers.SerializerMethodField()

    # FIXME: generate URLs with HTTPS schema
    downloads = serializers.DictField(source='get_downloads')

    urls = VersionURLsSerializer(source='*')

    class Meta:
        model = Version
        # expandable_fields = dict(
        #     last_build=serializers.SerializerMethodField,
        # )
        fields = [
            'id',
            'slug',
            'verbose_name',
            'identifier',
            'ref',
            'built',
            'active',
            'uploaded',
            'privacy_level',
            'type',

            # TODO: make this field expandable also. Nested expandable fields
            # are not working when using ``SerializerMethodField`` at the moment
            'last_build',

            'downloads',
            'urls',
            # 'links',
        ]

    def get_ref(self, obj):
        if obj.slug == STABLE:
            stable = determine_stable_version(obj.project.versions.all())
            if stable:
                return stable.slug

    def get_last_build(self, obj):
        build = obj.builds.order_by('-date').first()
        return BuildSerializer(build).data


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
    project = serializers.SerializerMethodField()

    def get_project(self, obj):
        # Overridden only to return ``None`` when the description is ``''``
        return obj.project_url or None


class RepositorySerializer(serializers.Serializer):

    url = serializers.CharField(source='repo')
    type = serializers.CharField(source='repo_type')


class ProjectLinksSerializer(serializers.Serializer):

    _self = serializers.SerializerMethodField()
    # users = serializers.URLField(source='get_link_users')
    # versions = serializers.URLField(source='get_link_versions')
    # users = serializers.URLField(source='get_link_users')
    # builds = serializers.URLField(source='get_link_builds')
    # subprojects = serializers.URLField(source='get_link_subprojects')
    # translations = serializers.URLField(source='get_link_translations')

    def get__self(self, obj):
        # TODO: maybe we want to make them full URLs instead of absolute
        return reverse('projects-detail', kwargs={'project_slug': obj.slug})


class ProjectSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):

    language = LanguageSerializer()
    programming_language = ProgrammingLanguageSerializer()
    repository = RepositorySerializer(source='*')
    privacy_level = PrivacyLevelSerializer(source='*')
    urls = ProjectURLsSerializer(source='*')
    # active_versions = serializers.SerializerMethodField()
    subproject_of = serializers.SerializerMethodField()
    translation_of = serializers.SerializerMethodField()
    default_branch = serializers.CharField(source='get_default_branch')
    tags = serializers.StringRelatedField(many=True)

    description = serializers.SerializerMethodField()

    links = ProjectLinksSerializer(source='*')

    # TODO: adapt these fields with the proper names in the db and then remove
    # them from here
    created = serializers.DateTimeField(source='pub_date')
    modified = serializers.DateTimeField(source='modified_date')

    class Meta:
        model = Project
        expandable_fields = dict(
            users=dict(
                serializer=UserSerializer,
                many=True,
            ),
            active_versions=dict(
                serializer=serializers.SerializerMethodField,
            ),
        )
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
            'urls',
            'tags',
            'links',
        ]

    def get_description(self, obj):
        # Overridden only to return ``None`` when the description is ``''``
        return obj.description or None

    def get_active_versions(self, obj):
        return VersionSerializer(obj.versions.filter(active=True), many=True).data

    def get_translation_of(self, obj):
        try:
            return obj.main_language_project.slug
        except:
            return None

    def get_subproject_of(self, obj):
        try:
            return obj.superprojects.first().slug
        except:
            return None
