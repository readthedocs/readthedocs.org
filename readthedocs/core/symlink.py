"""
A class that manages the symlinks for nginx to serve public files.

All private serving will be handled by the Python app servers,
so this only cares about public serving.

The main thing that is created is a *Web Root*,
which will be the area that is served from nginx as canonical.

Considerations
--------------

* Single version docs

The web root should be a symlink to the public documentation of that project.

* Subprojects

Subprojects will be nested under the `projects` directory,
they will be a symlink to that project's public documentation.

Objects
-------

Here is a list of all the things that the proper nouns point at:

* Single Version Project -> Default Version
* Language -> Version List
* Subproject -> Language List
* Project -> Language List

Example layout
--------------

.. code-block::

    cname_root/
        docs.fabfile.org -> /web_root/fabric
        pip.pypa.io -> /web_root/pip

    web_root/
        pip/
            en/
                latest -> rtd-builds/pip/latest/
                stable -> rtd-builds/pip/stable/
            ja -> /web_root/pip-ja/ja/
            projects/
                pip-oauth -> /web_root/pip-oauth/
        pip-ja/
            ja/

        fabric -> rtd-builds/fabric/en/latest/ # single version
"""

from __future__ import absolute_import, unicode_literals
from builtins import object
import os
import shutil
import logging
from collections import OrderedDict

from django.conf import settings

from readthedocs.builds.models import Version
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.core.utils import safe_makedirs, safe_unlink
from readthedocs.projects import constants
from readthedocs.projects.models import Domain
from readthedocs.projects.utils import run

log = logging.getLogger(__name__)


