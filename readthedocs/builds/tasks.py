import datetime
import logging
import shutil

from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Version, Build
from readthedocs.doc_builder.constants import DOCKER_LIMITS
from readthedocs.projects.constants import LOG_TEMPLATE

from readthedocs.worker import app


log = logging.getLogger(__name__)


@app.task(queue='web')
def fileify(version_pk, commit):
    """
    Create ImportedFile objects for all of a version's files.

    This is so we have an idea of what files we have in the database.
    """
    version = Version.objects.get(pk=version_pk)
    project = version.project

    if not commit:
        log.info(
            LOG_TEMPLATE.format(
                project=project.slug,
                version=version.slug,
                msg=(
                    'Imported File not being built because no commit '
                    'information'
                ),
            )
        )
        return

    path = project.rtd_build_path(version.slug)
    if path:
        log.info(
            LOG_TEMPLATE.format(
                project=version.project.slug,
                version=version.slug,
                msg='Creating ImportedFiles',
            )
        )
        from readthedocs.projects.tasks import _manage_imported_files
        _manage_imported_files(version, path, commit)
    else:
        log.info(
            LOG_TEMPLATE.format(
                project=project.slug,
                version=version.slug,
                msg='No ImportedFile files',
            )
        )


# Random Tasks
@app.task()
def remove_dir(path):
    """
    Remove a directory on the build/celery server.

    This is mainly a wrapper around shutil.rmtree so that app servers can kill
    things on the build server.
    """
    log.info('Removing %s', path)
    shutil.rmtree(path, ignore_errors=True)


@app.task()
def clear_artifacts(paths):
    """
    Remove artifacts from the web servers.

    :param paths: list containing PATHs where production media is on disk
        (usually ``Version.get_artifact_paths``)
    """
    for path in paths:
        remove_dir(path)


@app.task()
def finish_inactive_builds():
    """
    Finish inactive builds.

    A build is consider inactive if it's not in ``FINISHED`` state and it has been
    "running" for more time that the allowed one (``Project.container_time_limit``
    or ``DOCKER_LIMITS['time']`` plus a 20% of it).

    These inactive builds will be marked as ``success`` and ``FINISHED`` with an
    ``error`` to be communicated to the user.
    """
    time_limit = int(DOCKER_LIMITS['time'] * 1.2)
    delta = datetime.timedelta(seconds=time_limit)
    query = (~Q(state=BUILD_STATE_FINISHED) &
             Q(date__lte=timezone.now() - delta))

    builds_finished = 0
    builds = Build.objects.filter(query)[:50]
    for build in builds:

        if build.project.container_time_limit:
            custom_delta = datetime.timedelta(
                seconds=int(build.project.container_time_limit),
            )
            if build.date + custom_delta > timezone.now():
                # Do not mark as FINISHED builds with a custom time limit that wasn't
                # expired yet (they are still building the project version)
                continue

        build.success = False
        build.state = BUILD_STATE_FINISHED
        build.error = _(
            'This build was terminated due to inactivity. If you '
            'continue to encounter this error, file a support '
            'request with and reference this build id ({0}).'.format(build.pk),
        )
        build.save()
        builds_finished += 1

    log.info(
        'Builds marked as "Terminated due inactivity": %s',
        builds_finished,
    )
