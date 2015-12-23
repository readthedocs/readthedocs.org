"""Project symlink creation"""

import os
import logging
from collections import OrderedDict

from django.conf import settings

from readthedocs.core.utils import run_on_app_servers
from readthedocs.projects.constants import LOG_TEMPLATE
from readthedocs.projects.models import Domain
from readthedocs.restapi.client import api

log = logging.getLogger(__name__)


class Symlink(object):

    """
    Base class for Symlinking of projects.

    This will be inherited for private & public symlinking.
    """

    def __init__(self, project):
        self.project = project

    def _log(self, msg, level='info'):
        level = getattr(log, level)
        level(LOG_TEMPLATE
              .format(project=self.project.slug,
                      version='',
                      msg=msg)
              )

    def symlink_cnames(self):
        """Symlink project CNAME domains

        Link from HOME/user_builds/$CNAME_ROOT/<cname> ->
                  HOME/user_builds/<project>/rtd-builds/
        """
        domains = Domain.objects.filter(project=self.project)
        for domain in domains:
            self._log("Symlinking CNAME: %s" % domain.domain)
            docs_dir = self.project.doc_path
            # New symlink that properly respects public/private
            new_symlink = os.path.join(self.CNAME_ROOT, domain.domain)
            symlink = os.path.join(
                getattr(settings, 'SITE_ROOT'),
                'cnametoproject',
                domain.domain,
            )

            # Make sure containing directories exist
            run_on_app_servers('mkdir -p %s' %
                               os.path.sep.join(
                                   symlink.split(os.path.sep)[:-1]
                               ))
            run_on_app_servers('mkdir -p %s' %
                               os.path.sep.join(
                                   new_symlink.split(os.path.sep)[:-1]
                               ))

            # Create proper symlinks
            run_on_app_servers('ln -nsf %s %s' %
                               (docs_dir, new_symlink))
            run_on_app_servers('ln -nsf %s %s' %
                               (docs_dir, symlink))

    def symlink_subprojects(self):
        """Symlink project subprojects

        Link from HOME/user_builds/project/subprojects/<project> ->
                  HOME/user_builds/<project>/rtd-builds/
        """
        # Subprojects
        rels = self.project.subprojects.all()
        for rel in rels:
            # A mapping of slugs for the subproject URL to the actual built
            # documentation
            from_to = OrderedDict({rel.child.slug: rel.child.slug})
            if rel.alias:
                from_to[rel.alias] = rel.child.slug
            for from_slug, to_slug in from_to.items():
                self._log("Symlinking subproject: %s" % from_slug)
                # The directory for this specific subproject

                new_symlink = os.path.join(self.SUBPROJECT_ROOT, from_slug)
                symlink = self.project.subprojects_symlink_path(from_slug)

                docs_dir = os.path.join(
                    settings.DOCROOT, to_slug, 'rtd-builds')

                run_on_app_servers(
                    'mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))
                run_on_app_servers(
                    'mkdir -p %s' % '/'.join(new_symlink.split('/')[:-1]))

                # Where the actual docs live
                run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))


class Public(Symlink):

    CNAME_ROOT = os.path.join(settings.SITE_ROOT, 'public_cnames')
    SUBPROJECT_ROOT = os.path.join(settings.SITE_ROOT, 'public_subprojects')


class Private(Symlink):

    CNAME_ROOT = os.path.join(settings.SITE_ROOT, 'private_cnames')
    SUBPROJECT_ROOT = os.path.join(settings.SITE_ROOT, 'private_subprojects')

    def symlink_translations(self, project):
        """Symlink project translations

        Link from HOME/user_builds/project/translations/<lang> ->
                  HOME/user_builds/<project>/rtd-builds/
        """
        translations = {}

        if getattr(settings, 'DONT_HIT_DB', True):
            for trans in (api
                          .project(project.pk)
                          .translations.get()['translations']):
                translations[trans['language']] = trans['slug']
        else:
            for trans in project.translations.all():
                translations[trans.language] = trans.slug

        # Default language, and pointer for 'en'
        version_slug = project.slug.replace('_', '-')
        translations[project.language] = version_slug
        if 'en' not in translations:
            translations['en'] = version_slug

        run_on_app_servers(
            'mkdir -p {0}'
            .format(os.path.join(project.doc_path, 'translations')))

        for (language, slug) in translations.items():
            log.debug(LOG_TEMPLATE.format(
                project=project.slug,
                version=project.get_default_version(),
                msg="Symlinking translation: %s->%s" % (language, slug)
            ))

            # The directory for this specific translation
            symlink = project.translations_symlink_path(language)
            translation_path = os.path.join(
                settings.DOCROOT, slug, 'rtd-builds')
            run_on_app_servers(
                'ln -nsf {0} {1}'.format(translation_path, symlink))

    def symlink_single_version(self, project):
        """Symlink project single version

        Link from HOME/user_builds/<project>/single_version ->
                  HOME/user_builds/<project>/rtd-builds/<default_version>/
        """
        default_version = project.get_default_version()
        log.debug(LOG_TEMPLATE
                  .format(project=project.slug, version=default_version,
                          msg="Symlinking single_version"))

        # The single_version directory
        symlink = project.single_version_symlink_path()
        run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))

        # Where the actual docs live
        docs_dir = os.path.join(
            settings.DOCROOT, project.slug, 'rtd-builds', default_version)
        run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))

    def remove_symlink_single_version(self, project):
        """Remove single_version symlink"""
        log.debug(LOG_TEMPLATE.format(
            project=project.slug,
            version=project.get_default_version(),
            msg="Removing symlink for single_version")
        )
        symlink = project.single_version_symlink_path()
        run_on_app_servers('rm -f %s' % symlink)
