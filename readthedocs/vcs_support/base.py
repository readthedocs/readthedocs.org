"""Base classes for VCS backends."""

import os

import structlog

from readthedocs.core.utils.filesystem import safe_rmtree
from readthedocs.doc_builder.exceptions import BuildCancelled
from readthedocs.doc_builder.exceptions import BuildUserError
from readthedocs.projects.exceptions import RepositoryError


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


# TODO: merge this class with Git VCS class to simplify the code.
class BaseVCS:
    """
    Base for VCS Classes.

    VCS commands are executed inside a ``BaseBuildEnvironment`` subclass.
    """

    # =========================================================================
    # General methods
    # =========================================================================

    # Defining a base API, so we'll have unused args
    # pylint: disable=unused-argument
    def __init__(self, project, version, environment, **kwargs):
        self.default_branch = project.default_branch
        self.project = project
        self.version = version
        self.name = project.name
        self.repo_url = project.clean_repo
        self.working_dir = project.checkout_path(self.version.slug)
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
