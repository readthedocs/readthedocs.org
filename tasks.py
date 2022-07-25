"""Read the Docs tasks."""

import os

from invoke import Collection, task

import common.dockerfiles.tasks
import common.tasks

ROOT_PATH = os.path.dirname(__file__)


namespace = Collection()

namespace.add_collection(
    Collection(
        common.tasks.setup_labels,
    ),
    name='github',
)

namespace.add_collection(
    Collection.from_module(
        common.dockerfiles.tasks,
        config={
            'container_prefix': 'community',
        },
    ),
    name='docker',
)

@task
def docs(ctx, regenerate_config=False, push=False):
    """Pull and push translations to Transifex for our docs"""
    with ctx.cd(os.path.join(ROOT_PATH, 'docs')):
        # Update our translations
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
        docs,
    ),
    name='l10n',
)
