"""Render Read the Docs email templates with sample fixtures.

This is preview-only tooling for the MJML migration. It boots a minimal
standalone Django, registers stub URL names that match what the production
templates reference, then renders each fixture to ``emails/preview/out/``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import django
from django.conf import settings
from django.urls import path


REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIRS = [
    REPO_ROOT / "readthedocs" / "templates",
    REPO_ROOT / "readthedocs" / "organizations" / "templates",
    REPO_ROOT / "readthedocs" / "invitations" / "templates",
    REPO_ROOT / "readthedocs" / "subscriptions" / "templates",
    REPO_ROOT / "readthedocs" / "domains" / "templates",
    REPO_ROOT / "readthedocs" / "core" / "templates",
]


def _stub_view(*args, **kwargs):  # pragma: no cover - never called
    raise NotImplementedError


urlpatterns = [
    path("support/", _stub_view, name="support"),
    path("pricing/", _stub_view, name="pricing"),
    path("organizations/<slug:slug>/", _stub_view, name="organization_detail"),
    path("organizations/<slug:slug>/subscription/", _stub_view, name="subscription_detail"),
    path(
        "projects/<slug:project_slug>/domains/<int:domain_pk>/edit/",
        _stub_view,
        name="projects_domains_edit",
    ),
]


def setup_django() -> None:
    if settings.configured:
        return
    settings.configure(
        DEBUG=False,
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=["*"],
        USE_I18N=True,
        USE_TZ=True,
        LANGUAGE_CODE="en",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [str(p) for p in TEMPLATE_DIRS],
                "APP_DIRS": False,
                "OPTIONS": {
                    "builtins": ["django.templatetags.i18n"],
                },
            },
        ],
        INSTALLED_APPS=[],
    )
    django.setup()


def to_namespace(value):
    """Recursively convert dict fixtures to attribute-accessible namespaces.

    Strings prefixed with ``date:`` or ``datetime:`` are parsed into
    ``datetime.date`` / ``datetime.datetime`` so filters like ``|timeuntil``
    work in previews.
    """
    import datetime

    if isinstance(value, dict):
        return SimpleNamespace(**{k: to_namespace(v) for k, v in value.items()})
    if isinstance(value, list):
        return [to_namespace(v) for v in value]
    if isinstance(value, str):
        if value.startswith("date:"):
            return datetime.date.fromisoformat(value.removeprefix("date:"))
        if value.startswith("datetime:"):
            return datetime.datetime.fromisoformat(value.removeprefix("datetime:"))
    return value


def render_fixture(fixture: dict) -> tuple[str, str]:
    from django.template.loader import render_to_string

    template = fixture["template"]
    context = {k: to_namespace(v) for k, v in fixture.get("context", {}).items()}
    html = render_to_string(template, context)
    return fixture["name"], html


def main() -> int:
    setup_django()

    fixtures_path = Path(__file__).parent / "fixtures.json"
    out_dir = Path(__file__).parent / "out"
    out_dir.mkdir(exist_ok=True)

    fixtures = json.loads(fixtures_path.read_text())
    for fixture in fixtures:
        name, html = render_fixture(fixture)
        target = out_dir / f"{name}.html"
        target.write_text(html)
        print(f"rendered {fixture['template']} -> {target.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
