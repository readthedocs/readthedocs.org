Parse docs on the builder
=========================

Parse each page once, on the builder, where the files are already on local disk,
and ship the result with the build —
instead of re-downloading the whole version from S3 after the build
to produce the same thing on a web worker.

The first phase is the file tree diff manifest,
because it is what a user is waiting on:
the pull request build-overview comment and files changed
can't show until it exists.
Today that wait is the ``reindex`` queue plus a full re-download of the version;
with the manifest shipped by the builder it is a small task on the ``web`` queue
that runs the moment the build turns green.

Search indexing is unchanged in this phase.
Moving the parsed search content to the builder as well is the second phase,
sketched at the end.

Goals
-----

- Post the pull request build-overview comment,
  and make files changed available,
  seconds after a build finishes — independent of the ``reindex`` queue.
- Stop paying a full S3 download of the version to produce the manifest.
- Keep all Elasticsearch and database access server-side: builders gain no new trust.
- Nothing regresses when a builder ships no manifest:
  the server-side path stays as the fallback until the legacy fleet is gone.

Non-goals
---------

- Changing the upload client or its zip format — the isolated worker covers uploaded builds.
- Adding manifest generation to the legacy fleet;
  it stays on today's path and ages out with the isolated-builds migration.
- Changing what the manifest contains or how pages are hashed —
  the same parser output, produced where the files already are.
- Re-parsing already-built versions when the parser changes —
  parser changes roll forward with new builds (`discussion on #13246`_).
- Search indexing for pull request versions — external versions stay unindexed, as today.

What changes for users
----------------------

Today the pull request comment and files changed wait for `index_build`_
on the ``reindex`` queue.
With the queue idle that is about 15 seconds after the build finishes on average,
longer for large documentation sets, and noticeably longer on busy days;
while a bulk re-index runs, it is hours.
The docs pages themselves are not affected —
since `#13276`_ the docs CDN is purged at build success.

Proposed: the comment is posted, and files changed is available,
as soon as the build is marked finished —
the task reads one small file from S3 and does no parsing.
Builds get no slower: the parse runs on the builder
while the HTML is still being uploaded, and takes a few seconds.

How it works today
------------------

#. The builder syncs the built HTML to S3 and reports the build as finished.
#. At build success the server queues two tasks:
   `purge_docs_cdn`_ (``web`` queue) so the pages go live,
   and `index_build`_ (``reindex`` queue) for everything else.
#. ``index_build`` `downloads the whole version`_ with ``rclone`` into a scratch directory
   and parses every page once.
   That one walk feeds three indexers:
   Elasticsearch documents, the ``index.html``/``404.html`` records El Proxito serves 404s from,
   and the `file tree diff manifest`_.
#. After the manifest is written, the same task `snapshots the base manifest`_
   for pull request versions and `queues the build-overview comment`_.

Where the time goes: profiling on `#13246`_ put about 80% of ``index_build``
in the S3 download, the rest in parsing.
The download was already reduced from one GET per page to a single ``rclone`` sync by `#13246`_,
and the queue is fast when idle —
but every build still re-downloads what the builder uploaded moments earlier,
and the comment still waits behind whatever else is on ``reindex``.
Scaling out the ``reindex`` workers would shorten the queue wait,
not the round trip, and not the S3 bill.

Proposed: ship the manifest with the build
------------------------------------------

Three steps (`readthedocs-builder#40`_ and the matching readthedocs.org change):

#. **The builder parses and uploads the manifest.**
   Right after the HTML sync starts in `_upload_artifacts`_,
   the builder parses the HTML it just built
   with a port of `readthedocs/search/parsers.py`_
   and writes ``diff/<project>/<version>/manifest.json`` —
   the same file `FileManifestIndexer`_ writes today, with the same hashes,
   plus the build id it belongs to and a ``hasher_version``.
   It uses the per-build scoped S3 credentials it already holds:
   the `STS policy`_ is built from ``Version.get_storage_paths()`` and spans every media type,
   including ``diff``.
   The parse runs in a thread while ``rclone`` syncs the HTML,
   and the manifest is uploaded once both are done —
   before the build is marked finished.
   Uploaded-zip builds are covered too,
   since the isolated worker `downloads and extracts the zip`_ before the sync;
   the upload client needs no changes.
   A manifest failure is logged and never fails the build.
#. **A ``web`` task uses it at build success.**
   Next to ``purge_docs_cdn`` and ``index_build``, the server queues
   ``process_builder_manifest`` on the ``web`` queue.
   It reads the manifest, checks that it belongs to this build,
   and then does what the tail of ``index_build`` does today:
   snapshots the base manifest for pull request versions
   and queues the build-overview comment.
   If there is no manifest, or it is from another build, the task does nothing.
