Migrate GitHub pull request status reporting to the Checks API
===============================================================

Background
----------

Today we report pull request build status to GitHub through the
`Commit Statuses REST API`_ (``/repos/{owner}/{repo}/statuses/{sha}``),
from both ``GitHubService`` (OAuth tokens) and ``GitHubAppService``
(GitHub App installations). That API exposes only four states:
``pending``, ``success``, ``failure``, ``error``.

This model forces several workarounds and leaves gaps called out in
:rtd-issue:`12022`:

* Builds skipped via exit code ``183`` are reported as ``success`` with
  a custom description, because the API has no ``skipped`` state.
* User-cancelled builds are indistinguishable from failures.
* Restarted builds keep showing ``failure`` until they finish, because
  there is no way to move a terminal status back to ``pending`` (the API
  has no ``in_progress`` concept).
* Rich build output (summaries, annotations) cannot be attached.

GitHub's newer `Checks API`_
(``/repos/{owner}/{repo}/check-runs``) supports all of these. It is
authenticated as a GitHub App, which we already have installed via
``GitHubAppService``.

.. contents::
   :local:
   :depth: 2

Scope
-----

In scope:

* Replace commit-status reporting with check-run reporting for projects
  connected through a GitHub App installation.
* Use ``status=in_progress`` for running builds and use the richer
  ``conclusion`` values (``success``, ``failure``, ``skipped``,
  ``cancelled``, ``neutral``) for completed builds.
* Store enough state on the ``Build`` model to update the same check run
  across its lifecycle (trigger → running → completed).

Out of scope:

* OAuth-only GitHub projects. These keep the Commit Statuses path.
* GitLab. GitLab has a different pipeline status model and is untouched.
* Rich ``output`` (annotations, summaries). Follow-up work.
* Re-running a check run from the GitHub UI. Follow-up work.

Status mapping
--------------

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - Internal state
     - Checks API ``status``
     - Checks API ``conclusion``
   * - Build triggered
     - ``queued``
     - —
   * - Build running
     - ``in_progress``
     - —
   * - Build succeeded
     - ``completed``
     - ``success``
   * - Build failed
     - ``completed``
     - ``failure``
   * - Build skipped (exit code 183)
     - ``completed``
     - ``skipped``
   * - Build cancelled by user
     - ``completed``
     - ``cancelled``

Implementation outline
----------------------

**Build model.** Add a nullable ``github_check_run_id`` field so that
subsequent lifecycle updates can target the same check run.

**Provider service.** Extend ``GitHubAppService`` with
``create_check_run`` and ``update_check_run`` methods that wrap the
existing PyGithub ``installation_client``. Keep the existing
``send_build_status`` method in place as a fallback.

**Dispatcher.** In ``send_external_build_status``, route a build to the
Checks API when both of the following are true:

* the project has the ``Feature.USE_GITHUB_CHECKS_API`` flag enabled, and
* the resolved Git service for the project is ``GitHubAppService``.

Otherwise fall through to the existing commit-status path.

**Lifecycle hooks.** Wire the check-run lifecycle to existing points:

* Trigger: ``prepare_build`` in ``core/utils/__init__.py`` creates the
  check run and stores its ID on the ``Build``.
* Running: a new hook around the ``BUILD_STATE_BUILDING`` transition
  sends ``status=in_progress``.
* Completion: ``on_success`` and ``on_failure`` in
  ``projects/tasks/builds.py`` send ``status=completed`` with the
  appropriate conclusion (including ``skipped`` for exit code 183 and
  ``cancelled`` for user-cancelled builds).

**Check run name.** Keep the existing context convention
(``{RTD_BUILD_STATUS_API_NAME}:{project.slug}``) as the check run
``name``. This preserves branch-protection rules that reference the
current name, and continues to disambiguate multiple Read the Docs
projects that live on the same repository (subprojects, translations).

**Fallback.** If ``create_check_run`` fails, log and fall back to the
commit-status path so a pull request is never left without any status.

Rollout
-------

The feature ships behind ``Feature.USE_GITHUB_CHECKS_API``, disabled by
default. We enable it first for internal dogfood projects, monitor
``X-RateLimit-*`` headers (there is no rate-limit instrumentation
today), and then flip it on for all GitHub App installations. The old
commit-status path stays in place for OAuth-only projects indefinitely.

Risks
-----

* **Branch protection.** Repositories that have pinned the current
  status name as a required check will break if we change the ``name``.
  Mitigated by keeping the name identical.
* **Re-runs from GitHub UI.** The Checks API exposes a "Re-run" button
  that we do not currently handle. Out of scope for v1.
* **Multiple parallel builds on the same commit.** Check runs are
  unique by ``(name, head_sha, app_id)``. We overwrite the existing run
  for the same project and commit rather than creating a new one, which
  matches today's commit-status behaviour.

Related
-------

* :rtd-issue:`12022` — original feature request.
* :rtd-issue:`12959` — introduces ``BUILD_STATUS_SKIPPED`` as the
  incremental commit-status workaround that this migration replaces.

.. _Commit Statuses REST API: https://docs.github.com/en/rest/commits/statuses
.. _Checks API: https://docs.github.com/en/rest/checks/runs
