Parse docs on the builder
=========================

Parse each page once, on the builder, where the files are already on local disk —
instead of re-downloading every page from S3 after the build.
The parse output ships with the build as two artifacts —
the file tree diff manifest and the search payload —
and server-side post-build work shrinks to a light ingest task.

Two headline wins:

- **S3 reads**: from one GET per HTML page per build —
  the whole version re-downloaded right after the builder uploaded it —
  to a single GET for the payload at ingest.
- **Availability after build**: files changed, the pull request build-overview comment,
  and fresh search results land seconds after the build finishes,
  instead of waiting behind the ``reindex`` queue backlog.

Goals
-----

- Serve files changed, pull request build-overview comments, and fresh search results
  seconds after a build finishes, independent of the ``reindex`` queue.
- Eliminate the per-page S3 download-and-parse that follows every build today.
- Keep all Elasticsearch and database access server-side: builders gain no new trust.
- Make full Elasticsearch re-indexes replay stored payloads instead of re-parsing the corpus.
- End with one parser implementation, on the builder —
  the server-side parse path is transitional, not a second copy to maintain.

Non-goals
---------

- Changing the upload client or its zip format — the isolated worker covers uploaded builds.
- Adding manifest or payload generation to the legacy fleet;
  it stays on today's path and ages out with the isolated-builds migration.
- Changing what gets indexed or how pages are parsed —
  the same parser output, produced where the files already are.
- Re-parsing already-built versions when the parser changes —
  parser changes roll forward with new builds (`discussion on #13246`_).
- Search indexing for pull request versions — external versions stay unindexed, as today.
- Combining the manifest and payload into a single artifact —
  the manifest could later be derived from the payload server-side;
  two independent files keep this iteration's moving pieces fewer.

How it works today
------------------

A build uploads its HTML to S3 and turns green — and since `#13276`_,
the docs CDN is purged right there, so the pages themselves go live at build finish.
Everything else happens afterwards, in `index_build`_ on the ``reindex`` queue:
`_process_files`_ walks the version's storage prefix,
and each page is downloaded and parsed via ``HTMLFile.processed_json`` → `GenericParser.parse`_,
which `opens every file from storage`_.
That one walk produces the file tree diff manifest, the Elasticsearch documents,
and the ``index.html``/``404.html`` records El Proxito serves 404s and directory redirects from.
The ``rtd-search`` CDN purge (`search_index_updated`_) and the pull request build-overview comment
ride on the same task.

What this costs:

- Every page makes a full round trip: uploaded by the builder,
  then immediately re-downloaded and parsed on web-side workers.
  The cost predates today's feature set:
  profiling in `#10623`_ measured the predecessor task (``fileify``)
  at ~9.1s per build on average, ~2.5s of it boto3/S3 calls — before file tree diff existed.
- Everything user-visible from this task waits behind the queue:
  files changed, the pull request overview comment, and fresh search results;
  a bulk re-index backlog delays them by hours.
- Pull request builds pay the full download-and-parse solely for the manifest:
  `search indexing skips external versions`_,
  and the `manifest gate`_ checks ``is_external`` but not ``filetreediff_enabled`` —
  that flag is only checked `at serve time`_.
  Every pull request build of every project pays,
  even with file tree diff and build overview comments off.
- A full Elasticsearch re-index (`reindex_version`_) re-downloads and re-parses the entire corpus.

Proposed: parse on the builder
------------------------------

The builder has every built page on local disk right before upload:
the isolated fleet syncs artifact directories in `_upload_artifacts`_,
and uploaded-zip builds are covered too,
since the isolated worker `downloads and extracts the zip`_ before syncing —
the upload client needs no changes.

After the build, the builder parses each page once —
the same extraction ``index_build`` runs server-side today —
and uploads two extra artifacts next to the HTML,
using the per-build scoped S3 credentials it already holds
(the `STS policy`_ is built from ``Version.get_storage_paths()`` and spans every media type):

