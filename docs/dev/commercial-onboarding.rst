Commercial onboarding funnel
============================

How we measure trial onboarding on Read the Docs Business,
what the August 2026 investigation found,
and the ranked fix list that came out of it.
Retention on Business is exceptional (customers from 2014 still paying),
so nearly all revenue growth is gated on this funnel.

Measuring the funnel
--------------------

The scoreboard lives in Metabase (RTD Commercial = database 4),
collection **Business Overview**:

* **Activation funnel by org cohort** (question 1727) — created → imported → built → activated in 7 days.
  This is the headline number.
* **Activation rate by cohort** (question 1791) — activation only, full history,
  7d/30d/ever horizons. A step down in one cohort means something shipped that month broke onboarding.
* **Onboarding funnel by step** (question 1923) — decomposes created → imported into
  created → VCS account connected → imported → built OK → activated,
  with a ``likely_spam`` segment. Read the percentage columns left to right
  and fix the biggest drop.

Step definitions (all joins go through ``organizations_organizationowner``
because ``auth_user`` is not synced to Metabase):

* *Created*: ``organizations_organization.pub_date``.
* *VCS connected*: an owner has a ``socialaccount_socialaccount`` row with provider
  ``github``, ``githubapp``, ``gitlab``, or ``bitbucket_oauth2``.
  Google and Okta rows are identity-only and don't count.
* *Imported*: any project through ``organizations_organization_projects``.
  Importing always triggers a build, so there is no separate "attempted a build" step —
  the gap between imported and built OK is **first-build failure**, not users who never tried.
* *Built OK*: ``builds_build`` with ``success AND state = 'finished'``
  (``success`` defaults to true, so the state predicate is required).

Known measurement gaps
~~~~~~~~~~~~~~~~~~~~~~

* The Metabase role has no ``SELECT`` on the ``oauth_*`` tables
  (``oauth_remoterepository_2020``, ``oauth_remoterepositoryrelation``,
  ``oauth_githubappinstallation``, ``oauth_remoteorganization_2020``,
  ``oauth_remoteorganizationrelation``, and also ``account_emailaddress``).
  Until ops grants read access, the two steps that would separate
  "connected but the App was never installed" from "repos synced but none imported" —
  *repos listed* and *GitHub App installed* — cannot be measured.
  This grant is the single highest-value instrumentation change available.
* Since 2026-07-08 an SEO-spam campaign mass-registers trial orgs
  (~10× organic volume, almost all freemail, ``outlook.com`` monoculture).
  Question 1923 flags freemail org emails from July 2026 on as ``likely_spam``.
  The flag sweeps in some legitimate freemail signups,
  so the non-spam segment is the floor of the real cohort, not the exact truth.
  June 2026 is the last clean cohort.
  The spam bots connect the legacy GitHub OAuth provider and complete the funnel
  at ~86% — any unsegmented 2026-07+ read is meaningless.

What the August 2026 investigation found
----------------------------------------

Where the funnel actually loses people (clean cohorts, June 2025 – June 2026):

#. **Created → VCS connected loses ~55%.** Only 40–50% of org creators ever connect
   a VCS account; the rest mostly signed up with Google or email and stalled.
   This ratio has been flat for at least 18 months — it is the biggest loss,
   but not the 2026 regression. Real buyers are in this bucket
   (June examples include ``cisco.com`` and ``gatik.ai`` signups that never connected).
#. **Connected → imported collapsed in 2026.** 70–95% through late 2025,
   47% in June 2026 — the worst on record. This is the regression.
#. **Imported → first successful build loses ~30%.** Of clean orgs that built anything
   in their first week, 31% saw *every* build fail — they tried the product and got nothing.
#. **PR previews are absent from onboarding.** 55–60% of steady-state Business builds are
   pull request previews, but only 8 of 218 clean new orgs (3.7%) got a PR preview build
   in their first week. The value moment that retains teams is not part of starting.

Why connected → imported broke
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The GitHub App requires an installation on the user's GitHub account or company org —
a separate step on github.com after OAuth — and nothing in the product drives a new
user to it:

* An uninstalled App produces a **silently empty repo list**: ``GitHubAppService.for_user``
  finds no installations and only logs at info level; there is no "App not installed"
  or "pending org-admin approval" state anywhere in the data model or UI
  (the only code that reasons about installation presence is the migration flow in
  ``readthedocs/oauth/migrate.py``, surfaced only at ``/accounts/migrate-to-github-app/``).
* The import page renders **nothing until the user types a search**
  (the picker is a search dropdown with no default listing), and the App-install /
  org-approval guidance sits behind a "Repair" popup that only fires after a search
  returns zero results (ext-theme #648, October 2025 — previously the install link
  was always visible on the import page).
* The **org-approval guidance is gated on the wrong provider**: in
  ``project_create_automatic.html`` it renders only for legacy ``github`` accounts,
  explicitly not for ``githubapp`` — the users who actually need it.
