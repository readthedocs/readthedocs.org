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
                     cname=None, private=None):
        """Resolve a URL with a subset of fields defined."""
        cname = cname or project.domains.filter(canonical=True).first()
        version_slug = version_slug or project.get_default_version()
        language = language or project.language

        if private is None:
            private = self._get_private(project, version_slug)

        filename = self._fix_filename(project, filename)

        current_project = project
        project_slug = project.slug
        subproject_slug = None
        # We currently support more than 2 levels of nesting subprojects and
        # translations, only loop twice to avoid sticking in the loop
        for _ in range(0, 2):
            main_language_project = current_project.main_language_project
            relation = current_project.superprojects.first()

            if main_language_project:
                current_project = main_language_project
                project_slug = main_language_project.slug
                language = project.language
                subproject_slug = None
            elif relation:
                current_project = relation.parent
                project_slug = relation.parent.slug
                subproject_slug = relation.alias
                cname = relation.parent.domains.filter(canonical=True).first()
            else:
                break

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
        domain = self._get_project_custom_domain(canonical_project)
        if domain:
            return domain.domain

        if self._use_subdomain():
            return self._get_project_subdomain(canonical_project)

        return getattr(settings, 'PRODUCTION_DOMAIN')

    def resolve(self, project, require_https=False, filename='', private=None,
                **kwargs):
        if private is None:
            version_slug = kwargs.get('version_slug')
            if version_slug is None:
                version_slug = project.get_default_version()
            private = self._get_private(project, version_slug)

        canonical_project = self._get_canonical_project(project)
        custom_domain = self._get_project_custom_domain(canonical_project)
        use_custom_domain = self._use_custom_domain(custom_domain)

        if use_custom_domain:
            domain = custom_domain.domain
        elif self._use_subdomain():
            domain = self._get_project_subdomain(canonical_project)
        else:
            domain = getattr(settings, 'PRODUCTION_DOMAIN')

        public_domain = getattr(settings, 'PUBLIC_DOMAIN', None)
        use_https = getattr(settings, 'PUBLIC_DOMAIN_USES_HTTPS', False)

        use_https_protocol = any([
            # Rely on the ``Domain.https`` field
            use_custom_domain and custom_domain.https,
            # or force it if specified
            require_https,
            # or fallback to settings
            use_https and public_domain and public_domain in domain,
        ])
        protocol = 'https' if use_https_protocol else 'http'

        return '{protocol}://{domain}{path}'.format(
            protocol=protocol,
            domain=domain,
            path=self.resolve_path(project, filename=filename, private=private,
                                   **kwargs),
        )

    def _get_canonical_project(self, project, projects=None):
        """
        Recursively get canonical project for subproject or translations.

        We need to recursively search here as a nested translations inside
        subprojects, and vice versa, are supported.

        :type project: Project
        :type projects: List of projects for iteration
        :rtype: Project
        """
        # Track what projects have already been traversed to avoid infinite
        # recursion. We can't determine a root project well here, so you get
        # what you get if you have configured your project in a strange manner
        if projects is None:
            projects = [project]
        else:
            projects.append(project)
        next_project = None

        relation = project.superprojects.first()
        if project.main_language_project:
            next_project = project.main_language_project
        elif relation:
            next_project = relation.parent
        if next_project and next_project not in projects:
            return self._get_canonical_project(next_project, projects)
        return project

    def _get_project_subdomain(self, project):
        """Determine canonical project domain as subdomain."""
        public_domain = getattr(settings, 'PUBLIC_DOMAIN', None)
        if self._use_subdomain():
            project = self._get_canonical_project(project)
            subdomain_slug = project.slug.replace('_', '-')
            return "%s.%s" % (subdomain_slug, public_domain)

    def _get_project_custom_domain(self, project):
        return project.domains.filter(canonical=True).first()

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

    def _use_custom_domain(self, custom_domain):
        """
        Make decision about whether to use a custom domain to serve docs.

        Always use the custom domain if it exists.

        :param custom_domain: Domain instance or ``None``
        :type custom_domain: readthedocs.projects.models.Domain
        """
        return True if custom_domain is not None else False

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
