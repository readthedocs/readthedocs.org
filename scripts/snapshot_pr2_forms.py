"""Render HTML snapshots of the ``options_base_version`` field for PR #2.

Run with the tox env:

    tox -e py312 -- --nomigrations --reuse-db -p no:randomly \\
        scripts/snapshot_pr2_forms.py

It writes standalone HTML files under ``snapshots/pr2/`` that can be opened
in a browser to visually verify:

1. ``addons_base_version_empty.html`` — the project has no internal versions;
   only the "Default (stable or latest)" empty label is offered.
2. ``addons_base_version_populated.html`` — the dropdown lists the project's
   internal (branch/tag) versions but excludes external (pull-request) ones.
3. ``addons_base_version_other_project_rejected.html`` — submitting a version
   that belongs to a different project is rejected with an error message.
"""

from pathlib import Path

import pytest
from django_dynamic_fixture import get

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import TAG
from readthedocs.builds.models import Version
from readthedocs.projects.forms import AddonsConfigForm
from readthedocs.projects.models import Project


SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "snapshots" / "pr2"


def _wrap(title: str, body: str) -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title>"
        "<style>"
        "body{font-family:system-ui;padding:2rem;max-width:720px;}"
        "label{display:block;font-weight:bold;margin-top:1rem}"
        "input,textarea,select{width:100%;padding:.5rem}"
        ".helptext{display:block;color:#555;font-size:.9em;margin-top:.25rem}"
        ".errorlist{color:#b00;margin:.25rem 0;padding-left:1rem}"
        "</style></head><body>"
        f"<h1>{title}</h1>{body}</body></html>"
    )


def _base_data(**overrides):
    data = {
        "enabled": True,
        "options_root_selector": "main",
        "analytics_enabled": False,
        "customscript_enabled": False,
        "customscript_src": "",
        "doc_diff_enabled": False,
        "filetreediff_enabled": False,
        "filetreediff_ignored_files": "",
        "flyout_enabled": True,
        "flyout_sorting": "alphabetically",
        "flyout_sorting_latest_stable_at_beginning": True,
        "flyout_sorting_custom_pattern": None,
        "flyout_position": "bottom-left",
        "hotkeys_enabled": False,
        "search_enabled": False,
        "linkpreviews_enabled": False,
        "notifications_enabled": True,
        "notifications_show_on_latest": True,
        "notifications_show_on_non_stable": True,
        "notifications_show_on_external": True,
    }
    data.update(overrides)
    return data


@pytest.fixture
def snapshot_dir():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SNAPSHOT_DIR


def _render(field):
    return (
        f"<form>{field.errors}"
        f"<label>{field.label}</label>"
        f"{field}"
        f"<span class='helptext'>{field.help_text}</span>"
        "</form>"
    )


@pytest.mark.django_db
def test_snapshot_base_version_empty(snapshot_dir):
    project = get(Project)
    project.versions.all().delete()

    form = AddonsConfigForm(project=project)
    field = form["options_base_version"]
    (snapshot_dir / "addons_base_version_empty.html").write_text(
        _wrap(
            "AddonsConfigForm — options_base_version (no internal versions)",
            _render(field),
        )
    )


@pytest.mark.django_db
def test_snapshot_base_version_populated(snapshot_dir):
    project = get(Project)
    project.versions.all().delete()
    get(Version, project=project, slug="v1", verbose_name="v1", type=BRANCH)
    get(Version, project=project, slug="stable", verbose_name="stable", type=TAG)
    # External versions must NOT appear in the dropdown.
    get(Version, project=project, slug="42", verbose_name="42", type=EXTERNAL)

    form = AddonsConfigForm(project=project)
    field = form["options_base_version"]
    (snapshot_dir / "addons_base_version_populated.html").write_text(
        _wrap(
            "AddonsConfigForm — options_base_version (project versions only)",
            _render(field),
        )
    )


@pytest.mark.django_db
def test_snapshot_base_version_other_project_rejected(snapshot_dir):
    project = get(Project)
    project.versions.all().delete()
    get(Version, project=project, slug="v1", verbose_name="v1", type=BRANCH)
    other_version = get(Version, slug="other", verbose_name="other", type=BRANCH)

    form = AddonsConfigForm(
        data=_base_data(options_base_version=other_version.pk),
        project=project,
    )
    assert not form.is_valid()

    field = form["options_base_version"]
    (snapshot_dir / "addons_base_version_other_project_rejected.html").write_text(
        _wrap(
            "AddonsConfigForm — options_base_version (cross-project rejected)",
            _render(field),
        )
    )
