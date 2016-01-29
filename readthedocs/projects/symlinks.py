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


def symlink_cnames(project):
    """Symlink project CNAME domains

    OLD
    Link from HOME/user_builds/cnames/<cname> ->
              HOME/user_builds/<project>/rtd-builds/
    NEW
    Link from HOME/user_builds/cnametoproject/<cname> ->
              HOME/user_builds/<project>/
    """
    domains = Domain.objects.filter(project=project)
    for domain in domains:
        log.debug(LOG_TEMPLATE.format(
            project=project.slug,
            version=project.get_default_version(),
            msg="Symlinking CNAME: %s" % domain.domain)
        )
        docs_dir = project.rtd_build_path()
        # Chop off the version from the end.
        docs_dir = '/'.join(docs_dir.split('/')[:-1])
        # Old symlink location -- Keep this here til we change nginx over
        symlink = project.cnames_symlink_path(domain.domain)
        run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))
        run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))
        # New symlink location
        new_docs_dir = project.doc_path
        new_cname_symlink = os.path.join(
            getattr(settings, 'SITE_ROOT'),
            'cnametoproject',
            domain.domain,
        )
        run_on_app_servers('mkdir -p %s' % '/'.join(new_cname_symlink.split('/')[:-1]))
        run_on_app_servers('ln -nsf %s %s' % (new_docs_dir, new_cname_symlink))


def symlink_subprojects(project):
    """Symlink project subprojects

    Link from HOME/user_builds/project/subprojects/<project> ->
              HOME/user_builds/<project>/rtd-builds/
    """
    # Subprojects
    rels = project.subprojects.all()
    for rel in rels:
        # A mapping of slugs for the subproject URL to the actual built documentation
        from_to = OrderedDict({rel.child.slug: rel.child.slug})
        if rel.alias:
            from_to[rel.alias] = rel.child.slug
        # Fix underscore in slugs
        if '_' in rel.child.slug:
            from_to[rel.child.slug.replace('_', '-')] = rel.child.slug
        for from_slug, to_slug in from_to.items():
            log.debug(LOG_TEMPLATE
                      .format(project=project.slug,
                              version=project.get_default_version(),
                              msg="Symlinking subproject: %s" % from_slug))

            # The directory for this specific subproject
            symlink = project.subprojects_symlink_path(from_slug)
            run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))

            # Where the actual docs live
            docs_dir = os.path.join(settings.DOCROOT, to_slug, 'rtd-builds')
            run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))


def symlink_translations(project):
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
        translation_path = os.path.join(settings.DOCROOT, slug, 'rtd-builds')
        run_on_app_servers('ln -nsf {0} {1}'.format(translation_path, symlink))


def symlink_single_version(project):
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
    docs_dir = os.path.join(settings.DOCROOT, project.slug, 'rtd-builds', default_version)
    run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))


def remove_symlink_single_version(project):
    """Remove single_version symlink"""
    log.debug(LOG_TEMPLATE.format(
        project=project.slug,
        version=project.get_default_version(),
        msg="Removing symlink for single_version")
    )
    symlink = project.single_version_symlink_path()
    run_on_app_servers('rm -f %s' % symlink)