- ``diff/<project>/<version>/manifest.json`` — the file tree diff manifest:
  one entry per page with its content hashes, exactly what ``FileManifestIndexer`` writes today.
- The compressed search payload — one file per version (JSONL, one line per page)
  holding the parser's ``processed_json`` output: path, title, sections, and the content hashes.
  That is everything Elasticsearch indexing consumes,
  so the server never re-downloads or re-parses the pages.
  Exact media type and filename are open; the scoped credentials cover every option.

Builders never talk to Elasticsearch or the database —
they hold only a per-build, project-scoped API key and those storage credentials.
At build success, a small server-side task downloads the one payload file and does the rest:
bulk-indexes internal versions into Elasticsearch through the existing chunked `index_objects`_ path,
creates the index/404 records from the payload's file list,
snapshots the base manifest for pull request diffs,
and posts the pull request overview comment.
The CDN purge signals (``files_changed``, ``search_index_updated``)
are already in place after `#13276`_.

What changes
------------

- **S3 reads per build.** Today: one GET per HTML page. Proposed: one GET total, for the payload.
- **Files changed and the pull request comment.** Today: after the reindex queue drains.
  Proposed: seconds after build finish.
- **Fresh search results.** Today: after the reindex queue drains. Proposed: seconds after build finish.
- **Where the parse runs.** Today: web-side reindex workers. Proposed: the builder that made the files.
- **Pull request builds with the features off.** Today: full download-and-parse anyway.
  Proposed: no parse, no manifest.
- **Full Elasticsearch re-index.** Today: re-download and re-parse the corpus.
  Proposed: replay stored payloads.
- **What the reindex queue carries.** Today: all post-build work plus bulk jobs. Proposed: bulk jobs only.
- **Docs pages on the CDN.** Live at build finish since `#13276`_; unchanged by this proposal.

Changing the parser
-------------------

A parser change ships in the builder image and rolls forward:
it reaches each version on its next build, and nothing re-parses what is already built
(`discussion on #13246`_ — maintaining the parser server-side as well,
just to re-extract old builds, is the duplication both reviewers flagged).
A version that never rebuilds isn't changing its pages either,
so its stored extraction stays an accurate index of them;
it only misses extraction improvements until it builds again.
Payload replay re-indexes stored extractions verbatim,
so a full Elasticsearch re-index doesn't propagate a parser change either.

The payload carries a small metadata header — build id, created date,
and three version fields with different bump disciplines:

- **Schema version** — the payload file format itself.
  This is what gates ingest: the tolerant reader accepts known majors,
  ignores unknown fields, and refuses what it can't parse.
- **Parser version** — which extractor produced the content.
  It never gates search ingest,
  since extractions from different parser versions coexist harmlessly in Elasticsearch;
  with roll-forward it is pure observability:
  how much of the corpus each extractor produced,
  and whether an old extraction explains a search oddity.
- **Hasher version** — bumped only when a change alters what the file tree diff hashes mean;
  ``get_diff`` treats a mismatch as "outdated."
  Roll-forward is what makes this field earn its place:
  after a bump, a pull request built with the new parser
  diffs against a base version that may not have rebuilt yet,
  and the mismatch marks that diff "outdated" instead of reporting every file as modified;
  it heals on the base version's next build.
  Keeping this separate from the parser version matters:
  if every parser release bumped it, every release would invalidate every open pull request's diff.

A parser change paired with an Elasticsearch mapping change spans both repositories:
the readthedocs.org side (mapping plus tolerant ingest) deploys first, the builder second —
the same reader-first ordering as the main rollout.
Golden HTML fixtures with expected hashes, committed to both repositories,
catch accidental hash drift in CI.

Other risks and open questions
------------------------------

- **Payloads are derived from user content on build machines.**
  The ingest task re-enforces the parser's caps (section count, content size)
  before writing to Elasticsearch.
