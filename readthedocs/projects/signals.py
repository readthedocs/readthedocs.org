"""Project signals."""


import django.dispatch
import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.builds.models import Version
from readthedocs.projects.constants import MKDOCS
from readthedocs.projects.models import AddonsConfig

log = structlog.get_logger(__name__)


before_vcs = django.dispatch.Signal()

before_build = django.dispatch.Signal()
after_build = django.dispatch.Signal()

project_import = django.dispatch.Signal()

# Used to purge files from the CDN
files_changed = django.dispatch.Signal()


@receiver(post_save, sender=Version)
def enable_addons_on_new_mkdocs_projects(instance, *args, **kwargs):
    """
    Enable Addons on MkDocs projects.

    We removed all the `mkdocs.yml` manipulation that set the theme to `readthedocs` if
    undefined and injects JS and CSS files to show the old flyout.

    Now, we are enabling addons by default on MkDocs projects to move forward
    with the idea of removing the magic executed on behalves the users and
    promote addons more.

    Reference https://github.com/readthedocs/addons/issues/72#issuecomment-1926647293
    """
    version = instance
    project = instance.project

    if version.documentation_type == MKDOCS:
        config, created = AddonsConfig.objects.get_or_create(project=project)
        if created:
            log.info(
                "Creating AddonsConfig automatically for MkDocs project.",
                project_slug=project.slug,
            )
            config.enabled = True
            config.save()
