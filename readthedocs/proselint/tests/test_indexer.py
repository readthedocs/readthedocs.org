"""Unit tests for the proselint indexer's HTML lint helpers."""

import pytest


pytest.importorskip("proselint")
pytest.importorskip("selectolax")

from readthedocs.proselint.indexer import lint_html  # noqa: E402


HTML_WITH_HIT = """
<html>
  <body>
    <main>
      <p>The very first thing to notice is that this is bad style.</p>
      <pre><code>very very nested</code></pre>
    </main>
  </body>
</html>
"""

HTML_CODE_ONLY = """
<html>
  <body>
    <main>
      <pre><code>very very very</code></pre>
    </main>
  </body>
</html>
"""


def test_lint_html_returns_warnings_for_prose():
    warnings = lint_html(HTML_WITH_HIT)
    assert warnings, "expected at least one proselint warning"

    warning = warnings[0]
    assert warning.selector
    assert warning.snippet
    assert warning.check
    assert warning.message


def test_lint_html_skips_code_blocks():
    # The text only appears inside a <pre><code>, so nothing should be linted.
    assert lint_html(HTML_CODE_ONLY) == []


def test_lint_html_handles_missing_body():
    assert lint_html("<not really html>") == []
