"""Render HTML snapshots of forms changed in PR #1.

Run with the tox env:

    tox -e py312 -- --nomigrations --reuse-db -p no:randomly \\
        scripts/snapshot_pr1_forms.py

It writes three standalone HTML files under ``snapshots/pr1/`` that can be
opened in a browser to visually verify:

1. ``addons_customscript_invalid.html`` — AddonsConfigForm rejecting an
   ``http://`` custom-script URL.
2. ``addons_filetreediff_backslash.html`` — AddonsConfigForm rejecting a
   pattern with a backslash.
3. ``redirect_help_*.html`` — RedirectForm's ``from_url`` help text for each
   redirect type.
"""

from pathlib import Path

import pytest
from django_dynamic_fixture import get

from readthedocs.projects.forms import AddonsConfigForm
from readthedocs.projects.forms import RedirectForm
from readthedocs.projects.models import Project
from readthedocs.redirects.constants import CLEAN_URL_TO_HTML_REDIRECT
from readthedocs.redirects.constants import EXACT_REDIRECT
from readthedocs.redirects.constants import PAGE_REDIRECT


SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "snapshots" / "pr1"


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


def _addons_data(project, **overrides):
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


@pytest.mark.django_db
def test_snapshot_customscript_src_http_rejected(snapshot_dir):
    project = get(Project)
    form = AddonsConfigForm(
        data=_addons_data(
            project,
            customscript_enabled=True,
            customscript_src="http://example.com/custom.js",
        ),
        project=project,
    )
    assert not form.is_valid()

    field = form["customscript_src"]
    body = (
        f"<form>{field.errors}"
        f"<label>{field.label}</label>"
        f"{field}"
        f"<span class='helptext'>{field.help_text}</span>"
        "</form>"
    )
    (snapshot_dir / "addons_customscript_invalid.html").write_text(
        _wrap("AddonsConfigForm — customscript_src (http:// rejected)", body)
    )


@pytest.mark.django_db
def test_snapshot_filetreediff_backslash_rejected(snapshot_dir):
    project = get(Project)
    form = AddonsConfigForm(
        data=_addons_data(
            project,
            filetreediff_enabled=True,
            filetreediff_ignored_files="docs\\*.html",
        ),
        project=project,
    )
    assert not form.is_valid()

    field = form["filetreediff_ignored_files"]
    body = (
        f"<form>{field.errors}"
        f"<label>{field.label}</label>"
        f"{field}"
        f"<span class='helptext'>{field.help_text}</span>"
        "</form>"
    )
    (snapshot_dir / "addons_filetreediff_backslash.html").write_text(
        _wrap("AddonsConfigForm — filetreediff_ignored_files (backslash rejected)", body)
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "redirect_type,label",
    [
        (PAGE_REDIRECT, "page"),
        (EXACT_REDIRECT, "exact"),
        (CLEAN_URL_TO_HTML_REDIRECT, "clean_url_to_html"),
    ],
)
def test_snapshot_redirect_help_text(snapshot_dir, redirect_type, label):
    project = get(Project)
    form = RedirectForm(data={"redirect_type": redirect_type}, project=project)
    # Trigger the bound-form branch so help text is computed from ``data``.
    form.is_valid()

    field = form["from_url"]
    body = (
        f"<form>"
        f"<label>Redirect type: {redirect_type}</label>"
        f"<label>{field.label}</label>"
        f"{field}"
        f"<span class='helptext'>{field.help_text}</span>"
        "</form>"
    )
    (snapshot_dir / f"redirect_help_{label}.html").write_text(
        _wrap(f"RedirectForm — from_url help for type={redirect_type}", body)
    )
