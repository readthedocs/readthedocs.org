from dataclasses import dataclass

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from readthedocs.builds.models import Build
from readthedocs.filetreediff import get_diff
from readthedocs.filetreediff.dataclasses import FileTreeDiff


@dataclass
class BuildOverview:
    content: str
    diff: FileTreeDiff | None = None

    @property
    def should_create_comment(self) -> bool:
        """
        Whether this overview is worth starting a new comment for.

        A build that changed nothing only refreshes a comment that already exists,
        so we don't add noise to pull requests that never touch the documentation.
        A failed build is always worth reporting: it's the moment the reader most
        needs to know, and leaving the previous comment up would claim a preview
        is ready when it isn't.
        """
        if self.diff is None:
            return True
        return bool(self.diff.files)


def get_build_overview(build: Build) -> BuildOverview | None:
    """
    Generate a build overview for the given build.

    The overview includes a diff of the files changed between the current
    build and the base version of the project (latest by default).

    The returned string is rendered using a Markdown template,
    which can be included in a comment on a pull request.
    """
    project = build.project
    context = {
        "PRODUCTION_DOMAIN": settings.PRODUCTION_DOMAIN,
        "project": project,
        "build": build,
        # Overridden below with the build the manifest came from, which is the
        # one the file list actually describes.
        "current_version_build": build,
        # The comment is re-rendered and edited on every build,
        # so render time is when its contents were last refreshed.
        "last_updated": timezone.now(),
    }

    if not build.success:
        # There is no diff to report: the build produced no new manifest, and the
        # last successful one describes a commit this pull request has moved past.
        return BuildOverview(content=render_to_string("core/build-overview.md", context))

    base_version = project.addons.options_base_version or project.get_latest_version()
    if not base_version:
        return None

    diff = get_diff(
        current_version=build.version,
        base_version=base_version,
    )
    if not diff:
        return None

    context |= {
        "preview_url": diff.current_version.get_absolute_url(),
        "current_version_build": diff.current_version_build,
        "diff": diff,
    }
    return BuildOverview(
        content=render_to_string("core/build-overview.md", context),
        diff=diff,
    )
