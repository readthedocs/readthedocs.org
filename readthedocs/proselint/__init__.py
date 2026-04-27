"""
Module for the proselint addon.

Runs proselint over the built HTML of a version and stores the results as a
JSON sidecar in build media storage. The frontend addon then fetches that
JSON and overlays the warnings on the rendered page.

The flow is:

- A build is triggered for a version.
- After the build succeeds, the indexer task walks the HTML files in storage,
  extracts the textual content of block-level elements with selectolax, runs
  proselint over each block, and accumulates the warnings.
- The warnings are written to a single ``proselint.json`` report in the diff
  media storage path for the version.
- The proxito addons API exposes the URL to this report so the frontend can
  fetch it and render the warnings inline.
"""

import json

import structlog

from readthedocs.builds.models import Version
from readthedocs.projects.constants import MEDIA_TYPE_PROSELINT
from readthedocs.proselint.dataclasses import ProselintReport
from readthedocs.storage import build_media_storage


log = structlog.get_logger(__name__)

REPORT_FILE_NAME = "proselint.json"


def get_report_path(version: Version) -> str:
    return version.get_storage_path(
        media_type=MEDIA_TYPE_PROSELINT,
        filename=REPORT_FILE_NAME,
    )


def get_report(version: Version) -> ProselintReport | None:
    """Return the proselint report for a version, or ``None`` if missing."""
    path = get_report_path(version)
    try:
        with build_media_storage.open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        return None

    return ProselintReport.from_dict(data)


def write_report(version: Version, report: ProselintReport) -> None:
    path = get_report_path(version)
    with build_media_storage.open(path, "w") as f:
        json.dump(report.as_dict(), f)