* ``RelatedUserQuerySet.api`` (``readthedocs/oauth/querysets.py``) hides **all** legacy
  GitHub repos once a user has a ``githubapp`` account and at least one App-synced repo,
  so partially-migrated users lose repos from the list with no explanation.
* Timeline matches the data: the App became unconditional for all signups on
  2026-02-05 (#12753), the "we're syncing your repos" notification was suppressed for
  exactly the new-user cohort in mid-February (#12774, #12792), and the only proactive
  dashboard mention of the App was deleted on 2026-06-01 (ext-theme #751) —
  the month the funnel bottomed.
  Provider data agrees: only ~750 ``githubapp`` connections exist in total,
  and orgs whose owner connected the App import at 69% vs 58% for legacy-only —
  installing the App works; discovering it is what fails.
* Sentry corroborates the company-org friction (the buyers, who solo Community users
  never hit): GitHub orgs with IP allow lists reject the App's calls
  (``tensr-labs``, ``AMD-ROCm-Internal``), plus installation-level rate limits —
  all invisible to the user.

Two more June 2026 suspects need a first-build-failure taxonomy to confirm
(blocked on ``telemetry_builddata`` not being synced):
the 2026-06-16 release rewrote the import → webhook path
(GHSA-843j-p445-9532: ``attach_webhook`` now uses ``for_user`` instead of
``for_project``, is skipped when there's no remote repository, and Business
SSH-key attachment moved to a corporate subclass hook),
and django-allauth jumped five minor versions on 2026-05-25 (#13059).

Ranked fixes
------------

By measured loss, largest first:

#. **Detect and explain the empty repo list** (targets the regression).
   On the import page, when the user's remote repository list is empty,
   say why and link the fix inline — GitHub App not installed → install link;
   installed but restricted → update-installation link; org approval pending →
   request-approval guidance; sync still running → progress state.
   Backend: expose installation state (``oauth_githubappinstallation`` exists but has
   no pending/suspended state — the migration-flow logic in ``oauth/migrate.py``
   already computes most of this and should be generalized).
   Front end: show the guidance on first load instead of behind the post-search
   "Repair" popup, and ungate the org-approval copy from the legacy provider check.
#. **Make the App install part of the flow, not a footnote** (targets the same loss).
   After a ``githubapp`` connection with zero installations, drive straight to
   ``https://github.com/apps/<app>/installations/new/`` instead of landing the user
   on a page whose empty state assumes repos exist.
#. **A guaranteed first success** (targets created → connected and first-build failure).
   A one-click sample project (the template exists as dead code:
   ``onboard_import.html`` links ``projects_import_demo``; ext-theme's copy is
   unreferenced) gives every org a successful build and a PR preview to look at
   before wiring up their own repo — and gives email/Google signups a reason to
   come back and connect.
#. **PR-preview-first onboarding** (targets the value moment).
   After first successful build, the next prompt should be "open a pull request and
   watch the preview build", not more configuration. Measured by first-week PR preview
   share in question 1923's successor.
#. **Resume loops for the stalled majority**: the dashboard empty state currently has
   no call to action (ext-theme ``project_list.html`` placeholder has no Add button),
   and there is no abandoned-onboarding email. The only lifecycle email is
   "your trial is ending". An email nudge at +24h for orgs with no VCS connection or
   no import — linking the exact next step, not the dashboard — is cheap and addresses
   the largest absolute loss.
#. **First-build failure taxonomy**: 31% of orgs that build in week one never see a
   success. Getting ``telemetry_builddata`` (or a failure-reason rollup) into Metabase
   turns "imported → built OK" from a number into a work queue.

Success criteria (from the June 2026 baseline of 19% and 8.5%):
created → imported above 50% and 7-day activation above 25% on clean cohorts,
read monthly from question 1727.

Corporate handoff
-----------------

Pieces of this that live in the private corporate repo and can't be changed here:

* The trial/org signup flow itself (``OrganizationSignupForm`` and
  ``PROJECT_IMPORT_VIEW`` are ``SettingsOverrideObject`` extension points overridden
  there). The org-create page currently asks for name/slug/email before the user has
  connected anything or seen any value; June's data includes an org literally named
  ``join-or-create-an-organization`` (the page heading pasted into the name field)
  and two users who created duplicate orgs. Sequencing (connect → see repos → import →
  *then* name your org) is a corporate-side change.
* The Business override of ``_get_post_import_tasks`` attaches the SSH deploy key;
  after GHSA-843j-p445-9532 moved this from a signal to a subclass hook,
  verify the override is in place and imports get a working deploy key —
  a likely contributor to June's first-build failures.
* SSO/SAML-specific import blockers (``ProjectFormPrevalidateMixin``) render as
  hard stops; corporate owns the messaging around them.
