# Implementation Summary: Push Automation Rules for GitHub App Webhooks

## Overview

I have successfully implemented automation rules for the `GitHubAppWebhookHandler` to filter builds based on files changed in push webhook events. This feature allows users to define rules that decide whether a build should be triggered based on which files were modified, added, or deleted in a push.

## Changes Made

### 1. **New Model: `PushAutomationRule`** (`readthedocs/builds/models.py`)

A new polymorphic model class that extends `VersionAutomationRule`:

**Key Features:**
- Inherits from `VersionAutomationRule` as a proxy model
- Implements file pattern matching using regex (with timeout protection)
- Main method: `match_files(file_list)` - checks if any file matches the configured pattern
- Supports all standard automation rule actions (activate, hide, make public/private, set as default, delete)
- Uses the same predefined and custom match argument system as `RegexAutomationRule`

**Implementation Details:**
```python
class PushAutomationRule(VersionAutomationRule):
    def match_files(self, file_list):
        """Check if any file in the list matches the rule pattern."""
        # Uses regex.search() with timeout protection
        # Returns True if at least one file matches
```

### 2. **Enhanced `GitHubAppWebhookHandler`** (`readthedocs/oauth/tasks.py`)

Added three new methods and updated existing logic:

#### **`_should_build_push(project, modified_files)`**
- Evaluates all push automation rules for a project
- Checks if any rule matches the modified files
- **Backward Compatible**: Returns `True` if no push rules exist (preserves existing behavior)
- **Efficient**: Uses iterator to minimize database queries
- Logs rule matches and blocks

#### **`_get_modified_files_from_push()`**
- Extracts all modified files from push webhook payload
- Combines files from commits' `added`, `modified`, and `removed` arrays
- Returns deduplicated list of file paths

#### **Updated `_handle_push_event()`**
- Now extracts modified files from webhook payload
- Checks automation rules before triggering builds
- Only calls `build_versions_from_names()` if rules allow it
- Logs when rules block a build
- Preserves existing behavior for create/delete events (branch/tag creation/deletion)

### 3. **Import Addition**
Added `from readthedocs.builds.models import PushAutomationRule` to tasks.py for accessing the new rule class.

## How It Works

### User Workflow

1. **Create a Rule**: User creates a `PushAutomationRule` in the project settings with:
   - Pattern: e.g., `^docs/` (to match files in docs folder)
   - Action: e.g., `ACTIVATE_VERSION_ACTION`
   - Version type: `BRANCH` or `TAG`

2. **Push Event Occurs**: Developer pushes changes to the repository

3. **Webhook Processing**:
   - GitHub sends push webhook
   - `_handle_push_event()` is called
   - Modified files are extracted from the payload
   - Automation rules are checked
   - Build is triggered only if rules match

### Example Scenarios

**Scenario 1: Only build when docs change**
```
Rule: Pattern = "^docs/", Action = "ACTIVATE_VERSION_ACTION"
Push: Modified files = ["src/main.py", "docs/guide.md"]
Result: Build is triggered (docs/guide.md matches ^docs/)
```

**Scenario 2: Only build when code changes (not tests)**
```
Rule: Pattern = "^(?!tests/).*\.py$", Action = "ACTIVATE_VERSION_ACTION"
Push: Modified files = ["tests/test_main.py"]
Result: Build is NOT triggered (file matches tests/ exclusion)
```

## Technical Details

### Regex Matching
- Uses Python's `regex` module (not standard `re`)
- Applies timeout protection (1 second default) to prevent ReDoS attacks
- Uses `regex.VERSION0` flag for compatibility
- Catches and logs timeout/exception errors gracefully

### Database Query Optimization
- Uses `filter(polymorphic_ctype__model="pushautomationrule")` to target only push rules
- Uses `.iterator()` to avoid loading all rules into memory
- Early exit when first matching rule is found

### Backward Compatibility
- **Critical**: If no push rules exist, builds proceed as before
- Existing webhook behavior is completely preserved
- Feature is opt-in (only applies when rules are explicitly created)
- No changes to existing automation rule system

## Files Modified

1. **`readthedocs/builds/models.py`**
   - Added `PushAutomationRule` class (69 lines)
   - Positioned after `RegexAutomationRule`
   - Uses existing infrastructure (`match_arg`, `get_match_arg()`, etc.)

2. **`readthedocs/oauth/tasks.py`**
   - Added import: `from readthedocs.builds.models import PushAutomationRule`
   - Added `_should_build_push()` method (36 lines)
   - Added `_get_modified_files_from_push()` method (18 lines)
   - Updated `_handle_push_event()` method (14 lines modified)

## Future Enhancements

Potential improvements for future iterations:
1. Add UI/forms for creating and editing `PushAutomationRule` instances
2. Add tests in `test_automation_rules.py` and `test_sync_versions.py`
3. Create admin interface for managing push rules
4. Add more granular file matching options (e.g., AND/OR logic for multiple patterns)
5. Support for exclude patterns using negative lookahead
6. Add metrics/logging for rule effectiveness

## Testing Recommendations

1. **Unit Tests**: Test `match_files()` with various file patterns
2. **Integration Tests**: Test `_handle_push_event()` with mock webhook payloads
3. **E2E Tests**: Test with actual GitHub App webhooks
4. **Backward Compatibility**: Verify existing projects without push rules work unchanged
