"""Notifications related to projects."""
import textwrap

from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import gettext_noop as _

from readthedocs.core.permissions import AdminPermission
from readthedocs.notifications.constants import ERROR, INFO, WARNING
from readthedocs.notifications.email import EmailNotification
from readthedocs.notifications.messages import Message, registry
from readthedocs.projects.exceptions import (
    ProjectConfigurationError,
    RepositoryError,
    SyncRepositoryLocked,
    UserFileNotFound,
)
from readthedocs.projects.models import Project


class NewDashboardNotification(EmailNotification):

    """
    Notification about new dashboard rollout and changes for Business users.

    To send:

        for user in NewDashboardNotification.for_admins():
            notify = NewDashboardNotificaiton(user, user)
            notify.send()

    NOTE: This can be removed with RTD_EXT_THEME_ENABLED.
    """

    app_templates = "projects"
    name = "new_dashboard"
    subject = "Upcoming changes to our dashboard"

    @staticmethod
    def for_projects():
        # Only send to admin users of recently built projects
        projects = (
            Project.objects.filter(builds__date__gte=timezone.datetime(2023, 1, 1))
            .annotate(successful_builds=Count("builds__success"))
            .filter(successful_builds__gte=3)
            .distinct()
            .order_by("slug")
        )

        # Filter out projects that are spam. This is conditional as this module
        # doesn't seem available in our tests.
        try:
            from readthedocsext.spamfighting.utils import spam_score

            projects = filter(lambda p: spam_score(p) < 200, projects)

            # Convert back to queryset
            return Project.objects.filter(slug__in=[p.slug for p in projects])
        except ImportError:
            return projects

    @staticmethod
    def for_admins(projects=None):
        if projects is None:
            projects = NewDashboardNotification.for_projects()
        usernames = set()
        for project in projects:
            usernames.update(
                set(AdminPermission.admins(project).values_list("username", flat=True))
            )

        return User.objects.filter(username__in=usernames)


MESSAGE_PROJECT_SKIP_BUILDS = "project:invalid:skip-builds"
MESSAGE_PROJECT_ADDONS_BY_DEFAULT = "project:addons:by-default"
messages = [
    Message(
        id=MESSAGE_PROJECT_SKIP_BUILDS,
        header=_("Builds skipped for this project"),
        body=_(
            textwrap.dedent(
                """
            Your project is currently disabled for abuse of the system.
            Please make sure it isn't using unreasonable amounts of resources or triggering lots of builds in a short amount of time.
            Please <a href="mailto:{{SUPPORT_EMAIL}}">contact support</a> to get your project re-enabled.
            """
            ).strip(),
        ),
        type=INFO,
    ),
    Message(
        id=RepositoryError.GENERIC,
        header=_("Error while cloning the repository"),
        body=_(
            textwrap.dedent(
                """
            There was a problem cloning your repository.
            Please check the command output for more information.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.DUPLICATED_RESERVED_VERSIONS,
        header=_("Duplicated reserved versions"),
        body=_(
            textwrap.dedent(
                """
            You can not have two versions with the name latest or stable.
            Ensure you don't have both a branch and a tag with this name.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.FAILED_TO_CHECKOUT,
        header=_("Error while checking out the repository"),
        body=_(
            textwrap.dedent(
                """
            Failed to checkout revision: <code>{{revision}}</code>
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.CLONE_ERROR_WITH_PRIVATE_REPO_ALLOWED,
        header=_("Error while cloning the repository"),
        body=_(
            textwrap.dedent(
                """
            There was a problem connecting to your repository,
            ensure that your repository URL is correct.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.CLONE_ERROR_WITH_PRIVATE_REPO_NOT_ALLOWED,
        header=_("Error while cloning the repository"),
        body=_(
            textwrap.dedent(
                """
            There was a problem connecting to your repository,
            ensure that your repository URL is correct and your repository is public.
            Private repositories are not supported.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.UNSUPPORTED_VCS,
        header=_("Repository type not suported"),
        body=_(
            textwrap.dedent(
                """
                Subversion, Mercurial, and Bazaar are not supported anymore.
                Read more about this deprecation in <a href="https://about.readthedocs.com/blog/2024/02/drop-support-for-subversion-mercurial-bazaar/">our blog</a>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ProjectConfigurationError.NOT_FOUND,
        header=_("Sphinx configuration file is missing"),
        body=_(
            textwrap.dedent(
                """
            A configuration file was not found.
            Make sure you have a <code>conf.py</code> file in your repository.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ProjectConfigurationError.MULTIPLE_CONF_FILES,
        header=_("Multiple Sphinx configuration files found"),
        body=_(
            textwrap.dedent(
                """
            We found more than one <code>conf.py</code> and are not sure which one to use.
            Please, specify the correct file under the Advanced settings tab
            in the project's Admin.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=UserFileNotFound.FILE_NOT_FOUND,
        header=_("Expected file not found"),
        body=_(
            textwrap.dedent(
                """
            The file <code>{{filename}}</code> doesn't exist. Make sure it's a valid file path.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=SyncRepositoryLocked.REPOSITORY_LOCKED,
        header=_("Repository locked"),
        body=_(
            textwrap.dedent(
                """
                We can't perform the versions/branches synchronize at the moment.
                There is another sync already running.
                """
            ).strip(),
        ),
        type=WARNING,
    ),
    # Temporary notification until October 7th.
    Message(
        id=MESSAGE_PROJECT_ADDONS_BY_DEFAULT,
        header=_(
            """Read the Docs Addons were enabled by default on October 7th, 2024"""
        ),
        body=_(
            textwrap.dedent(
                """
                Read the <a href="https://about.readthedocs.com/blog/2024/07/addons-by-default/" target="_blank">full announcement in our blog</a>
                to know if your project is affected and how to update.
                """
            ).strip(),
        ),
        type=INFO,
    ),
]
registry.add(messages)
