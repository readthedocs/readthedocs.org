"""
Read the Docs tasks
"""

from __future__ import division, print_function, unicode_literals

import os

from invoke import task, Collection

import common.tasks


ROOT_PATH = os.path.dirname(__file__)


# TODO make these tasks namespaced
# release = Collection(common.tasks.prepare, common.tasks.release)

namespace = Collection(
    common.tasks.prepare,
    common.tasks.release,
    #release=release,
)


# Localization tasks
@task
def push(ctx):
    """Rebuild and push the source language to Transifex"""
    with ctx.cd(os.path.join(ROOT_PATH, 'readthedocs')):
        ctx.run('django-admin makemessages -l en')
        ctx.run('tx push -s')
        ctx.run('django-admin compilemessages -l en')


@task
def pull(ctx):
    """Pull the updated translations from Transifex"""
    with ctx.cd(os.path.join(ROOT_PATH, 'readthedocs')):
        ctx.run('tx pull -f ')
        ctx.run('django-admin makemessages --all')
        ctx.run('django-admin compilemessages')


@task
def docs(ctx, regenerate_config=False, push=False):
    """Pull and push translations to Transifex for our docs"""
    with ctx.cd(os.path.join(ROOT_PATH, 'docs')):
        # Update our tanslations
        ctx.run('tx pull -a')
        # Update resources
        if regenerate_config:
            os.remove(os.path.join(ROOT_PATH, 'docs', '.tx', 'config'))
            ctx.run('sphinx-intl create-txconfig')
        ctx.run('sphinx-intl update-txconfig-resources --transifex-project-name readthedocs-docs')
        # Rebuild
        ctx.run('sphinx-intl build')
        ctx.run('make gettext')
        # Push new ones
        if push:
            ctx.run('tx push -s')


namespace.add_collection(
    Collection(
        push,
        pull,
        docs,
    ),
    name='l10n',
)
