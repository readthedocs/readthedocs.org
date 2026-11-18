Pull request diffs
==================

This document covers what a pull request is compared against in the file tree diff (:doc:`file-tree-diff`),
the build overview comment, and visual diff,
and proposes one answer for all of them.

Problem
-------

Each feature picks its own base today:

.. list-table::
   :header-rows: 1

   * - Feature
     - Compares the pull request against
   * - Files changed (flyout and build overview comment)
     - A copy of the base version's manifest, taken on the pull request's first build and never refreshed
       (`#12922 <https://github.com/readthedocs/readthedocs.org/pull/12922>`__)
   * - Visual diff
     - The base version's page as it is right now, fetched by the browser
   * - Sorting by changed blocks (`#13424 <https://github.com/readthedocs/readthedocs.org/pull/13424>`__)
     - The base version's page as it is right now, read from storage

None of these is the pull request's merge base, so each is wrong in its own way:

- The pinned copy goes stale when the base branch is merged into the pull request, or it is rebased.
  The base's own changes then show up as added by the pull request.
- The live base moves under the pull request.
  Visual diff highlights changes the pull request never made,
  which is the larger complaint in `#12232 <https://github.com/readthedocs/readthedocs.org/issues/12232>`__.
- The features disagree with each other.
  A page can be listed as unchanged and still light up in visual diff, or the other way around.

The cause is the same in every case.
Build output is stored per version and overwritten on every build,
so "the base version as built at commit X" doesn't exist once the base builds again.
Each feature works around that on its own.

Goals
-----

- Compare a pull request against its merge base: the newest base commit it contains.
  This is what GitHub's "files changed" does, and it holds when the base moves, is merged in, or the pull request is rebased.
- Every feature uses the same base, and can say which one it is ("compared against ``latest`` at ``abc123``").
- No extra builds, and nothing that needs the builder to reach the database or storage.

Proposed design
---------------

Three pieces: remember recent base builds, pick one per pull request build, and compute the diff once.

Base history
~~~~~~~~~~~~

When the base version is indexed, we keep two things in its ``diff`` storage instead of one overwritten manifest:

``manifests/<build_id>.json``
   The manifest for that build, same format as today.

``content/<hash>.html``
   The main content of each page, stored under the hash of its content.
   A page that didn't change between builds is already there and isn't written again,
   so each base build only adds the pages it changed.

This is the same idea as git's trees and blobs, limited to what diffs need.
The main content is already extracted and hashed when the manifest is written,
so this adds uploads for changed pages and no new parsing.

A daily task keeps the manifests of the newest 50 base builds,
plus any that an open pull request is still compared against,
and deletes content no kept manifest refers to.

The base build
~~~~~~~~~~~~~~

Only the build has a git clone, so the build picks the base:

#. The version API response for a pull request includes ``base_commits``:
   the commits of the base builds we have a manifest for, newest first.
#. After checkout, the build runs ``git rev-list HEAD`` once
   and reports the first of those commits it finds.
   That is the merge base, or the closest built commit before it.
   The clone already has the pull request's history, so there is no extra fetch.
#. The API stores it as ``Build.base_build``, a foreign key to the base version's build.

The isolated builder and the legacy build task do this with the same few lines.
`#13329 <https://github.com/readthedocs/readthedocs.org/pull/13329>`__ and
`readthedocs-builder#26 <https://github.com/readthedocs/readthedocs-builder/pull/26>`__
already do it for a single candidate and carry most of the plumbing.

One stored diff
~~~~~~~~~~~~~~~

When a pull request build is indexed, we diff its manifest against the base build's manifest
and store the result as ``diff.json`` next to the pull request's manifest:
the base build, and the added, deleted, and modified files.

Everything reads that file:

- The addons API and the build overview comment return it as is,
  instead of reading two manifests from storage and diffing them on each request.
