"""
A class that managed the symlinks for nginx to serve public files.

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

import os
import shutil
import logging
from collections import OrderedDict

from django.conf import settings

from readthedocs.projects.constants import LOG_TEMPLATE
from readthedocs.projects.models import Domain
from readthedocs.projects.utils import run

log = logging.getLogger(__name__)


class Symlink(object):

    """
    Base class for Symlinking of projects.

    This will be inherited for private & public symlinking.
    """

    CNAME_ROOT = os.path.join(settings.SITE_ROOT, 'public_cname_root')
    WEB_ROOT = os.path.join(settings.SITE_ROOT, 'public_web_root')

    def __init__(self, project):
        self.project = project
        self.PROJECT_ROOT = os.path.join(
            self.WEB_ROOT, project.slug
        )
        self.SUBPROJECT_ROOT = os.path.join(
            self.PROJECT_ROOT, 'projects'
        )
        self.sanity_check()

    def _log(self, msg, level='info'):
        logger = getattr(log, level)
        logger(LOG_TEMPLATE
               .format(project=self.project.slug,
                       version='',
                       msg=msg)
               )

    def sanity_check(self):
        """
        Make sure the PROJECT_ROOT is the proper structure before continuing.

        This will leave it in the proper state for the single_project setting.
        """
        if os.path.islink(self.PROJECT_ROOT) and not self.project.single_version:
            self._log("Removing single version symlink")
            os.unlink(self.PROJECT_ROOT)
            os.makedirs(self.PROJECT_ROOT)
        elif self.project.single_version and not os.path.islink(self.PROJECT_ROOT):
            shutil.rmtree(self.PROJECT_ROOT)
        elif not os.path.exists(self.PROJECT_ROOT):
            os.makedirs(self.PROJECT_ROOT)

    def run(self):
        """
        Create proper symlinks in the right order.

        Since we have a small nest of directories and symlinks,
        the ordering of these calls matter,
        so we provide this helper to make life easier.
        """
        # Outside of the web root
        self.symlink_cnames()

        # Build structure inside symlink zone
        if self.project.single_version:
            self.symlink_single_version()
        else:
            self.symlink_translations()
            self.symlink_subprojects()
            self.symlink_versions()

    def symlink_cnames(self, domain=None):
        """Symlink project CNAME domains

        Link from HOME/user_builds/$CNAME_ROOT/<cname> ->
                  HOME/user_builds/$WEB_ROOT/<project>
        """
        if domain:
            domains = [domain]
        else:
            domains = Domain.objects.filter(project=self.project)
        for domain in domains:
            self._log("Symlinking CNAME: {0} -> {1}".format(domain.domain, self.project.slug))
            docs_dir = self.PROJECT_ROOT
            symlink = os.path.join(self.CNAME_ROOT, domain.domain)

            # Make sure containing directories exist
            symlink_dir = os.sep.join(symlink.split(os.path.sep)[:-1])
            if not os.path.lexists(symlink_dir):
                os.makedirs(symlink_dir)
            # Create proper symlinks
            print run('ln -nsf {0} {1}'.format(docs_dir, symlink))

    def remove_symlink_cname(self, domain):
        """Remove single_version symlink"""
        self._log("Removing symlink for CNAME {0}".format(domain.domain))
        symlink = os.path.join(self.CNAME_ROOT, domain.domain)
        os.unlink(symlink)

    def symlink_subprojects(self):
        """Symlink project subprojects

        Link from $WEB_ROOT/projects/<project> ->
                  $WEB_ROOT/<project>
        """
        rels = self.project.subprojects.all()
        if rels.count():
            if not os.path.exists(self.SUBPROJECT_ROOT):
                os.makedirs(self.SUBPROJECT_ROOT)
        for rel in rels:
            # A mapping of slugs for the subproject URL to the actual built
            # documentation
            from_to = OrderedDict({rel.child.slug: rel.child.slug})
            if rel.alias:
                from_to[rel.alias] = rel.child.slug
            for from_slug, to_slug in from_to.items():
                self._log("Symlinking subproject: {0} -> {1}".format(from_slug, to_slug))
                symlink = os.path.join(self.SUBPROJECT_ROOT, from_slug)
                docs_dir = os.path.join(
                    self.WEB_ROOT, to_slug
                )
                symlink_dir = os.sep.join(symlink.split(os.path.sep)[:-1])
                if not os.path.lexists(symlink_dir):
                    os.makedirs(symlink_dir)
                print run('ln -nsf %s %s' % (docs_dir, symlink))

    def symlink_translations(self):
        """Symlink project translations

        Link from $WEB_ROOT/<project>/<language>/ ->
                  $WEB_ROOT/<translation>/<language>/
        """
        translations = {}

        for trans in self.project.translations.all():
            translations[trans.language] = trans.slug

        # Make sure the language directory is a directory
        language_dir = os.path.join(self.PROJECT_ROOT, self.project.language)
        if os.path.islink(language_dir):
            os.unlink(language_dir)
        if not os.path.exists(language_dir):
            os.makedirs(language_dir)

        for (language, slug) in translations.items():
            self._log("Symlinking translation: {0}->{1}".format(language, slug))
            symlink = os.path.join(self.PROJECT_ROOT, language)
            docs_dir = os.path.join(self.WEB_ROOT, slug, language)
            print run('ln -nsf {0} {1}'.format(docs_dir, symlink))

    def symlink_single_version(self):
        """Symlink project single version

        Link from $WEB_ROOT/<project> ->
                  HOME/user_builds/<project>/rtd-builds/latest/
        """
        default_version = self.project.get_default_version()
        self._log("Symlinking single_version")

        symlink = self.PROJECT_ROOT
        if os.path.islink(symlink):
            os.unlink(symlink)
        if os.path.exists(symlink):
            shutil.rmtree(symlink)

        # Where the actual docs live
        docs_dir = os.path.join(settings.DOCROOT, self.project.slug, 'rtd-builds', default_version)
        print run('ln -nsf %s/ %s' % (docs_dir, symlink))

    def symlink_versions(self):
        """Symlink project's versions

        Link from $WEB_ROOT/<project>/<language>/<version>/ ->
                  HOME/user_builds/<project>/rtd-builds/<version>
        """
        for version in self.project.versions.public(only_active=True):
            self._log("Symlinking Version: %s" % version)
            symlink = os.path.join(
                self.WEB_ROOT, self.project.slug, self.project.language, version.slug)
            docs_dir = os.path.join(settings.DOCROOT, self.project.slug, 'rtd-builds', version.slug)
            print run('ln -nsf {0} {1}'.format(docs_dir, symlink))
