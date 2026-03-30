"""
Test that all Django templates can be compiled without syntax errors.

See https://github.com/readthedocs/readthedocs.org/issues/6290
"""

import os

from django.apps import apps
from django.conf import settings
from django.template import engines
from django.test import TestCase


class TemplateSyntaxTest(TestCase):
    """Ensure all project templates compile without TemplateSyntaxError."""

    def test_all_templates_compile(self):
        """
        Load and compile every template file found in the project's own
        template directories. If any template has a syntax error,
        ``get_template`` will raise ``TemplateSyntaxError`` and the test
        will fail.
        """
        django_engine = engines["django"]

        errors = []
        for template_path in self._find_project_template_files():
            try:
                django_engine.get_template(template_path)
            except Exception as e:
                errors.append((template_path, e))

        if errors:
            message_parts = [f"Found {len(errors)} template(s) with errors:\n"]
            for path, error in errors:
                message_parts.append(f"  {path}: {error}")
            self.fail("\n".join(message_parts))

    @staticmethod
    def _find_project_template_files():
        """
        Walk template directories that belong to the readthedocs project
        (not third-party packages) and yield relative template paths.
        """
        site_root = settings.SITE_ROOT
        template_dirs = list(engines["django"].dirs)

        for app_config in apps.get_app_configs():
            # Only include apps that live inside the project source tree.
            if not app_config.path.startswith(site_root):
                continue
            template_dir = os.path.join(app_config.path, "templates")
            if os.path.isdir(template_dir):
                template_dirs.append(template_dir)

        seen = set()
        for template_dir in template_dirs:
            for root, _dirs, files in os.walk(template_dir):
                for filename in files:
                    if not filename.endswith((".html", ".txt")):
                        continue
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, template_dir)
                    if rel_path not in seen:
                        seen.add(rel_path)
                        yield rel_path
