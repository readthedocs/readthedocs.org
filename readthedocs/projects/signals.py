"""Project signals."""

import datetime

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
    Enable Addons on projects created after 2024-04-01.

    We removed all the `mkdocs.yml` manipulation that set the `readthedocs` if
    undefined and injects JS and CSS files to show the old flyout.

    Now, we are enabling addons by default on this projects to move forward
    with this idea of removing the magic executed on behalves the users and
    promote addons more.

    Reference https://github.com/readthedocs/addons/issues/72#issuecomment-1926647293
    """
    project = instance.project

    if (
        project.pub_date
        > datetime.datetime(2023, 4, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        and instance.documentation_type == MKDOCS
    ):
        created, config = AddonsConfig.objects.get_or_create(project=project)
        if created:
            log.info(
                "Creating AddonsConfig automatically for MkDocs project.",
                project_slug=project.slug,
            )
            config.enabled = True
            config.save()
