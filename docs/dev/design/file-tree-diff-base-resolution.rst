File tree diff base resolution
==============================

This document explains how the file tree diff (FTD) for pull request builds
decides *which* base state to compare against, why the current approach exists,
and where someone picking this up next should look.

It assumes you've read :doc:`file-tree-diff`, which covers the manifest format
and the diff API. This document is only about the base version resolution
problem for external (pull request) versions.

Context
-------

For a pull request preview, the diff compares the PR's files against a "base"
version (the project's ``latest`` by default). The naive approach — always
compare against whatever the base version currently contains — breaks in two
opposite ways:

**Stale base.**
A PR opens against base@A and builds. The base branch then moves forward to
base@B with unrelated new files. Comparing the PR (still at base@A) against
the live base@B makes base@B's new files look like they were *deleted* by the
PR. Wrong.

**Merged base.**
A PR opens against base@A. The base branch moves to base@B. The user merges
base@B into the PR branch and pushes. The PR now contains ``base@B + the PR's
own changes``. If we're still comparing against a pinned snapshot of base@A,
base@B's content looks like it was *added* by the PR. Also wrong.

Neither "always pin" nor "always refresh" is correct. The semantically correct
base is the commit the PR has actually been brought up to — in git's own sense,
the merge-base.

The snapshot
------------

To fix the stale-base problem, the first successful PR build takes a snapshot of
the base version's manifest and pins it:

.. code-block::

   diff/{project}/{external_version}/base_manifest_snapshot.json

Subsequent PR builds diff against this snapshot instead of the live base
manifest. This is written from ``FileManifestIndexer.collect`` in
``readthedocs/projects/tasks/search.py``, and read back in ``get_diff`` in
``readthedocs/filetreediff/__init__.py``.

The snapshot was originally **write-once**: once the file existed, it was never
rewritten. That fixed stale-base but *created* the merged-base problem, because
a PR that merged in newer base kept being compared against the old pinned state.

Smart refresh
-------------

The snapshot is now refreshed on each PR build, but only when the PR has
actually pulled the base branch into its own history. The check lives in
``should_refresh_snapshot`` (``readthedocs/filetreediff/__init__.py``) and runs
a single git command against the build's live clone:

.. code-block:: bash

   git merge-base --is-ancestor <base_commit> HEAD

- Exit ``0`` — the base commit is reachable from ``HEAD``, i.e. the user merged
  the base branch in. Refresh the snapshot from the base version's current
  manifest.
- Any other exit — not an ancestor, or the commit isn't in the clone. Leave the
  snapshot pinned (stale-base fix preserved).

Why no extra fetch is needed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs does a shallow clone and only fetches the PR ref
(``pull/{id}/head``); the base branch is never fetched separately. It might seem
like we'd need to fetch the base branch to reason about it — we don't.

``<base_commit>`` is present in the PR's clone *only if* it's reachable from
``HEAD``, which is exactly the condition we're testing. If the user merged the
base branch in, the merge commit has the base tip as a parent, so that history
is already in the clone. If they didn't, the base commit is on a divergent
branch that was never fetched, and ``--is-ancestor`` returns non-zero. Either
way the local clone already contains everything needed to answer the question.

``--is-ancestor`` is a pure history walk: no network, no working-tree change.

Where ``base_commit`` comes from
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Two sources, in priority order:

1. ``Version.base_identifier`` — the base commit the PR targets, captured from
   the webhook payload (``pull_request.base.sha`` on GitHub) in
   ``get_or_create_external_version``
   (``readthedocs/core/views/hooks.py``). This is the precise answer: the base
   the PR actually points at. (Introduced as a follow-up; see below.)
2. ``base_version.latest_successful_build.commit`` — the base version's most
   recent successful build. This is what the initial implementation uses, and
   the fallback when ``base_identifier`` isn't set (GitLab's merge request
   payload has no equivalent field; versions created before ``base_identifier``
   existed).

.. note::

   The initial change resolves ``base_commit`` from
   ``latest_successful_build.commit`` only. Capturing ``pull_request.base.sha``
   into ``Version.base_identifier`` and preferring it is a stacked follow-up —
   it's more precise (the base the PR *targets*, rather than whatever the base
   version last built), needs no forge API, and is plumbed from a webhook field
   we already receive.

Where the code runs
-------------------

The refresh check needs the live git clone, so it runs *during* the build, not
in the post-build indexing task:

- ``refresh_snapshot_if_stale`` (``readthedocs/filetreediff/__init__.py``) is
  called from ``UpdateDocsTask.execute`` in
  ``readthedocs/projects/tasks/builds.py``, inside the VCS environment context
  (after ``setup_vcs``, before the environment is torn down).
- Snapshot *creation* on the first PR build still happens in
  ``FileManifestIndexer.collect``, which runs in the ``index_build`` Celery task
  after the build — the clone is already gone by then, but creation only needs
  the base manifest from storage, not git.

So there are two writers for one snapshot file: the indexer creates it, the
build task refreshes it. This split exists because creation and refresh have
different data dependencies (storage vs. live git).

The remaining gap
-----------------

The snapshot is always written from the base version's *latest* manifest, and
the manifest is **per-version, overwritten on every build** — there is no
per-build manifest history. So if the base branch has moved *further* than the
commits the user merged in, we can't reconstruct the exact merge-base manifest;
we can only snapshot "current base," which may be slightly too new. A few
base-only files can then still show as changed.

This is a **storage** limitation, not a detection one. Computing a more precise
merge-base (even via a forge API) would not help, because we still couldn't
materialize the manifest for that commit. In practice the gap is small for
active projects, since the base builds frequently and ``latest_successful_build``
stays close to the merge-base.

Path forward
------------

The clean fix for the remaining gap is **per-build manifest history**: store a
manifest per build (e.g. content-addressed by commit) instead of overwriting one
per version, and pin the diff to the exact merge-base build via a
``Build.diff_base_build`` foreign key. That removes the "current base is too new"
approximation entirely and would let the refresh check resolve to the precise
merge-base manifest.

That redesign is independent of, and supersedes, the smart-refresh approach
described here. A prototype exists on the ``claude/compassionate-thompson-iEEik``
branch. Until it lands, the merge-base ``--is-ancestor`` check is the best
approximation available within the per-version storage model.

Things to know before touching this
------------------------------------

- **The base branch name is not persisted.** It arrives on the webhook
  (``ExternalVersionData.base_branch``) and is used to drive the fetch, then
  discarded. Only ``base_identifier`` (the base *commit*) is stored. Don't assume
  you can read the base branch name at build time.
- **Shallow clones.** ``git merge-base --is-ancestor`` can return non-zero
  simply because a commit is beyond the fetch depth. The check treats that as
  "don't refresh," which is safe (worst case is current behavior), but it means
  the refresh silently no-ops on deep histories.
- **Everything is best-effort.** ``should_refresh_snapshot`` and
  ``refresh_snapshot_if_stale`` swallow every failure and fall back to the
  existing write-once snapshot. A bug here degrades the diff; it must never fail
  a build.
