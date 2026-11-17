Pull request diff base
======================

This document covers which state of the base version a pull request is compared against
in the file tree diff (:doc:`file-tree-diff`),
the build overview comment, and visual diff.

Problem
-------

A pull request is compared against the project's base version (``latest`` unless set in the addons settings).
That comparison goes wrong in two opposite ways:

- **The base moves forward.**
  Files that changed on the base branch after the pull request was opened show up as changed by the pull request.
- **The pull request catches up.**
  When the base branch is merged into the pull request, or the pull request is rebased,
  the base's own changes show up as added by the pull request.

`#12922 <https://github.com/readthedocs/readthedocs.org/pull/12922>`__ fixed the first case:
the first successful build of a pull request copies the base version's manifest into a snapshot
(``base_manifest_snapshot.json``), and later diffs use that snapshot.
The snapshot is never refreshed, so the second case is still broken.
See `#12232 <https://github.com/readthedocs/readthedocs.org/issues/12232>`__.

What we want
------------

Compare a pull request against the base as it was at the pull request's merge base:
the newest base commit the pull request contains.
That is the same baseline GitHub uses for "files changed",
and it stays correct when the base moves forward, when the base is merged in, and after a rebase.

Two things stand in the way:

- Only the build has a git clone, so only the build can tell which base commits the pull request contains.
  The isolated builder has no database or storage access, so it can answer the question but not act on it.
- Manifests are stored per version and overwritten on every build,
  so the manifest for an older base commit is gone by the time we know we need it.

Proposed solution
-----------------

Keep a short history of base manifests, have the build pick the one at the merge base,
and point the snapshot at it.

Keep base manifests per commit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the base version is indexed,
``FileManifestIndexer`` writes ``manifests/<commit>.json`` next to the existing ``manifest.json``.
It keeps the newest 50 and deletes the rest in the same step.

Manifests are a few KB to a few hundred KB, so this is cheap.
50 builds covers weeks of history for active projects,
and pull requests that fall outside it keep their current snapshot (see `Fallbacks`_).

Send the candidates to the build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The version API response for a pull request includes ``base_commits``:
the commits of the base version's newest 50 successful builds, newest first.
These are the commits we have a manifest for.

Pick the merge base on the build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After checkout, the build runs ``git rev-list HEAD`` once
and reports the first entry of ``base_commits`` it finds there as ``Build.base_commit``.
That is the newest base state the pull request contains, which is the merge base,
or the closest built commit before it.

No extra fetch is needed:
the clone already has the pull request's history, including any base commits merged into it.
Both the isolated builder and the legacy build task do this, with the same few lines.

Point the snapshot at it
~~~~~~~~~~~~~~~~~~~~~~~~

When the pull request is indexed and ``Build.base_commit`` is set,
``FileManifestIndexer`` copies ``manifests/<base_commit>.json`` from the base version into the pull request's snapshot,
unless the snapshot already comes from that commit.
Diffing is unchanged: it reads the snapshot as it does today.

The indexer stays the only writer of the snapshot, and the snapshot only changes on successful builds.

Behavior
--------

.. list-table::
   :header-rows: 1

   * - Scenario
     - Result
   * - First build of a pull request
     - Snapshot at the merge base
   * - New commits on the pull request, base untouched
     - Same merge base, snapshot unchanged
   * - Base moves forward
     - Same merge base, snapshot unchanged
   * - Base merged into the pull request, or rebased
     - Merge base moves, snapshot follows it
   * - Pull request retargeted to another base version
     - Picks the merge base of the new target on the next build

Fallbacks
---------

If no candidate is found, the build reports nothing and the current behavior applies:
the first build creates the snapshot from the live base manifest, and later builds keep it.
That happens when:

- The pull request targets a branch other than the base version, so none of the base's commits are in its history.
- The merge base is older than the 50 manifests we keep.
- The shallow clone (``--depth 50``) doesn't reach back to a candidate.

Alternatives considered
-----------------------

Clear the snapshot on webhook ``synchronize`` events
   `#12923 <https://github.com/readthedocs/readthedocs.org/pull/12923>`__.
   ``synchronize`` fires on every push, so this rebuilt the snapshot from the live base on every build
   and undid the fix from #12922.

Compute ``git merge-base`` against the base branch
   The shelved first version of this design.
   It needs the base branch name stored on the version, a second fetch with deeper history,
   and still only tells us a commit we usually have no manifest for.

Refresh from the live base manifest when it is an ancestor
   `#13329 <https://github.com/readthedocs/readthedocs.org/pull/13329>`__.
   This is the proposed solution with a single candidate and no history.
   It fixes the common case of merging in the latest base,
   but leaves a snapshot that is too new when the base has moved further than what was merged.

A manual reset, or expiring the snapshot after some time
   Simple, but it resets to the live base, which brings back the first problem.
   With the merge base tracked, there is nothing left to reset.

Rollout
-------

#. Write per-commit manifests for base versions, so history builds up before anything reads it.
#. Add ``Build.base_commit``, ``base_commits`` in the API, and the indexer change.
   Rework #13329 and `readthedocs-builder#26 <https://github.com/readthedocs/readthedocs-builder/pull/26>`__ for this,
   since they already carry most of the plumbing.
#. Update the user docs on visual diff to drop the known issue about stale snapshots.

The order between web and builder doesn't matter:
without ``Build.base_commit`` the indexer keeps today's behavior,
and the API ignores the field until the migration lands.
