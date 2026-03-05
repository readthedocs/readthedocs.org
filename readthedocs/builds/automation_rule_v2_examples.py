"""
Example usage of the new AutomationRule (V2) model.

This demonstrates the new unified automation rule system that combines
version matching with webhook filtering.
"""

from readthedocs.builds.models import AutomationRule


# Example 1: Activate release tags (version matching only)
# ==========================================================
# This rule activates any version of type "tag" that matches "release-*"
rule_activate_releases = AutomationRule(
    project=my_project,
    priority=0,
    description="Activate release tags",
    version_types=["tag"],  # Apply to tags only
    version_match_pattern=r"^release-.*",  # Match "release-1.0", "release-2.0", etc.
    webhook_filter=None,  # No webhook filtering
    webhook_match_pattern=None,
    action=AutomationRule.ACTIVATE_VERSION_ACTION,
    enabled=True,
)

# Usage in version creation handler:
version = Version(verbose_name="release-1.0", type="tag")
if rule_activate_releases.match(version):
    rule_activate_releases.apply_action(version)
    # Version will be activated


# Example 2: Trigger builds only when documentation files are modified
# ====================================================================
# This rule triggers builds only when specific files change
rule_docs_files = AutomationRule(
    project=my_project,
    priority=1,
    description="Build only when docs are modified",
    version_types=["branch"],  # Apply to branches
    version_match_pattern=r".*",  # Match any version name
    webhook_filter=AutomationRule.WEBHOOK_FILTER_FILE_PATTERN,
    webhook_match_pattern="docs/*,*.rst,.readthedocs.yaml,requirements/docs.txt",
    action=AutomationRule.TRIGGER_BUILD_ACTION,
    enabled=True,
)

# Usage in webhook handler:
version = Version(verbose_name="main", type="branch")
changed_files = ["docs/index.rst", "README.md", "src/code.py"]
if rule_docs_files.match(version, changed_files=changed_files):
    rule_docs_files.apply_action(version)
    # Build will be triggered because "docs/index.rst" matches


# Example 3: Skip builds based on commit message
# ===============================================
# This rule can be used to skip builds when commit contains [skip ci]
rule_skip_ci = AutomationRule(
    project=my_project,
    priority=2,
    description="Detect [skip ci] in commits",
    version_types=["any"],  # Apply to all version types
    version_match_pattern=r".*",  # Match any version name
    webhook_filter=AutomationRule.WEBHOOK_FILTER_COMMIT_MESSAGE,
    webhook_match_pattern=r"\[skip ci\]|\[ci skip\]",
    action=AutomationRule.TRIGGER_BUILD_ACTION,  # Action to take if matched
    enabled=True,
)

# Usage in webhook handler:
version = Version(verbose_name="feature-branch", type="branch")
commit_message = "Update README [skip ci]"
if rule_skip_ci.match(version, commit_message=commit_message):
    # In practice, you'd invert this logic to *skip* the build
    # Or add a new "skip-build" action
    print("Commit message indicates build should be skipped")


# Example 4: Trigger builds only for PRs with specific labels
# ============================================================
# This rule triggers builds only for PRs labeled "documentation"
rule_docs_prs = AutomationRule(
    project=my_project,
    priority=3,
    description="Build only docs-labeled PRs",
    version_types=["external"],  # Apply to external versions (PRs)
    version_match_pattern=r".*",  # Match any PR number/name
    webhook_filter=AutomationRule.WEBHOOK_FILTER_LABEL,
    webhook_match_pattern=r"^(documentation|docs)$",  # Exact match
    action=AutomationRule.TRIGGER_BUILD_ACTION,
    enabled=True,
)

# Usage in webhook handler:
version = Version(verbose_name="42", type="external")  # PR #42
pr_labels = ["bug", "documentation", "enhancement"]
if rule_docs_prs.match(version, labels=pr_labels):
    rule_docs_prs.apply_action(version)
    # Build will be triggered because "documentation" label is present


# Example 5: Match multiple version types
# ========================================
# This powerful feature allows one rule to apply to multiple version types
rule_multi_types = AutomationRule(
    project=my_project,
    priority=4,
    description="Activate semver tags and branches",
    version_types=["tag", "branch"],  # Multiple types!
    version_match_pattern=r"^v\d+\.\d+\.\d+$",  # Match v1.0.0, v2.1.3, etc.
    webhook_filter=None,
    action=AutomationRule.ACTIVATE_VERSION_ACTION,
    enabled=True,
)

# This matches both:
# - Tags named "v1.0.0", "v2.1.3", etc.
# - Branches named "v1.0.0", "v2.1.3", etc.


