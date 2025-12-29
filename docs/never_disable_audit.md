# Organization `never_disable` Field Audit

## Overview

This document analyzes the `never_disable` field on the `Organization` model to ensure it is properly respected everywhere that organizations can be disabled.

The `never_disable` field is a boolean flag (introduced in migration `0012_add_organization_never_disable`) that prevents an organization from being disabled, even if its subscription ends. This is useful for special cases like internal organizations, sponsored organizations, or testing purposes.

## Field Definition

**Location:** `readthedocs/organizations/models.py:116-122`

```python
never_disable = models.BooleanField(
    _("Never disable"),
    help_text="Never disable this organization, even if its subscription ends",
    # TODO: remove after migration
    null=True,
    default=False,
)
```

## Places Where Organizations Are Disabled

### 1. ✅ Subscription Event Handler - `subscription_updated_event`

**Location:** `readthedocs/subscriptions/event_handlers.py:103-174`

**Status:** ✅ **PROPERLY RESPECTS `never_disable`**

This webhook handler responds to Stripe subscription updates/deletions. When a subscription becomes inactive:

```python
if stripe_subscription.status not in (SubscriptionStatus.active, SubscriptionStatus.trialing):
    if organization.never_disable:
        log.info(
            "Organization can't be disabled, skipping deactivation.",
            organization_slug=organization.slug,
        )
    else:
        log.info(
            "Organization disabled due its subscription is not active anymore.",
            organization_slug=organization.slug,
        )
        organization.disabled = True
```

**Test Coverage:** 
- `test_subscription_canceled_on_never_disable_organization` (line 360)

### 2. ✅ Subscription Canceled Notification Handler - `subscription_canceled`

**Location:** `readthedocs/subscriptions/event_handlers.py:176-232`

**Status:** ✅ **PROPERLY RESPECTS `never_disable`**

This handler sends notifications when a subscription is canceled. It skips notification for `never_disable` organizations:

```python
if organization.never_disable:
    log.info(
        "Organization can't be disabled, skipping notification.",
        organization_slug=organization.slug,
    )
    return
```

The notification is correctly skipped, which is important because it prevents sending "your organization will be disabled" emails to organizations that won't actually be disabled.

**Test Coverage:**
- `test_subscription_canceled_on_never_disable_organization` (line 360)

### 3. ✅ Organization Queryset - `disable_soon`

**Location:** `readthedocs/organizations/querysets.py:109-126`

**Status:** ✅ **PROPERLY RESPECTS `never_disable`**

This queryset method filters organizations that will be disabled due to expired subscriptions. It explicitly excludes `never_disable` organizations:

```python
def disable_soon(self, days, exact=False):
    """
    Filter organizations that will eventually be marked as disabled.

    These are organizations which their subscription has ended,
    excluding organizations that can't be disabled, or are already disabled.
    """
    return (
        self.subscription_ended(days=days, exact=exact)
        # Exclude organizations that can't be disabled.
        .exclude(never_disable=True)
        # Exclude organizations that are already disabled
        .exclude(disabled=True)
    )
```

This method is used by:
- `OrganizationDisabledNotification.for_organizations()` in notifications
- `weekly_subscription_stats_email` task for reporting

**Test Coverage:**
- `test_organizations_to_be_disabled` (line 79-221)

## Other Places That Check Organization Disabled Status

### 4. ✅ Project Queryset - Should Not Serve Docs

**Location:** `readthedocs/projects/querysets.py:97-106`

**Status:** ✅ **CORRECTLY USES `disabled` STATUS**

This method checks if docs should be served for a project. It correctly checks the `organization.disabled` field (which should never be True for `never_disable` organizations):

```python
if (
    project.skip
    or project.n_consecutive_failed_builds
    or any_owner_banned
    or (organization and organization.disabled)
    or spam_project
):
    return False
```

This is working correctly because `never_disable` prevents the `disabled` flag from being set to True in the first place.

### 5. ✅ Notification Signal - Organization Disabled

**Location:** `readthedocs/notifications/signals.py:48-61`

**Status:** ✅ **CORRECTLY USES `disabled` STATUS**

This signal adds/removes notifications when an organization's `disabled` status changes:

