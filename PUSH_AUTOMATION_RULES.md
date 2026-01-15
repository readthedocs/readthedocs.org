# Push Automation Rules

## Overview

Push automation rules enable filtering builds based on files changed in push webhook events. This allows users to configure rules that automatically trigger or prevent builds depending on which files were modified, added, or removed in a push.

## How It Works

### 1. PushAutomationRule Model

A new `PushAutomationRule` model has been added as a polymorphic child of `VersionAutomationRule`. This model:

- **Inherits from**: `VersionAutomationRule`
- **Purpose**: Provides file-based filtering for push events
- **Key Method**: `match_files(file_list)` - Checks if any file in the list matches the configured pattern

### 2. File Matching

The `PushAutomationRule.match_files()` method:

- Takes a list of file paths that were changed in a push
- Uses regex matching (with timeout protection) to check if any file matches the rule's pattern
- Returns `True` if at least one file matches, `False` otherwise

### 3. GitHubAppWebhookHandler Integration

The `GitHubAppWebhookHandler` has been enhanced with:

#### `_get_modified_files_from_push()`
- Extracts all modified files from the push event payload
- Combines files from all commits' `added`, `modified`, and `removed` arrays
- Returns a deduplicated list of file paths

#### `_should_build_push(project, modified_files)`
- Checks if automation rules exist for the project
- Evaluates all push rules against the modified files
- Returns `True` if:
  - No push rules are configured (backward compatible), OR
  - At least one rule matches the modified files
- Returns `False` if rules exist but none match

#### Updated `_handle_push_event()`
- Extracts modified files from the webhook payload
- Checks automation rules before triggering builds
- Only calls `build_versions_from_names()` if rules allow it
- Logs when rules block a build

## Usage Example

A project can create a `PushAutomationRule` with:

- **match_arg**: `^docs/` (regex pattern to match files in docs folder)
- **action**: `ACTIVATE_VERSION_ACTION` (or other available actions)
- **version_type**: `BRANCH` or `TAG`

When a push occurs:
1. The webhook handler extracts all modified files
2. Checks if any file matches `^docs/` pattern
3. Only triggers a build if a file in the docs folder was changed

## Backward Compatibility

- If no push automation rules are configured for a project, the build is triggered as before
- Existing webhook behavior is preserved
- The feature is opt-in (only applies if rules are explicitly created)

## File Matching Features

- Uses `regex` module with timeout protection (1 second default) to prevent ReDoS attacks
- Supports standard regex patterns (same as other automation rules)
- Matches against the complete file path from the repository root
- Deduplicated file lists to avoid redundant checks