# Example 6: Combine version matching with file filtering
# ========================================================
# This rule only builds release branches when config files change
rule_combined = AutomationRule(
    project=my_project,
    priority=5,
    description="Build release branches only on config changes",
    version_types=["branch"],
    version_match_pattern=r"^release/\d+\.\d+$",  # Match release/1.0, release/2.1
    webhook_filter=AutomationRule.WEBHOOK_FILTER_FILE_PATTERN,
    webhook_match_pattern=".readthedocs.yaml,requirements/*,pyproject.toml",
    action=AutomationRule.TRIGGER_BUILD_ACTION,
    enabled=True,
)

# Usage:
version = Version(verbose_name="release/2.1", type="branch")
changed_files = [".readthedocs.yaml", "src/main.py"]
if rule_combined.match(version, changed_files=changed_files):
    # Both conditions must match:
    # 1. Version name matches "release/2.1" ✓
    # 2. Changed files include ".readthedocs.yaml" ✓
    rule_combined.apply_action(version)


# Example 7: Use "any" to match all version types
# ================================================
rule_all_types = AutomationRule(
    project=my_project,
    priority=6,
    description="Make all stable versions public",
    version_types=["any"],  # Special value to match all types
    version_match_pattern=r"^(stable|\d+\.\d+)$",
    webhook_filter=None,
    action=AutomationRule.MAKE_VERSION_PUBLIC_ACTION,
    enabled=True,
)


# Example 8: Temporarily disable a rule
# ======================================
rule_disabled = AutomationRule(
    project=my_project,
    priority=7,
    description="Temporarily disabled rule",
    version_types=["tag"],
    version_match_pattern=r"^beta-.*",
    action=AutomationRule.ACTIVATE_VERSION_ACTION,
    enabled=False,  # Rule won't match anything when disabled
)


# Testing the new AutomationRule
# ===============================
def test_automation_rule():
    """Test the new AutomationRule functionality."""

    # Test 1: Version matching only
    rule = AutomationRule(
        version_types=["tag"],
        version_match_pattern=r"^v\d+\.\d+\.\d+$",
        action="activate-version",
        enabled=True,
    )

    version_tag = type("Version", (), {"type": "tag", "verbose_name": "v1.0.0"})()
    version_branch = type("Version", (), {"type": "branch", "verbose_name": "v1.0.0"})()

    assert rule.match_version(version_tag) == True  # Type and name match
    assert rule.match_version(version_branch) == False  # Type doesn't match

    # Test 2: File pattern webhook filtering
    rule = AutomationRule(
        version_types=["any"],
        version_match_pattern=r".*",
        webhook_filter="file_pattern",
        webhook_match_pattern="docs/*,*.rst",
        action="trigger-build",
        enabled=True,
    )

    assert rule.match_webhook(changed_files=["docs/index.rst"]) == True
    assert rule.match_webhook(changed_files=["README.rst"]) == True
    assert rule.match_webhook(changed_files=["src/code.py"]) == False
    assert rule.match_webhook(changed_files=["docs/guide.md", "src/code.py"]) == True

    # Test 3: Commit message webhook filtering
    rule = AutomationRule(
        version_types=["any"],
        version_match_pattern=r".*",
        webhook_filter="commit_message",
        webhook_match_pattern=r"\[skip ci\]",
        action="trigger-build",
        enabled=True,
    )

    assert rule.match_webhook(commit_message="Update docs [skip ci]") == True
    assert rule.match_webhook(commit_message="Update docs") == False

    # Test 4: Label webhook filtering
    rule = AutomationRule(
        version_types=["external"],
        version_match_pattern=r".*",
        webhook_filter="label",
        webhook_match_pattern=r"^docs$",
        action="trigger-build",
        enabled=True,
    )

    assert rule.match_webhook(labels=["docs"]) == True
    assert rule.match_webhook(labels=["bug", "docs"]) == True
    assert rule.match_webhook(labels=["documentation"]) == False  # Doesn't match ^docs$
    assert rule.match_webhook(labels=["bug"]) == False

    # Test 5: Combined matching
    version = type("Version", (), {"type": "branch", "verbose_name": "main"})()

    rule = AutomationRule(
        version_types=["branch"],
        version_match_pattern=r"^main$",
        webhook_filter="file_pattern",
        webhook_match_pattern="docs/*",
        action="trigger-build",
        enabled=True,
    )

    # Both version and webhook must match
    assert rule.match(version, changed_files=["docs/index.rst"]) == True
    assert rule.match(version, changed_files=["src/code.py"]) == False

    version_dev = type("Version", (), {"type": "branch", "verbose_name": "develop"})()
    assert rule.match(version_dev, changed_files=["docs/index.rst"]) == False

    # Test 6: Disabled rule never matches
    rule.enabled = False
    assert rule.match(version, changed_files=["docs/index.rst"]) == False

    print("All tests passed! ✓")


if __name__ == "__main__":
    test_automation_rule()
