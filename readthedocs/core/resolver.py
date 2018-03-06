"""URL resolver for documentation."""

from __future__ import absolute_import
from builtins import object
import re

from django.conf import settings

from readthedocs.projects.constants import PRIVATE, PUBLIC
from readthedocs.core.utils.extend import SettingsOverrideObject


class ResolverBase(object):

    """
    Read the Docs URL Resolver.

    Url Types:

    - Subdomain
    - CNAME

    Path Types:

    - Subproject
    - Single Version
    - Normal

    All possible URL's::

        Subdomain or CNAME:

        # Default
        /<lang>/<version>/<filename>
        # Single Version
        /<filename>
        # Subproject Default
        /projects/<subproject_slug>/<lang>/<version>/<filename>
        # Subproject Single Version
        /projects/<subproject_slug>/<filename>

        Development serving:

        # Default
        /docs/<project_slug>/<lang>/<version>/<filename>
        # Single Version
        /docs/<project_slug>/<filename>
        # Subproject Default
        /docs/<project_slug>/projects/<subproject_slug>/<lang>/<version>/<filename>
        # Subproject Single Version
        /docs/<project_slug>/projects/<subproject_slug>/<filename>
    """

    def base_resolve_path(self, project_slug, filename, version_slug=None,
                          language=None, private=False, single_version=None,
                          subproject_slug=None, subdomain=None, cname=None):
        """Resolve a with nothing smart, just filling in the blanks."""
        # Only support `/docs/project' URLs outside our normal environment. Normally
        # the path should always have a subdomain or CNAME domain
        # pylint: disable=unused-argument
        if subdomain or cname or (self._use_subdomain()):
            url = u'/'
        else:
            url = u'/docs/{project_slug}/'

        if subproject_slug:
            url += u'projects/{subproject_slug}/'

        if single_version:
            url += u'{filename}'
        else:
            url += u'{language}/{version_slug}/{filename}'

        return url.format(
            project_slug=project_slug, filename=filename,
            version_slug=version_slug, language=language,
            single_version=single_version, subproject_slug=subproject_slug,
        )

    def resolve_path(self, project, filename='', version_slug=None,
                     language=None, single_version=None, subdomain=None,
                     private=None, cname=None, relation=None, **kwargs):
        """Resolve a URL with a subset of fields defined."""

        main_language_project_id = project.main_language_project_id
        version_slug = version_slug or project.get_default_version()
        language = language or project.language
        relation_bool = kwargs.pop('relation_bool',False)
        cname_bool = kwargs.pop('cname_bool',False)
        private_bool = kwargs.pop('private_bool',False)

        if not cname_bool:
            cname = cname or project.domains.filter(canonical=True).first()
        if not private_bool:
            private = private or self._get_private(project, version_slug)
        if not relation_bool:
            relation = relation or project.superprojects.prefetch_related('parent__domains').first()

        filename = self._fix_filename(project, filename)
        if main_language_project_id:
            project_slug = project.main_language_project.slug
            language = project.language
            subproject_slug = None
        elif relation:
            project_slug = relation.parent.slug
            subproject_slug = relation.alias
            cname = relation.parent.domains.filter(canonical=True).first()
        else:
            project_slug = project.slug
            subproject_slug = None
        single_version = bool(project.single_version or single_version)
        return self.base_resolve_path(
            project_slug=project_slug,
            filename=filename,
            version_slug=version_slug,
            language=language,
            single_version=single_version,
            subproject_slug=subproject_slug,
            cname=cname,
            private=private,
            subdomain=subdomain,
        )

    def resolve_domain(self, project, private=None):
        # pylint: disable=unused-argument
        canonical_project = self._get_canonical_project(project)
        domains = canonical_project.domains.filter(canonical=True)
        if domains.exists():
            return domains.first().domain
        elif self._use_subdomain():
            return self._get_project_subdomain(canonical_project)
        return getattr(settings, 'PRODUCTION_DOMAIN')

    def resolve(self, project, protocol='http', filename='', private=None,**kwargs):
        domain = kwargs.pop('domain',None)
        if domain is None:
            domain = self.resolve_domain(project)
        return '{protocol}://{domain}{path}'.format(
            protocol=protocol,
            domain=domain,
            path=self.resolve_path(project, filename=filename, **kwargs),
        )

    def _get_canonical_project(self, project):
        """
        Get canonical project in the case of subproject or translations.

        :type project: Project
        :rtype: Project
        """
        main_language_project_id = project.main_language_project_id
        relations = project.superprojects.all()
        if main_language_project_id:
            return project.main_language_project
        elif relations:
            relation = relations.prefetch_related('parent__domains').first()
            return relation.parent
        return project

    def _get_project_subdomain(self, project):
        """Determine canonical project domain as subdomain."""
        public_domain = getattr(settings, 'PUBLIC_DOMAIN', None)
        if self._use_subdomain():
            project = self._get_canonical_project(project)
            subdomain_slug = project.slug.replace('_', '-')
            return "%s.%s" % (subdomain_slug, public_domain)

    def _get_private(self, project, version_slug):
        from readthedocs.builds.models import Version
        try:
            version = project.versions.get(slug=version_slug)
            private = version.privacy_level == PRIVATE
        except Version.DoesNotExist:
            private = getattr(settings, 'DEFAULT_PRIVACY_LEVEL', PUBLIC) == PRIVATE
        return private

    def _fix_filename(self, project, filename):
        """
        Force filenames that might be HTML file paths into proper URL's.

        This basically means stripping / and .html endings and then re-adding
        them properly.
        """
        # Bail out on non-html files
        if '.' in filename and '.html' not in filename:
            return filename
        filename = filename.lstrip('/')
        filename = re.sub(r'(^|/)index(?:.html)?$', '\\1', filename)
        if filename:
            if filename.endswith('/') or filename.endswith('.html'):
                path = filename
            elif project.documentation_type == "sphinx_singlehtml":
                path = "index.html#document-" + filename
            elif project.documentation_type in ["sphinx_htmldir", "mkdocs"]:
                path = filename + "/"
            elif '#' in filename:
                # do nothing if the filename contains URL fragments
                path = filename
            else:
                path = filename + ".html"
        else:
            path = ""
        return path

    def _use_subdomain(self):
        """Make decision about whether to use a subdomain to serve docs."""
        use_subdomain = getattr(settings, 'USE_SUBDOMAIN', False)
        public_domain = getattr(settings, 'PUBLIC_DOMAIN', None)
        return use_subdomain and public_domain is not None


class Resolver(SettingsOverrideObject):

    _default_class = ResolverBase
    _override_setting = 'RESOLVER_CLASS'


resolver = Resolver()
resolve_path = resolver.resolve_path
resolve_domain = resolver.resolve_domain
resolve = resolver.resolve