```python
@receiver(post_save, sender=Organization)
def organization_disabled(instance, *args, **kwargs):
    """Check if the organization is ``disabled`` and add/cancel the notification."""
    if instance.disabled:
        Notification.objects.add(
            message_id=MESSAGE_ORGANIZATION_DISABLED,
            attached_to=instance,
            dismissable=False,
        )
    else:
        Notification.objects.cancel(
            message_id=MESSAGE_ORGANIZATION_DISABLED,
            attached_to=instance,
        )
```

This works correctly because organizations with `never_disable=True` should never have `disabled=True`.

### 6. ✅ Daily Email Task - Organization Disabled Notification

**Location:** `readthedocs/subscriptions/tasks.py` (imported as `readthedocs/organizations/tasks.py:24-40`)

**Status:** ✅ **CORRECTLY USES `disable_soon` QUERYSET**

The daily email task uses the `disable_soon` queryset method which already filters out `never_disable` organizations:

```python
@app.task(queue="web")
def daily_email():
    """Daily email beat task for organization notifications."""
    organizations = OrganizationDisabledNotification.for_organizations().distinct()
    for organization in organizations:
        for owner in organization.owners.all():
            notification = OrganizationDisabledNotification(
                context_object=organization,
                user=owner,
            )
            notification.send()
```

### 7. ✅ Organization Queryset - Clean Artifacts

**Location:** `readthedocs/organizations/querysets.py:128-139`

**Status:** ✅ **IMPLICITLY RESPECTS `never_disable`**

The `clean_artifacts` method filters organizations for artifact cleanup. It only targets organizations that are already `disabled=True`:

```python
def clean_artifacts(self):
    """
    Filter organizations which their artifacts can be cleaned up.

    These organizations are at least 3*DISABLE_AFTER_DAYS (~3 months) that
    are disabled and their artifacts weren't cleaned already.
    """
    return self.subscription_ended(days=3 * DISABLE_AFTER_DAYS, exact=False).filter(
        disabled=True,
        artifacts_cleaned=False,
    )
```

Since `never_disable` organizations should never have `disabled=True`, they won't be included in artifact cleanup.

## Summary of Findings

### ✅ All Critical Paths Are Protected

The `never_disable` field is properly respected in all places where organizations are actively disabled:

1. **Subscription event handlers** - Both `subscription_updated_event` and `subscription_canceled` explicitly check `never_disable`
2. **Queryset methods** - The `disable_soon` method explicitly excludes `never_disable` organizations
3. **Downstream consumers** - All code that disables organizations or sends related notifications uses the above protected paths

### Architecture Pattern

The codebase follows a good architectural pattern:

- **Single point of control**: Organizations are only actively disabled in one place (the subscription event handler)
- **Defensive filtering**: The `disable_soon` queryset method provides a second layer of protection
- **Correct propagation**: All downstream code that checks `disabled` status works correctly because `never_disable` prevents the flag from being set in the first place

## Recommendations

### 1. ✅ No Changes Needed for Core Functionality

The current implementation is sound. The `never_disable` field is properly checked at all critical points where organizations would be disabled.

### 2. Consider Adding Database Constraint (Optional)

To provide an additional layer of safety, consider adding a database-level check constraint:

```python
class Meta:
    constraints = [
        models.CheckConstraint(
            check=~models.Q(never_disable=True, disabled=True),
            name='never_disable_cant_be_disabled',
        ),
    ]
```

This would prevent the database from ever having `never_disable=True` and `disabled=True` at the same time, even if there's a bug in the application code.

### 3. ✅ Test Coverage is Good

The existing tests verify the critical paths:
- `test_subscription_canceled_on_never_disable_organization` tests subscription event handling
- `test_organizations_to_be_disabled` tests the queryset filtering

### 4. Documentation is Clear

The field has a clear help text that explains its purpose. The code comments in various places reference the behavior appropriately.

## Changelog Reference

From `CHANGELOG.rst`:
```
* `@stsewd <https://github.com/stsewd>`__: Subscriptions: improve subscription detection and respect never_disable (`#12046 <https://github.com/readthedocs/readthedocs.org/pull/12046>`__)
```

This indicates that the feature was specifically designed and implemented in PR #12046 to respect the `never_disable` flag.

## Conclusion

**The `never_disable` field is properly respected everywhere that organizations are disabled.**

The implementation is robust with:
- Explicit checks in the primary disable path (subscription event handlers)
- Filtering in queryset methods used for notifications and reporting
- Implicit safety through the disabled flag never being set for `never_disable` organizations
- Good test coverage of the critical paths
- Clear documentation and logging

No code changes are required. The system is working as designed.
