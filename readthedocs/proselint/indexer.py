"""
Indexer that runs proselint over a build's HTML files.

Proselint operates on plain text. We use selectolax to parse the rendered HTML,
walk block-level prose elements (paragraphs, list items, headings, definition
descriptions), and feed each block's text to ``proselint``. Each warning is
anchored back to its source element via a stable CSS selector and the matched
substring, so the frontend can highlight the warning at view time without
needing to count Unicode offsets.

Code-bearing subtrees (``pre``, ``code``, ``samp``, ``kbd``, etc.) and
non-content regions (``nav``, ``script``, ``style``) are skipped to keep noise
down.
"""

import structlog

from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.projects.constants import MEDIA_TYPE_HTML
from readthedocs.projects.models import HTMLFile
from readthedocs.proselint import write_report
from readthedocs.proselint.dataclasses import ProselintFileReport
from readthedocs.proselint.dataclasses import ProselintReport
from readthedocs.proselint.dataclasses import ProselintWarning
from readthedocs.storage import build_media_storage


log = structlog.get_logger(__name__)

# Block-level elements we lint. We skip ``pre`` and ``code`` because proselint
# does not understand markup and would flag identifiers, attribute values, and
# similar noise inside source listings.
LINTABLE_TAGS = ("p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "dd", "dt", "blockquote")

# Subtrees that should never be linted regardless of where they appear.
SKIP_SUBTREE_SELECTORS = (
    "pre",
    "code",
    "samp",
    "kbd",
    "tt",
    "script",
    "style",
    "nav",
    "[role=navigation]",
    "[role=search]",
    ".headerlink",
    ".toctree-wrapper",
)

# proselint check paths whose findings we want to flag as errors rather than
# warnings. Everything else is rendered as a softer suggestion.
ERROR_PREFIXES = ("spelling", "typography", "misc.illogic")


_CHECKS_LOADED = False


def _ensure_checks_loaded():
    """
    Populate the proselint check registry on first use.

    Modern proselint (3.x) ships its checks as a ``__register__`` tuple that
    has to be installed into the ``CheckRegistry`` singleton before linting.
    """
    global _CHECKS_LOADED
    if _CHECKS_LOADED:
        return

    from proselint.checks import __register__ as all_checks
    from proselint.tools import CheckRegistry

    registry = CheckRegistry()
    if not registry.checks:
        registry.register_many(all_checks)
    _CHECKS_LOADED = True


def _selector_for(node) -> str:
    """
    Build a stable ``parent > child:nth-of-type(n)`` selector for a node.

    selectolax doesn't generate selectors for existing nodes, so we walk
    parents up to ``body`` counting same-tag siblings at each step. The
    result is stable as long as the rendered HTML is deterministic (same
    source → same DOM → same selector), which holds for Sphinx and MkDocs
    output.
    """
    parts = []
    current = node
    while current is not None and current.tag not in (None, "html"):
        parent = current.parent
        if parent is None:
            parts.append(current.tag)
            break

        same_tag_siblings = [c for c in parent.iter() if c.tag == current.tag]
        if len(same_tag_siblings) == 1:
            parts.append(current.tag)
        else:
            try:
                index = same_tag_siblings.index(current) + 1
            except ValueError:
                index = 1
            parts.append(f"{current.tag}:nth-of-type({index})")

        if current.tag == "body":
            break
        current = parent

    return " > ".join(reversed(parts))


def _has_skip_ancestor(node) -> bool:
    """Walk up to see if the node is inside a non-prose subtree."""
    skip_tags = {"pre", "code", "samp", "kbd", "tt", "script", "style", "nav"}
    current = node.parent
    while current is not None:
        if current.tag in skip_tags:
            return True
        current = current.parent
    return False


def _severity_for(check_path: str) -> str:
    if any(check_path.startswith(prefix) for prefix in ERROR_PREFIXES):
        return "error"
    return "warning"


def lint_text(text: str) -> list[tuple[str, str, tuple[int, int], list]]:
    """
    Lint a plain-text string and return ``(check_path, message, span, replacements)`` tuples.

    Spans are normalised to 0-based offsets into the original ``text`` (proselint
    internally prepends a newline that shifts spans by one).
    """
    from proselint.tools import LintFile

    _ensure_checks_loaded()

    lint_file = LintFile(source="inline", content=text)
    results = []
    for result in lint_file.lint():
        cr = result.check_result
        start, end = cr.span
        # ``LintFile.__init__`` wraps ``content`` with a leading newline,
        # so spans are off-by-one relative to the caller's text.
        results.append(
            (
                cr.check_path,
                cr.message,
                (max(start - 1, 0), max(end - 1, 0)),
                list(cr.replacements or []),
            )
        )
    return results


def lint_html(html_content: str) -> list[ProselintWarning]:
    """Lint an HTML document and return a list of anchored warnings."""
    from selectolax.parser import HTMLParser

    tree = HTMLParser(html_content)
    body = tree.body
    if body is None:
        return []

    # Strip subtrees we never want to lint, mutating the parsed tree in place.
    for selector in SKIP_SUBTREE_SELECTORS:
        for node in body.css(selector):
            node.decompose()

    warnings: list[ProselintWarning] = []
    for tag in LINTABLE_TAGS:
        for node in body.css(tag):
            if _has_skip_ancestor(node):
                continue

            text = node.text(deep=True, separator=" ", strip=True)
            if not text:
                continue

            try:
                results = lint_text(text)
            except Exception:
                log.exception("proselint failed on element", tag=tag)
                continue

            if not results:
                continue

            selector = _selector_for(node)
            for check_path, message, (start, end), replacements in results:
                snippet = text[start:end].strip()
                if not snippet:
                    continue
                replacement = replacements[0] if replacements else None
                warnings.append(
                    ProselintWarning(
                        selector=selector,
                        snippet=snippet,
                        check=check_path,
                        severity=_severity_for(check_path),
                        message=message,
                        replacement=replacement,
                    )
                )

    return warnings


class ProselintIndexer:
    """
    Indexer that produces a single proselint report per build.

    Duck-types the ``Indexer`` interface from ``readthedocs.projects.tasks.search``
    (we don't subclass to avoid a circular import). For each HTML file in the
    build we lint the textual content of block elements and accumulate the
    warnings, then write a single JSON report to build media storage.
    """

    def __init__(self, version: Version, build: Build):
        self.version = version
        self.build = build
        self._report = ProselintReport()

    def process(self, html_file: HTMLFile, sync_id: int):
        storage_path = self.version.get_storage_path(
            media_type=MEDIA_TYPE_HTML,
            filename=html_file.path,
        )
        try:
            with build_media_storage.open(storage_path, mode="r") as f:
                content = f.read()
        except Exception:
            log.warning("Failed to read HTML for proselint", path=html_file.path)
            return

        warnings = lint_html(content)
        if warnings:
            self._report.add_file(
                ProselintFileReport(path=html_file.path, warnings=warnings)
            )

    def collect(self, sync_id: int):
        # Always write the report — even when empty — so the frontend can
        # distinguish "feature ran, no warnings" from "feature didn't run".
        write_report(self.version, self._report)