class Symlink(object):

    """Base class for symlinking of projects."""

    def __init__(self, project):
        self.project = project
        self.project_root = os.path.join(
            self.WEB_ROOT, project.slug
        )
        self.subproject_root = os.path.join(
            self.project_root, 'projects'
        )
        self.sanity_check()

    def sanity_check(self):
        """
        Make sure the project_root is the proper structure before continuing.

        This will leave it in the proper state for the single_project setting.
        """
        if os.path.islink(self.project_root) and not self.project.single_version:
            log.info(constants.LOG_TEMPLATE.format(
                     project=self.project.slug, version='',
                     msg="Removing single version symlink"))
            safe_unlink(self.project_root)
            safe_makedirs(self.project_root)
        elif (self.project.single_version and
              not os.path.islink(self.project_root) and
              os.path.exists(self.project_root)):
            shutil.rmtree(self.project_root)
        elif not os.path.lexists(self.project_root):
            safe_makedirs(self.project_root)

        # CNAME root directories
        if not os.path.lexists(self.CNAME_ROOT):
            safe_makedirs(self.CNAME_ROOT)
        if not os.path.lexists(self.PROJECT_CNAME_ROOT):
            safe_makedirs(self.PROJECT_CNAME_ROOT)

    def run(self):
        """
        Create proper symlinks in the right order.

        Since we have a small nest of directories and symlinks, the ordering of
        these calls matter, so we provide this helper to make life easier.
        """
        # Outside of the web root
        self.symlink_cnames()

        # Build structure inside symlink zone
        if self.project.single_version:
            self.symlink_single_version()
            self.symlink_subprojects()
        else:
            self.symlink_translations()
            self.symlink_subprojects()
            self.symlink_versions()

    def symlink_cnames(self, domain=None):
        """
        Symlink project CNAME domains.

        Link from HOME/$CNAME_ROOT/<cname> ->
                  HOME/$WEB_ROOT/<project>

        Also give cname -> project link

        Link from HOME/public_cname_project/<cname> ->
                  HOME/<project>/
        """
        if domain:
            domains = [domain]
        else:
            domains = Domain.objects.filter(project=self.project)
        for dom in domains:
            log_msg = 'Symlinking CNAME: {0} -> {1}'.format(dom.domain, self.project.slug)
            log.info(constants.LOG_TEMPLATE.format(project=self.project.slug,
                                                   version='', msg=log_msg))

            # CNAME to doc root
            symlink = os.path.join(self.CNAME_ROOT, dom.domain)
            run(['ln', '-nsf', self.project_root, symlink])

            # Project symlink
            project_cname_symlink = os.path.join(self.PROJECT_CNAME_ROOT, dom.domain)
            run(['ln', '-nsf', self.project.doc_path, project_cname_symlink])

    def remove_symlink_cname(self, domain):
        """Remove CNAME symlink."""
        log_msg = "Removing symlink for CNAME {0}".format(domain.domain)
        log.info(constants.LOG_TEMPLATE.format(project=self.project.slug,
                                               version='', msg=log_msg))
        symlink = os.path.join(self.CNAME_ROOT, domain.domain)
        safe_unlink(symlink)

    def symlink_subprojects(self):
        """
        Symlink project subprojects.

        Link from $WEB_ROOT/projects/<project> ->
                  $WEB_ROOT/<project>
        """
        subprojects = set()
        rels = self.get_subprojects()
        if rels.count():
            # Don't create the `projects/` directory unless subprojects exist.
            if not os.path.exists(self.subproject_root):
                safe_makedirs(self.subproject_root)
        for rel in rels:
            # A mapping of slugs for the subproject URL to the actual built
            # documentation
            from_to = OrderedDict({rel.child.slug: rel.child.slug})
            subprojects.add(rel.child.slug)
            if rel.alias:
                from_to[rel.alias] = rel.child.slug
                subprojects.add(rel.alias)
            for from_slug, to_slug in list(from_to.items()):
                log_msg = "Symlinking subproject: {0} -> {1}".format(from_slug, to_slug)
                log.info(constants.LOG_TEMPLATE.format(project=self.project.slug,
                                                       version='', msg=log_msg))
                symlink = os.path.join(self.subproject_root, from_slug)
                docs_dir = os.path.join(
                    self.WEB_ROOT, to_slug
                )
                symlink_dir = os.sep.join(symlink.split(os.path.sep)[:-1])
                if not os.path.lexists(symlink_dir):
                    safe_makedirs(symlink_dir)
                # TODO this should use os.symlink, not a call to shell. For now,
                # this passes command as a list to be explicit about escaping
                # characters like spaces.
                status, _, stderr = run(['ln', '-nsf', docs_dir, symlink])
                if status > 0:
                    log.error('Could not symlink path: status=%d error=%s',
                              status, stderr)

        # Remove old symlinks
        if os.path.exists(self.subproject_root):
            for subproj in os.listdir(self.subproject_root):
                if subproj not in subprojects:
                    safe_unlink(os.path.join(self.subproject_root, subproj))

    def symlink_translations(self):
        """
        Symlink project translations.

        Link from $WEB_ROOT/<project>/<language>/ ->
                  $WEB_ROOT/<translation>/<language>/
        """
        translations = {}

        for trans in self.get_translations():
            translations[trans.language] = trans.slug

        # Make sure the language directory is a directory
        language_dir = os.path.join(self.project_root, self.project.language)
        if os.path.islink(language_dir):
            safe_unlink(language_dir)
        if not os.path.lexists(language_dir):
            safe_makedirs(language_dir)

        for (language, slug) in list(translations.items()):

            log_msg = 'Symlinking translation: {0}->{1}'.format(language, slug)
            log.info(constants.LOG_TEMPLATE.format(project=self.project.slug,
                                                   version='', msg=log_msg))
            symlink = os.path.join(self.project_root, language)
            docs_dir = os.path.join(self.WEB_ROOT, slug, language)
            run(['ln', '-nsf', docs_dir, symlink])

        # Remove old symlinks
        for lang in os.listdir(self.project_root):
            if (lang not in translations and
                    lang not in ['projects', self.project.language]):
                to_delete = os.path.join(self.project_root, lang)
                if os.path.islink(to_delete):
                    safe_unlink(to_delete)
                else:
                    shutil.rmtree(to_delete)

    def symlink_single_version(self):
        """
        Symlink project single version.

        Link from $WEB_ROOT/<project> ->
                  HOME/user_builds/<project>/rtd-builds/latest/
        """
        version = self.get_default_version()

        # Clean up symlinks
        symlink = self.project_root
        if os.path.islink(symlink):
            safe_unlink(symlink)
        if os.path.exists(symlink):
            shutil.rmtree(symlink)

        # Create symlink
        if version is not None:
            docs_dir = os.path.join(settings.DOCROOT, self.project.slug,
                                    'rtd-builds', version.slug)
            run(['ln', '-nsf', docs_dir, symlink])

    def symlink_versions(self):
        """
        Symlink project's versions.

        Link from $WEB_ROOT/<project>/<language>/<version>/ ->
                  HOME/user_builds/<project>/rtd-builds/<version>
        """
        versions = set()
        version_dir = os.path.join(self.WEB_ROOT, self.project.slug, self.project.language)
        # Include active public versions,
        # as well as public versions that are built but not active, for archived versions
        version_queryset = self.get_version_queryset()
        if version_queryset.count():
            if not os.path.exists(version_dir):
                safe_makedirs(version_dir)
        for version in version_queryset:
            log_msg = 'Symlinking Version: {}'.format(version)
            log.info(constants.LOG_TEMPLATE.format(project=self.project.slug,
                                                   version='', msg=log_msg))
            symlink = os.path.join(version_dir, version.slug)
            docs_dir = os.path.join(settings.DOCROOT, self.project.slug, 'rtd-builds', version.slug)
            run(['ln', '-nsf', docs_dir, symlink])
            versions.add(version.slug)

        # Remove old symlinks
        if os.path.exists(version_dir):
            for old_ver in os.listdir(version_dir):
                if old_ver not in versions:
                    safe_unlink(os.path.join(version_dir, old_ver))

    def get_default_version(self):
        """Look up project default version, return None if not found."""
        default_version = self.project.get_default_version()
        try:
            return self.get_version_queryset().get(slug=default_version)
        except Version.DoesNotExist:
            return None


class PublicSymlinkBase(Symlink):
    CNAME_ROOT = os.path.join(settings.SITE_ROOT, 'public_cname_root')
    WEB_ROOT = os.path.join(settings.SITE_ROOT, 'public_web_root')
    PROJECT_CNAME_ROOT = os.path.join(settings.SITE_ROOT, 'public_cname_project')

    def get_version_queryset(self):
        return (self.project.versions.protected(only_active=False).filter(built=True) |
                self.project.versions.protected(only_active=True))

    def get_subprojects(self):
        return self.project.subprojects.protected()

    def get_translations(self):
        return self.project.translations.protected()


class PrivateSymlinkBase(Symlink):
    CNAME_ROOT = os.path.join(settings.SITE_ROOT, 'private_cname_root')
    WEB_ROOT = os.path.join(settings.SITE_ROOT, 'private_web_root')
    PROJECT_CNAME_ROOT = os.path.join(settings.SITE_ROOT, 'private_cname_project')

    def get_version_queryset(self):
        return (self.project.versions.private(only_active=False).filter(built=True) |
                self.project.versions.private(only_active=True))

    def get_subprojects(self):
        return self.project.subprojects.private()

    def get_translations(self):
        return self.project.translations.private()


class PublicSymlink(SettingsOverrideObject):

    _default_class = PublicSymlinkBase


class PrivateSymlink(SettingsOverrideObject):

    _default_class = PrivateSymlinkBase
