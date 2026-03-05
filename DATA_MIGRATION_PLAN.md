# Data Migration Plan: VersionAutomationRule → AutomationRule (V2)

This document outlines the plan for migrating from the old `VersionAutomationRule` models to the new `AutomationRule` (V2) models.

## Overview

The new automation rule system (`AutomationRule`) combines version matching with webhook filtering in a single, more flexible model. This replaces the polymorphic `VersionAutomationRule` / `RegexAutomationRule` / `WebhookAutomationRule` system.

## Key Differences

### Old System (VersionAutomationRule)
- Polymorphic base model with `RegexAutomationRule` and `WebhookAutomationRule` subclasses
- Single `version_type` field (one type per rule)
- `match_arg` field for version name pattern
- `RegexAutomationRule` only does version management actions
- `WebhookAutomationRule` only does file pattern matching for trigger build

### New System (AutomationRule)
- Single non-polymorphic model
- `version_types` JSONField (can match multiple types or "any")
- `version_match_pattern` for version name matching
- `webhook_filter` + `webhook_match_pattern` for webhook filtering
- Supports all combinations of version matching + webhook filtering + actions
- More flexible and easier to extend

## Migration Strategy

### Phase 1: Deploy New Models (Already Done)
- ✅ New `AutomationRule` model created
- ✅ New `AutomationRuleMatchV2` model created
- ✅ Migration `0071_add_automationrule_v2.py` created

### Phase 2: Data Migration (Next Step)

Create a migration that copies data from old models to new ones:

```python
# readthedocs/builds/migrations/0072_migrate_to_automationrule_v2.py

def migrate_regex_rules_forward(apps, schema_editor):
    """Migrate RegexAutomationRule to AutomationRule."""
    VersionAutomationRule = apps.get_model("builds", "VersionAutomationRule")
    AutomationRule = apps.get_model("builds", "AutomationRule")

    # Get all non-proxy rules (RegexAutomationRule)
    regex_rules = VersionAutomationRule.objects.filter(
        polymorphic_ctype__model='regexautomationrule'
    )

    for old_rule in regex_rules:
        AutomationRule.objects.create(
            project=old_rule.project,
            priority=old_rule.priority,
            description=old_rule.description or f"Migrated from rule #{old_rule.pk}",
            version_types=[old_rule.version_type],  # Single type becomes list
            version_match_pattern=old_rule.match_arg or ".*",
            webhook_filter=None,  # No webhook filtering for regex rules
            webhook_match_pattern=None,
            action=old_rule.action,
            action_arg=old_rule.action_arg,
            enabled=True,  # All migrated rules are enabled
        )


def migrate_webhook_rules_forward(apps, schema_editor):
    """Migrate WebhookAutomationRule to AutomationRule."""
    VersionAutomationRule = apps.get_model("builds", "VersionAutomationRule")
    AutomationRule = apps.get_model("builds", "AutomationRule")

    # Get all proxy rules (WebhookAutomationRule)
    webhook_rules = VersionAutomationRule.objects.filter(
        polymorphic_ctype__model='webhookautomationrule'
    )

    for old_rule in webhook_rules:
        AutomationRule.objects.create(
            project=old_rule.project,
            priority=old_rule.priority,
            description=old_rule.description or f"Migrated webhook rule #{old_rule.pk}",
            version_types=[old_rule.version_type],
            version_match_pattern=".*",  # Match all version names
            webhook_filter="file_pattern",  # Old webhook rules only did file patterns
            webhook_match_pattern=old_rule.match_arg,
            action=old_rule.action,  # Should be "trigger-build"
            action_arg=old_rule.action_arg,
            enabled=True,
        )
```

### Phase 3: Update Code to Use New Models

1. **Update webhook handlers** to use `AutomationRule` instead of checking both `RegexAutomationRule` and `WebhookAutomationRule`

2. **Update views/forms** to work with the new model structure

3. **Update API serializers** to expose the new fields

4. **Update admin interface** to manage the new models

### Phase 4: Deprecation Period

Keep both models active for a period to allow for rollback and testing:
- Mark old models as deprecated in code comments
- Add warnings to admin interface when editing old rules
- Prevent creation of new old-style rules (make forms read-only or redirect)

### Phase 5: Cleanup

After successful migration and verification:
1. Delete old `VersionAutomationRule`, `RegexAutomationRule`, `WebhookAutomationRule` models
2. Delete old `AutomationRuleMatch` model
3. Create migration to remove old database tables

## Migration Mapping Examples