#. **``index_build`` skips what the builder already did.**
   `_get_indexers`_ leaves out ``FileManifestIndexer`` when a manifest for this build is already stored.
   Everything else in ``index_build`` is unchanged:
   search indexing, the ``index.html``/``404.html`` records, and the ``rtd-search`` CDN purge.
   When no manifest arrived — legacy-fleet builds, or a failed upload —
   it generates the manifest and posts the comment exactly as today.

The upload is a single file, not a sync of the ``diff/`` prefix,
so the server-written base-manifest snapshot next to it is never deleted.

Security
--------

The parse runs in the builder process, outside the build container —
the same place the upload step already walks the output directory.
The rules are the ones that step follows today:

- Read regular files only; never follow symlinks.
  The build can write anything into its output directory,
  including a link to a file on the host.
- Keep the parser's caps on page and section size.
- Server-side, the manifest is untrusted input:
  the task validates its shape, ignores unknown keys,
  and only acts on it when the build id matches the build that just finished.

Builders never talk to Elasticsearch or the database;
they hold a per-build, project-scoped API key and the storage credentials they have today.

Changing the parser
-------------------

A parser change ships in the builder image and rolls forward:
it reaches each version on its next build, and nothing re-parses what is already built
(`discussion on #13246`_ — maintaining the parser server-side as well,
just to re-extract old builds, is the duplication both reviewers flagged).
A version that never rebuilds isn't changing its pages either,
so its stored manifest stays an accurate index of them.

Roll-forward is why the manifest carries a ``hasher_version``:
after a change to what the hashes mean,
a pull request built with the new parser diffs against a base version that may not have rebuilt yet.
``get_diff`` treats the mismatch as "outdated" instead of reporting every file as modified,
and it heals on the base version's next build.
The field is written from the first builder release and enforced server-side once both sides carry it;
today's reader ignores unknown keys, so the order doesn't matter.
It is bumped only for hash-meaning changes, not every parser release —
otherwise every release would invalidate every open pull request's diff.

Golden HTML fixtures with expected hashes, committed to both repositories,
catch accidental hash drift in CI.

Rollout
-------

#. Already merged: `#13276`_ purges the docs CDN at build success,
   and `#13246`_ replaced the per-page S3 reads in ``index_build`` with one ``rclone`` download.
#. readthedocs.org, deploys first: skip ``FileManifestIndexer`` when a manifest for the current build exists;
   add ``process_builder_manifest`` and queue it at build success on both fleets' success paths.
   Nothing changes until a builder ships a manifest.
#. readthedocs-builder (`readthedocs-builder#40`_): port the parser with its golden-fixture tests,
   emit the manifest from ``_upload_artifacts``.
   Verify on a few projects that the server-side and builder-side manifests match
   before enabling it fleet-wide.
#. Enforce ``hasher_version`` in ``get_diff`` once every manifest in storage carries it.

The two quick-relief changes considered earlier —
routing external versions' ``index_build`` to the ``web`` queue,
and skipping the manifest when a project has neither feature on —
were dropped: the queue is fast now, and with the manifest produced on the builder
the pull request path no longer depends on ``index_build`` at all.

Phase 2: search content from the builder
----------------------------------------

The same parse produces everything Elasticsearch indexing consumes:
path, title, sections, and the content hashes.
Shipping that as a second, compressed artifact
would let ``index_build`` ingest one file instead of downloading the version,
and let full re-indexes replay stored payloads instead of re-parsing the corpus.

That phase has its own questions, left open here:

- Internal versions would always emit the payload, whether or not search is enabled for the project,
  so turning search on later re-indexes from the stored payload rather than re-parsing;
  pull request versions would emit only the manifest.
- Payload size on the largest projects, and the file format,
  need bounds before payload replay becomes the re-index path.
- The server-side parser can only be deleted once payloads exist for every version still being served,
  which needs a one-time pass over the long tail.

Background: why it works this way today
---------------------------------------

No one designed the S3 round trip;
it is the residue of a local-disk pipeline surviving two migrations.
There is no public issue proposing and rejecting builder-side processing —
each era's constraints simply made it impossible.

- **2010–2013** — ``ImportedFile`` appears (Aug 2010) and ``fileify`` becomes a Celery task (Jan 2013),
  "a prereq for indexing the docs for search," running server-side;
  builders already went through the API, not the ORM.
- **pre-2019** — builders rsync artifacts to every web node;
  ``fileify`` runs after the sync, walking local disk with ``os.walk``
  and md5-hashing every file to compute per-file CDN purge URLs.
  The purge consumed the walk's output —
  the original reason purging stayed welded to indexing until `#13276`_.
- **2019** — `#5854`_ points the same walk at blob storage
  while shared filesystems and the syncers are removed.
  The S3 round trip begins here as a port, not a decision;
  the performance implications of walking cloud storage were flagged in the PR.
