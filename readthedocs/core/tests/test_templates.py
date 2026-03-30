"""Test that all templates compile without syntax errors."""

import os

from django.template import engines
from django.test import TestCase


class TemplateCompilationTest(TestCase):
    """Ensure all project templates are valid and free of syntax errors."""

    def test_all_templates_compile(self):
        """
        Load and compile every template to catch TemplateSyntaxErrors.

        This iterates over all .html and .txt template files in the configured
        template directories and attempts to compile them. Any template with a
        syntax error will cause this test to fail.
        """
        django_engine = engines["django"]
        template_dirs = django_engine.dirs

        errors = []
        for template_dir in template_dirs:
            for root, _dirs, files in os.walk(template_dir):
                for filename in files:
                    if not filename.endswith((".html", ".txt", ".xml")):
                        continue
                    filepath = os.path.join(root, filename)
                    template_name = os.path.relpath(filepath, template_dir)
                    try:
                        django_engine.get_template(template_name)
                    except Exception as e:
                        errors.append(f"{template_name}: {e}")

        if errors:
            self.fail(
                f"Found {len(errors)} template(s) with errors:\n"
                + "\n".join(errors)
            )
