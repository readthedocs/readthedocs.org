from django.template.loader import render_to_string

from readthedocs.builds.models import Build
from readthedocs.filetreediff import get_diff


def get_build_report(build: Build):
    project = build.project
    base_version = project.addons.options_base_version or project.get_latest_version()
    if not base_version:
        return None

    diff = get_diff(
        current_version=build.version,
        base_version=base_version,
    )

    if not diff:
        return None

    return render_to_string(
        "core/build-overview.md",
        {
            "project": project,
            "current_version": diff.current_version,
            "current_version_build": diff.current_version_build,
            "base_version": diff.base_version,
            "base_version_build": diff.base_version_build,
            "diff": diff,
        },
    )
