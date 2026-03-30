from pathlib import Path

from django.apps import apps
from django.template import TemplateSyntaxError, engines
from django.template.loader import get_template
from django.test import TestCase


class TestTemplateSyntax(TestCase):
    """
    Ensure all Django templates have valid syntax.

    Loads every template visible to Django's template engine and checks
    for TemplateSyntaxError. This catches issues in our own templates,
    ext-theme overrides, and third-party app templates before they
    reach production.

    See https://github.com/readthedocs/readthedocs.org/issues/6290
    """

    TEMPLATE_EXTENSIONS = {".html", ".txt"}

    # Templates with known syntax issues from dependencies.
    # Each entry should have a comment explaining the issue
    # and when it can be removed.
    KNOWN_ISSUES = {
        # dj_pagination uses {% ifequal %} removed in Django 5.1.
        "pagination/pagination.html",
        # ext-theme flagging templates reference a removed 'flagging' tag
        # library. Remove these once ext-theme drops the flagging/ directory
        # and projects/includes/flagging.html.
        "flagging/flag_confirm.html",
        "flagging/flag_success.html",
        "projects/includes/flagging.html",
    }

    def _get_all_template_names(self):
        """Collect all template names from DIRS and app template directories."""
        engine = engines["django"]
        template_names = set()

        for template_dir in engine.dirs:
            self._collect_templates(Path(template_dir), template_names)

        for app_config in apps.get_app_configs():
            self._collect_templates(
                Path(app_config.path) / "templates",
                template_names,
            )

        return sorted(template_names)

    def _collect_templates(self, template_dir, template_names):
        if not template_dir.exists():
            return
        for template_file in template_dir.rglob("*"):
            if template_file.suffix in self.TEMPLATE_EXTENSIONS:
                template_names.add(
                    str(template_file.relative_to(template_dir))
                )

    def test_all_templates_have_valid_syntax(self):
        """Load every template to verify it has valid syntax."""
        template_names = self._get_all_template_names()
        self.assertGreater(len(template_names), 0, "No templates found")

        errors = []
        for name in template_names:
            if name in self.KNOWN_ISSUES:
                continue
            try:
                get_template(name)
            except TemplateSyntaxError as e:
                errors.append(f"  {name}: {e}")

        if errors:
            self.fail(
                f"Template syntax errors in {len(errors)} template(s):\n"
                + "\n".join(errors)
            )
