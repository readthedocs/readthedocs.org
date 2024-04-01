"""Base classes for VCS backends."""
import datetime
import os

import pytz
import structlog

from readthedocs.core.utils.filesystem import safe_rmtree
from readthedocs.doc_builder.exceptions import BuildCancelled, BuildUserError
from readthedocs.projects.exceptions import RepositoryError
from django.conf import settings

log = structlog.get_logger(__name__)


class VCSVersion:

    """
    Represents a Version (tag or branch) in a VCS.

    This class should only be instantiated in BaseVCS subclasses.

    It can act as a context manager to temporarily switch to this tag (eg to
    build docs for this tag).
    """

    def __init__(self, repository, identifier, verbose_name):
        self.repository = repository
        self.identifier = identifier
        self.verbose_name = verbose_name

    def __repr__(self):
        return "<VCSVersion: {}:{}".format(
            self.repository.repo_url,
            self.verbose_name,
        )


class Deprecated:
    def __init__(self, *args, **kwargs):
        tzinfo = pytz.timezone("America/Los_Angeles")
        now = datetime.datetime.now(tz=tzinfo)

        # Brownout dates as published in https://about.readthedocs.com/blog/2024/02/drop-support-for-subversion-mercurial-bazaar/
        # fmt: off
        disabled = any([
            # 12 hours browndate
            datetime.datetime(2024, 4, 1, 0, 0, 0, tzinfo=tzinfo) < now < datetime.datetime(2024, 4, 1, 12, 0, 0, tzinfo=tzinfo),
            # 24 hours browndate
            datetime.datetime(2024, 5, 6, 0, 0, 0, tzinfo=tzinfo) < now < datetime.datetime(2024, 5, 7, 0, 0, 0, tzinfo=tzinfo),
            # 48 hours browndate
            datetime.datetime(2024, 5, 20, 0, 0, 0, tzinfo=tzinfo) < now < datetime.datetime(2024, 5, 22, 0, 0, 0, tzinfo=tzinfo),
            # Deprecated after June 3
            datetime.datetime(2024, 6, 3, 0, 0, 0, tzinfo=tzinfo) < now,
        ])
        # fmt: on

        if settings.RTD_ENFORCE_BROWNOUTS_FOR_DEPRECATIONS and disabled:
            from .backends import bzr, hg, svn

            vcs = None
            if isinstance(self, bzr.Backend):
                vcs = "Bazaar"
            elif isinstance(self, svn.Backend):
                vcs = "Subversion"
            elif isinstance(self, hg.Backend):
                vcs = "Mercurial"

            raise BuildUserError(
                message_id=BuildUserError.VCS_DEPRECATED,
                format_values={
                    "vcs": vcs,
                },
            )

        super().__init__(*args, **kwargs)


class BaseVCS:

    """
    Base for VCS Classes.

    VCS commands are executed inside a ``BaseBuildEnvironment`` subclass.
    """

    supports_tags = False  # Whether this VCS supports tags or not.
    supports_branches = False  # Whether this VCS supports branches or not.
    supports_submodules = False  # Whether this VCS supports submodules or not.

    # Whether this VCS supports listing remotes (branches, tags) without cloning
    supports_lsremote = False

    # =========================================================================
    # General methods
    # =========================================================================

    # Defining a base API, so we'll have unused args
    # pylint: disable=unused-argument
    def __init__(
        self,
        project,
        version_slug,
        environment,
        verbose_name=None,
        version_type=None,
        **kwargs
    ):
        self.default_branch = project.default_branch
        self.project = project
        self.name = project.name
        self.repo_url = project.clean_repo
        self.working_dir = project.checkout_path(version_slug)
        # required for External versions
        self.verbose_name = verbose_name
        self.version_type = version_type

        self.environment = environment

    def check_working_dir(self):
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)

    def make_clean_working_dir(self):
        """Ensures that the working dir exists and is empty."""
        safe_rmtree(self.working_dir, ignore_errors=True)
        self.check_working_dir()

    def update(self):
        """
        Update a local copy of the repository in self.working_dir.

        If self.working_dir is already a valid local copy of the repository,
        update the repository, else create a new local copy of the repository.
        """
        self.check_working_dir()

    def run(self, *cmd, **kwargs):
        kwargs.update(
            {
                "cwd": self.working_dir,
                "shell": False,
            }
        )

        try:
            build_cmd = self.environment.run(*cmd, **kwargs)
        except BuildCancelled as exc:
            # Catch ``BuildCancelled`` here and re raise it. Otherwise, if we
            # raise a ``RepositoryError`` then the ``on_failure`` method from
            # Celery won't treat this problem as a ``BuildCancelled`` issue.
            raise BuildCancelled(message_id=BuildCancelled.CANCELLED_BY_USER) from exc
        except BuildUserError as exc:
            # Re raise as RepositoryError to handle it properly from outside
            raise RepositoryError(message_id=RepositoryError.GENERIC) from exc

        # Return a tuple to keep compatibility
        return (build_cmd.exit_code, build_cmd.output, build_cmd.error)

    # =========================================================================
    # Tag / Branch related methods
    # These methods only apply if supports_tags = True and/or
    # support_branches = True
    # =========================================================================

    @property
    def tags(self):
        """
        Returns a list of VCSVersion objects.

        See VCSVersion for more information.
        """
        raise NotImplementedError

    @property
    def branches(self):
        """
        Returns a list of VCSVersion objects.

        See VCSVersion for more information.
        """
        raise NotImplementedError

    @property
    def commit(self):
        """Returns a string representing the current commit."""
        raise NotImplementedError

    def checkout(self, identifier=None):
        """
        Set the state to the given identifier.

        If identifier is None, checkout to the latest revision.

        The type and format of identifier may change from VCS to VCS, so each
        backend is responsible to understand it's identifiers.
        """
        self.check_working_dir()

    def update_submodules(self, config):
        """
        Update the submodules of the current checkout.

        :type config: readthedocs.config.BuildConfigBase
        """
        raise NotImplementedError