- The changed blocks count from #13424 is computed from the base build's stored content and saved in it.
- The per pull request snapshot (``base_manifest_snapshot.json``) goes away. ``Build.base_build`` replaces it.

Visual diff
~~~~~~~~~~~

Visual diff keeps diffing in the browser. Only where the base page comes from changes.

``doc_diff.base_url`` in the addons API points at a new endpoint
that serves the page's main content from the base build's stored content,
with the same permission check the base version has.
The browser no longer fetches and parses the live base page through the embed API.

The result is that visual diff shows exactly the pages that files changed lists, against the same base,
and stops changing when the base branch moves.

Behavior
--------

.. list-table::
   :header-rows: 1

   * - Scenario
     - Result
   * - First build of a pull request
     - Compared against the merge base, even when the branch is old
   * - New commits on the pull request, base untouched
     - Same base build
   * - Base moves forward
     - Same base build, in files changed and in visual diff
   * - Base merged into the pull request, or rebased
     - Base build moves to the new merge base
   * - Base build's manifest or content is missing
     - Falls back to the live base version, as today

Fallbacks
---------

When the build finds no candidate, the pull request is compared against the newest base build at the time of its first build,
and keeps that base on later builds.
This matches today's behavior, and applies when:

- The pull request targets a branch other than the base version.
- The merge base is older than the manifests we keep.
- The shallow clone (``--depth 50``) doesn't reach a candidate.
- The project uploads its docs directly, so there is no clone.
  The upload client can send the base commit later.

Alternatives considered
-----------------------

Clear the snapshot on webhook ``synchronize`` events
   `#12923 <https://github.com/readthedocs/readthedocs.org/pull/12923>`__.
   ``synchronize`` fires on every push, so this compared against the live base on every build.

Compute ``git merge-base`` against the base branch
   The shelved first version of this design.
   It needs the base branch name on the version and a second, deeper fetch,
   and returns a commit we usually have no build for.

A manual reset, or expiring the snapshot after some time
   Simple, but both reset to the live base, which is the problem #12922 fixed.

Copy the base version's HTML into each pull request
   `#12928 <https://github.com/readthedocs/readthedocs.org/pull/12928>`__.
   Fixes visual diff for the base moving, but copies every page for every pull request,
   and still pins to the first build.

S3 object versioning on the docs bucket
   Would keep old base pages with no code.
   Most pages change on every build (dates, commit hashes in footers),
   so it stores every build of every version in full, and applies to the whole bucket.

Pick the base by similarity
   Choose the stored base manifest with the fewest differences from the pull request, with no git involved.
   It works for direct uploads, but a pull request that reverts a change matches the build before that change
   and shows an empty diff.

Build the merge base ourselves
   Exact, but doubles the builds for every pull request.

Rollout
-------

Each step ships on its own and is useful without the next.

#. **Base history.**
   Write per-build manifests and page content for base versions, and add the cleanup task.
   Nothing reads them yet.
#. **Base build.**
   ``Build.base_build``, ``base_commits`` in the API, and the builder change.
   Files changed and the comment use the base build's manifest.
   This fixes the merged-in and rebased cases.
#. **Stored diff.**
   Write ``diff.json`` at index time, read it from the addons API and the comment, and drop the snapshot.
#. **Visual diff.**
   Serve base content from the base build and point ``doc_diff.base_url`` at it.

The order between web and builder doesn't matter:
without a reported base commit everything behaves as it does today.

Open questions
--------------

- **Main content selection.**
  Visual diff uses the root selector from addons, and the manifest uses the search parser's main node.
  They need to select the same element for the stored content to line up with the page in the browser.
  Both start from ``[role=main]``, but projects with a custom root selector need checking.
- **Storage.**
  Measure the content added per base build on a few large, busy projects before settling on 50 builds.
- **Parsing on the builder.**
  With `#13355 <https://github.com/readthedocs/readthedocs.org/pull/13355>`__ the builder writes the manifest.
  It would upload the page content too, which it has on disk.