### Example 1: RegexAutomationRule for Activating Release Tags

**Old:**
```python
RegexAutomationRule(
    project=project,
    priority=0,
    version_type="tag",
    match_arg="^release-.*",
    action="activate-version",
)
```

**New:**
```python
AutomationRule(
    project=project,
    priority=0,
    version_types=["tag"],
    version_match_pattern="^release-.*",
    webhook_filter=None,
    webhook_match_pattern=None,
    action="activate-version",
)
```

### Example 2: WebhookAutomationRule for File Pattern Builds

**Old:**
```python
WebhookAutomationRule(
    project=project,
    priority=1,
    version_type="branch",
    match_arg="docs/*.rst",
    action="trigger-build",
)
```

**New:**
```python
AutomationRule(
    project=project,
    priority=1,
    version_types=["branch"],
    version_match_pattern=".*",  # Match any version name
    webhook_filter="file_pattern",
    webhook_match_pattern="docs/*.rst",
    action="trigger-build",
)
```

### Example 3: New Functionality - Match Multiple Version Types

**Only possible with new model:**
```python
AutomationRule(
    project=project,
    priority=0,
    version_types=["tag", "branch"],  # Multiple types!
    version_match_pattern="^v\\d+\\.\\d+\\.\\d+$",
    webhook_filter=None,
    action="activate-version",
)
```

### Example 4: New Functionality - Commit Message Filter

**Only possible with new model:**
```python
AutomationRule(
    project=project,
    priority=2,
    version_types=["any"],  # All version types
    version_match_pattern=".*",
    webhook_filter="commit_message",
    webhook_match_pattern="\\[skip ci\\]|\\[ci skip\\]",
    action="trigger-build",  # In practice, would skip build if matched
)
```

### Example 5: New Functionality - PR Label Filter

**Only possible with new model:**
```python
AutomationRule(
    project=project,
    priority=3,
    version_types=["external"],
    version_match_pattern=".*",
    webhook_filter="label",
    webhook_match_pattern="^(documentation|docs)$",
    action="trigger-build",
)
```

## Testing the Migration

Before deploying to production:

1. **Export existing rules:**
   ```python
   python manage.py dumpdata builds.VersionAutomationRule > old_rules.json
   ```

2. **Run migration in staging:**
   ```bash
   python manage.py migrate builds 0072_migrate_to_automationrule_v2
   ```

3. **Verify data:**
   ```python
   # Check counts match
   old_count = VersionAutomationRule.objects.count()
   new_count = AutomationRule.objects.count()
   assert old_count == new_count

   # Spot check a few rules
   for project in Project.objects.all()[:10]:
       old_rules = project.automation_rules.all()
       new_rules = project.automation_rules_v2.all()
       # Verify they match
   ```

4. **Test webhook handlers** with both old and new rules active

5. **Monitor for errors** in logs

## Rollback Plan

If issues are discovered:

1. **Disable new rules:**
   ```python
   AutomationRule.objects.update(enabled=False)
   ```

2. **Keep old rules active** (don't delete them yet)

3. **Fix issues** and re-run migration

4. **Re-enable new rules:**
   ```python
   AutomationRule.objects.update(enabled=True)
   ```

## Notes for Future Enhancement

The new `AutomationRule` model is designed to be extensible:

- **Multiple matchers**: Could add more webhook filter types (e.g., "author", "base_branch")
- **Composition**: Could support AND/OR logic between multiple conditions
- **Action chains**: Could support multiple actions per rule
- **Scheduling**: Could add time-based conditions (e.g., only apply rule during business hours)

These enhancements can be added without major model changes.

## Timeline

- **Week 1**: Deploy new models to production (migration 0071)
- **Week 2**: Run data migration (migration 0072), monitor
- **Week 3**: Update code to use new models
- **Week 4-6**: Deprecation period, both models active
- **Week 7**: Remove old models, cleanup

## Questions / Decisions Needed

1. **Priority handling**: Should we renumber priorities when migrating, or keep original values?
   - **Recommendation**: Keep original values to maintain order

2. **Predefined match args**: How to migrate rules with `predefined_match_arg`?
   - **Recommendation**: Resolve to actual pattern value during migration

3. **Failed migrations**: What to do if a rule can't be migrated cleanly?
   - **Recommendation**: Log warning, create disabled rule, notify project owner

4. **Duplicate priorities**: If multiple rules have same priority after migration?
   - **Recommendation**: Add unique suffix to priority during migration

## Contact

For questions about this migration, contact the infrastructure team.
