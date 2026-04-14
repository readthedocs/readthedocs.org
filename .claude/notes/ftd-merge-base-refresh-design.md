# File Tree Diff: Refresh Base Manifest on PR Merge-Base Change

## Problem

`#12922` introduced a "base manifest snapshot" to fix the stale-branch bug in
the file tree diff feature: when the base branch (e.g. `main`) moved forward
after a PR was opened, subsequent PR builds would diff against the *new* base
and show files that landed on main as if they'd been deleted from the PR.

The snapshot fixed that by pinning the base manifest at first PR build. But it
introduced a new problem: the snapshot lives forever. When the PR is later
rebased onto a newer base, the snapshot is stale and shows files that the
rebase brought in as false "additions" in the PR.

`#12923` was a first attempt at fixing this: clear the snapshot on the webhook
`synchronize` event. That turned out to be wrong — `synchronize` fires on
*every* push to the PR head branch, including normal "I added a commit to my
PR" pushes. Clearing then meant the snapshot was recreated against whatever
main was at *now* on every build, which is exactly what the snapshot was
supposed to prevent.

## What we actually want

Refresh the snapshot only when the PR's relationship to its base branch
actually changes. That means detecting rebases and base-branch retargets, not
every push.

## The signal: git merge-base

The correct signal is the git merge-base between the PR head and the base
branch. It changes when:

- The PR is rebased onto a newer base (merge-base moves forward to the new
  common ancestor).
- The PR is retargeted to a different base branch (merge-base changes to the
  new branch's common ancestor).
- Someone merges the base branch into the PR branch (same effect as rebase).

It does *not* change when the user just pushes new commits to their PR branch
without touching the base.

The webhook payload alone can't tell us this — `pull_request.base.sha` in the
synchronize payload is just the current tip of the base branch at webhook
time, which moves whenever main moves, regardless of whether the user actually
rebased. We need real git knowledge.

## Approach

**Compute merge-base at build time, store it in the manifest, refresh the
snapshot when it differs.**

### Plumbing

1. **`Version.base_branch`** (new field, migration) — persisted from the
   webhook. The PR's target branch name (e.g. `"main"`, `"develop"`). Rarely
   changes (only on retarget). Also gives us durable PR-target metadata
   queryable in SQL for future features.

2. **`Build.merge_base`** (new field, migration) — computed during the build
   worker phase. The git merge-base between the PR head and the base branch
   at the time of this build.

3. **`BuildDirector.setup_vcs()`** — after checkout, for external versions:
   - Shallow-fetch the base branch (`--depth 500`) into
     `refs/remotes/origin/<base_branch>`.
   - Deepen the PR head ref by the same amount so merge-base has enough
     history on both sides.
   - Run `git merge-base origin/<base_branch> HEAD`.
   - Store the result on `self.data.build["merge_base"]`, which the existing
     build API patch persists to the Build row.
   - All failures are non-fatal: fetch errors, missing refs, or
     merge-base-not-found all return `None` and the feature degrades
     gracefully.

4. **`FileTreeDiffManifest`** — gains an optional `merge_base` field.
   Backwards-compatible (`from_dict` uses `data.get("merge_base")`, defaults
   to `None` for older snapshots).

5. **`FileManifestIndexer.collect()`** — reads `self.build.merge_base` and
   includes it when writing both the PR's own manifest and when calling
   `snapshot_base_manifest()`.

6. **`snapshot_base_manifest()`** — the refresh logic:

   | State | Action |
   |---|---|
   | No existing snapshot | Create, pin to current merge-base |
   | Existing snapshot, same merge-base | No-op |
   | Existing snapshot, different merge-base | Refresh with new content + new merge-base |
   | Existing snapshot, current merge-base unknown | Keep existing (graceful fallback) |

### Why the manifest, not cache or a side channel

The manifest is already a JSON file in storage that both the build worker and
the indexer use for diffing. `merge_base` is only ever consulted for one
decision (should we refresh this snapshot?) and that decision happens where
the manifest is already being read. No cache, no API handoff, no extra
storage round-trip — the merge-base lives exactly where it's used.

`Build.merge_base` exists because the indexer runs in a separate Celery task
(`reindex` queue) after the build worker has cleaned up, and the git clone is
gone by then. The field is the cleanest cross-worker handoff and doubles as
queryable history.

## Behavior matrix

| Scenario | Outcome |
|---|---|
| First PR build | Snapshot created, pinned to current merge-base |
| User pushes commit to PR head (no rebase) | merge-base unchanged → snapshot kept |
| User rebases PR onto newer base | merge-base changes → snapshot refreshed |
| User retargets PR to different base branch | `base_branch` updates on next webhook → merge-base changes → snapshot refreshed |
| Shallow clone too shallow to find merge-base | `current_merge_base=None` → existing snapshot kept (pin-once fallback) |
| Old snapshot from before this change | `existing.merge_base is None` vs `current="abc"` → refreshed on next build |
| Legacy build without `Build.merge_base` set | `current_merge_base=None` → pin-once fallback |

## What we shelved

The branch `claude/clear-snapshot-on-rebase` had this implemented as a single
commit on top of main, with:

- Migration `0071_add_merge_base_fields.py`
- Model field updates in `readthedocs/builds/models.py`
- Webhook persistence in `readthedocs/core/views/hooks.py`
- Merge-base computation in `readthedocs/doc_builder/director.py`
- Manifest schema update in `readthedocs/filetreediff/dataclasses.py`
- Refresh logic in `readthedocs/filetreediff/__init__.py`
- Indexer wiring in `readthedocs/projects/tasks/search.py`
- Tests covering all four refresh states

Total: ~245 lines added, ~39 removed. One migration, two new CharFields.

The associated PR `#12923` was closed (not merged). The original stale-branch
fix from `#12922` is live; it just uses pin-once-forever semantics instead of
merge-base-aware refresh, which means PRs that get rebased onto a newer base
still show slightly-wrong diffs until someone builds them fresh.

## Why we shelved it

It's a correct and reasonably small change, but it touches the build pipeline
(git fetches, new model fields, migration, director logic) for a feature
that's currently a small quality-of-life improvement to the PR diff feature.
The pin-once-forever behavior from `#12922` is already "mostly right" for the
common case and the extra correctness isn't urgent.

Worth revisiting if/when:

- We want to surface merge-base or base-branch info in the UI (e.g. "this PR
  is N commits behind main").
- Users start reporting rebase-related diff weirdness often enough to be
  painful.
- We pick up the broader "better understand what the PR is merging into"
  theme and want the DB foundation for it.

## Future extensions that become cheap once this lands

- Query analytics: "show me all PRs targeting `develop`".
- UI nudge: "your PR is 47 commits behind `main`" (compare `Build.merge_base`
  against `base_version.latest_successful_build.commit`).
- Precise `outdated` flag: today it's approximate; with `merge_base` it can be
  exact.
- Historical diff reproducibility: old builds can be re-diffed correctly
  against the state they originally represented.