- **2020** — `#7161`_ adds the ``reindex`` queue
  ("this should make our web queue not backup as much").
  `#7204`_/`#7208`_ switch parsing from Sphinx fjson to the HTML itself —
  needed for tool-agnostic builds, and it raises the per-page cost.
- **2022–2023** — builders are locked down: API-only build task (`#8815`_),
  per-build scoped API keys (`#10378`_).
  `#10696`_ replaces ``fileify`` with today's ``index_build``,
  walking storage instead of the DB —
  ImportedFile had become one of the largest tables (`#10623`_).
- **2024** — the :doc:`file tree diff design doc <file-tree-diff>`
  states the manifest "will be done at the end of the build";
  `#11646`_ implements it inside ``index_build`` instead,
  because the server-side walk existed and the isolated builder didn't yet.
- **2026** — `#13246`_ swaps the per-page storage reads for one ``rclone`` download per build.

Two of the three original constraints have since reversed:
built files are now local to the builders rather than the webs,
and builders hold per-build scoped storage credentials.
The one that stands — builders run untrusted code
and never hold DB or Elasticsearch credentials — is the one this proposal keeps.

.. _#13276: https://github.com/readthedocs/readthedocs.org/pull/13276
.. _#13246: https://github.com/readthedocs/readthedocs.org/pull/13246
.. _discussion on #13246: https://github.com/readthedocs/readthedocs.org/pull/13246#issuecomment-5933896429
.. _readthedocs-builder#40: https://github.com/readthedocs/readthedocs-builder/pull/40
.. _#10623: https://github.com/readthedocs/readthedocs.org/issues/10623
.. _#5854: https://github.com/readthedocs/readthedocs.org/pull/5854
.. _#7161: https://github.com/readthedocs/readthedocs.org/pull/7161
.. _#7204: https://github.com/readthedocs/readthedocs.org/pull/7204
.. _#7208: https://github.com/readthedocs/readthedocs.org/pull/7208
.. _#8815: https://github.com/readthedocs/readthedocs.org/pull/8815
.. _#10378: https://github.com/readthedocs/readthedocs.org/pull/10378
.. _#10696: https://github.com/readthedocs/readthedocs.org/pull/10696
.. _#11646: https://github.com/readthedocs/readthedocs.org/pull/11646
.. _index_build: https://github.com/readthedocs/readthedocs.org/blob/5a851c553bc7598b9c5bf3a0e11ba90faa1aec8c/readthedocs/projects/tasks/search.py#L341
.. _purge_docs_cdn: https://github.com/readthedocs/readthedocs.org/blob/5a851c553bc7598b9c5bf3a0e11ba90faa1aec8c/readthedocs/builds/tasks.py#L815
.. _downloads the whole version: https://github.com/readthedocs/readthedocs.org/blob/5a851c553bc7598b9c5bf3a0e11ba90faa1aec8c/readthedocs/projects/tasks/search.py#L292
.. _file tree diff manifest: https://github.com/readthedocs/readthedocs.org/blob/5a851c553bc7598b9c5bf3a0e11ba90faa1aec8c/readthedocs/projects/tasks/search.py#L161
.. _FileManifestIndexer: https://github.com/readthedocs/readthedocs.org/blob/5a851c553bc7598b9c5bf3a0e11ba90faa1aec8c/readthedocs/projects/tasks/search.py#L161
.. _snapshots the base manifest: https://github.com/readthedocs/readthedocs.org/blob/5a851c553bc7598b9c5bf3a0e11ba90faa1aec8c/readthedocs/projects/tasks/search.py#L204
.. _queues the build-overview comment: https://github.com/readthedocs/readthedocs.org/blob/5a851c553bc7598b9c5bf3a0e11ba90faa1aec8c/readthedocs/projects/tasks/search.py#L211
.. _`_get_indexers`: https://github.com/readthedocs/readthedocs.org/blob/5a851c553bc7598b9c5bf3a0e11ba90faa1aec8c/readthedocs/projects/tasks/search.py#L214
.. _`_upload_artifacts`: https://github.com/readthedocs/readthedocs-builder/blob/54f47c3/builder/builder/runner.py#L447
.. _downloads and extracts the zip: https://github.com/readthedocs/readthedocs-builder/blob/54f47c3/builder/builder/director.py#L917
.. _STS policy: https://github.com/readthedocs/readthedocs.org/blob/5a851c553bc7598b9c5bf3a0e11ba90faa1aec8c/readthedocs/aws/security_token_service.py#L147
.. _readthedocs/search/parsers.py: https://github.com/readthedocs/readthedocs.org/blob/5a851c553bc7598b9c5bf3a0e11ba90faa1aec8c/readthedocs/search/parsers.py
