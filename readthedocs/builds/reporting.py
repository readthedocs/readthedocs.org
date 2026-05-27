from dataclasses import dataclass

from django.conf import settings
from django.template.loader import render_to_string

from readthedocs.builds.models import Build
from readthedocs.filetreediff import get_diff_for_build
from readthedocs.filetreediff.dataclasses import FileTreeDiff


@dataclass
class BuildOverview:
    content: str
    diff: FileTreeDiff


def get_build_overview(build: Build) -> BuildOverview | None:
    """
    Generate a build overview for the given build.

    The overview includes a diff of the files changed between this build and
    the build pinned as the diff base (the base version's latest successful
    build at PR-open time, for PR builds).

    The returned string is rendered using a Markdown template,
    which can be included in a comment on a pull request.
    """
    diff = get_diff_for_build(build)
    if not diff:
        return None

    content = render_to_string(
        "core/build-overview.md",
        {
            "PRODUCTION_DOMAIN": settings.PRODUCTION_DOMAIN,
            "project": build.project,
            "current_version": diff.current_version,
            "current_version_build": diff.current_version_build,
            "base_version": diff.base_version,
            "base_version_build": diff.base_version_build,
            "diff": diff,
        },
    )
    return BuildOverview(
        content=content,
        diff=diff,
    )