- **Payload size on the largest projects.**
  Compressed JSONL should stay well under the HTML itself,
  but confirm bounds before making it the re-index source.

Rollout
-------

#. Already merged: `#13276`_ purges the docs CDN at build success (``purge_docs_cdn``)
   and adds the ``search_index_updated`` signal,
   so cached search results can be purged by the ``rtd-search`` cache tag once indexing lands.
#. Quick relief, independent of the rest:
   route external versions' ``index_build`` to the ``web`` queue
   (they skip search indexing already),
   and skip the manifest indexer when a project has neither file tree diff
   nor build overview comments enabled.
#. readthedocs.org, deploys first:
   skip server-side generation when a manifest for the current build already exists;
   treat a hasher version mismatch in ``get_diff`` as "outdated";
   move the base-manifest snapshot and pull request comment to a build-success task.
#. readthedocs-builder: port the parser
   (`readthedocs/search/parsers.py`_, 512 lines today, plus golden-fixture tests)
   and emit the manifest and payload from `_upload_artifacts`_.
   Covers isolated and uploaded builds in one place.
#. Search payload ingest task;
   then payload replay becomes the path for full Elasticsearch re-indexes.

The legacy fleet stays on today's path and ages out with the isolated-builds migration —
no throwaway code written for it.
The server-side parse path is equally transitional:
it keeps covering builds that ship no payload
(legacy-fleet builds, and versions whose last build predates the rollout),
and once a one-time pass stores payloads for that long tail,
the parser code is deleted from readthedocs.org and lives only on the builder —
resolving the `discussion on #13246`_ about not keeping it in two codebases.

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

Two of the three original constraints have since reversed:
built files are now local to the builders rather than the webs,
and builders hold per-build scoped storage credentials.
The one that stands — builders run untrusted code
and never hold DB or Elasticsearch credentials — is the one this proposal keeps.

.. _#13276: https://github.com/readthedocs/readthedocs.org/pull/13276
.. _discussion on #13246: https://github.com/readthedocs/readthedocs.org/pull/13246#issuecomment-5933896429
.. _#10623: https://github.com/readthedocs/readthedocs.org/issues/10623
.. _#5854: https://github.com/readthedocs/readthedocs.org/pull/5854
.. _#7161: https://github.com/readthedocs/readthedocs.org/pull/7161
.. _#7204: https://github.com/readthedocs/readthedocs.org/pull/7204
.. _#7208: https://github.com/readthedocs/readthedocs.org/pull/7208
.. _#8815: https://github.com/readthedocs/readthedocs.org/pull/8815
.. _#10378: https://github.com/readthedocs/readthedocs.org/pull/10378
.. _#10696: https://github.com/readthedocs/readthedocs.org/pull/10696
.. _#11646: https://github.com/readthedocs/readthedocs.org/pull/11646
.. _index_build: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/projects/tasks/search.py#L319
.. _`_process_files`: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/projects/tasks/search.py#L255
.. _GenericParser.parse: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/search/parsers.py#L444
.. _opens every file from storage: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/search/parsers.py#L76
.. _search_index_updated: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/projects/tasks/search.py#L111
.. _search indexing skips external versions: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/projects/tasks/search.py#L214
.. _manifest gate: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/projects/tasks/search.py#L236
.. _at serve time: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/proxito/views/hosting.py#L650
.. _reindex_version: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/projects/tasks/search.py#L352
.. _`_upload_artifacts`: https://github.com/readthedocs/readthedocs-builder/blob/4574e1d/builder/builder/runner.py#L446
.. _downloads and extracts the zip: https://github.com/readthedocs/readthedocs-builder/blob/4574e1d/builder/builder/director.py#L969
.. _STS policy: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/aws/security_token_service.py#L147
.. _index_objects: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/search/utils.py
.. _readthedocs/search/parsers.py: https://github.com/readthedocs/readthedocs.org/blob/01a4d8ecafd751b913b922ab69b08c979f666626/readthedocs/search/parsers.py
