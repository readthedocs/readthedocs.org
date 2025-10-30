from collections import Counter

import structlog

from readthedocs.builds import tasks as build_tasks
from readthedocs.builds.constants import LATEST_VERBOSE_NAME
from readthedocs.builds.constants import STABLE_VERBOSE_NAME
from readthedocs.builds.models import APIVersion

from ..exceptions import RepositoryError
from ..models import Feature


log = structlog.get_logger(__name__)


class SyncRepositoryMixin:
    """Mixin that handles the VCS sync/update."""

    def get_version(self, version_pk):
        """
        Retrieve version data from the API.

        :param version_pk: version pk to sync
        :type version_pk: int
        :returns: a data-complete version object
        :rtype: builds.models.APIVersion
        """
        version_data = self.data.api_client.version(version_pk).get()
        return APIVersion(**version_data)

    def sync_versions(self, vcs_repository):
        """
        Update tags/branches via a Celery task.

        .. note::

           It may trigger a new build to the stable version.
        """

        # NOTE: `sync_versions` should receive `tags` and `branches` already
        # and just validate them trigger the task. All the other logic should
        # be done by the BuildDirector or the VCS backend. We should not
        # check this here and do not depend on ``vcs_repository``.
        sync_tags = not self.data.project.has_feature(Feature.SKIP_SYNC_TAGS)
        sync_branches = not self.data.project.has_feature(Feature.SKIP_SYNC_BRANCHES)
        try:
            branches, tags = vcs_repository.lsremote(
                include_tags=sync_tags,
                include_branches=sync_branches,
            )
        except RepositoryError:
            log.warning(
                "Error running lsremote to get versions from the repository.",
                exc_info=True,
            )
            return

        tags_data = [
            {
                "identifier": v.identifier,
                "verbose_name": v.verbose_name,
            }
            for v in tags
        ]

        branches_data = [
            {
                "identifier": v.identifier,
                "verbose_name": v.verbose_name,
            }
            for v in branches
        ]

        log.debug("Synchronizing versions.", branches=branches, tags=tags)

        self.validate_duplicate_reserved_versions(
            tags_data=tags_data,
            branches_data=branches_data,
        )

        build_tasks.sync_versions_task.delay(
            project_pk=self.data.project.pk,
            tags_data=tags_data,
            branches_data=branches_data,
        )

    def validate_duplicate_reserved_versions(self, tags_data, branches_data):
        """
        Check if there are duplicated names of reserved versions.

        The user can't have a branch and a tag with the same name of
        ``latest`` or ``stable``. Raise a RepositoryError exception
        if there is a duplicated name.

        :param data: Dict containing the versions from tags and branches
        """
        version_names = [version["verbose_name"] for version in tags_data + branches_data]
        counter = Counter(version_names)
        for reserved_name in [STABLE_VERBOSE_NAME, LATEST_VERBOSE_NAME]:
            if counter[reserved_name] > 1:
                raise RepositoryError(
                    RepositoryError.DUPLICATED_RESERVED_VERSIONS,
                )
