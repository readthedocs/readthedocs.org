Pre-built docs upload
=====================

Goal
----

Let users host documentation they built outside Read the Docs while
keeping every hosting feature: dashboard, builds, build commands,
notifications, addons, search, redirects, custom domains, APIv3.

The feature is named "pre-built HTML" colloquially but the archive may
contain any of the formats Read the Docs supports — ``html/`` is
required, ``htmlzip/``, ``pdf/`` and ``epub/`` are optional.

Renaming and "rename ``latest``" are out of scope: the existing
:py:class:`~readthedocs.builds.forms.VersionForm` already lets users edit
the slug of any non-machine version.

Shape
-----

One new field, :py:attr:`Version.source_type`, selects how the builder
fetches source:

``vcs`` (default)
    Clone the repository and run the configured build tool. Existing
    behavior, unchanged for every existing row.

``upload``
    Skip the clone and unzip an archive uploaded via APIv3.

Upload-type versions are excluded from VCS sync delete and from webhook
ref resolution (i.e. when a ``git push`` arrives, the lookup that maps
the branch/tag to a ``Version`` skips upload rows so a push can never
accidentally trigger an upload rebuild).

Same :py:class:`Build` rows, state machine, Celery queues, APIv3 — all
reused.

Data model
----------

In ``readthedocs/builds/models.py``::

    source_type = CharField(choices=SOURCE_TYPES, default="vcs")
    upload_content_hash = CharField(max_length=64, null=True, blank=True)

The hash is the SHA256 of the latest archive. It also forms the storage
key, making same-content uploads idempotent and the builder fetch
deterministic.

Migration ``builds/migrations/0072_*.py`` is ``Safe.before_deploy()``:
additive, nullable, default-valued.

Storage layout
--------------

``build_media_storage``::

    uploads/<project_slug>/<version_slug>/<sha256>.zip

Validation contract
-------------------

Run on the web side **before** anything is persisted
(``projects/tasks/uploads.validate_archive``):

* ≤ 1 GiB compressed, ≤ 5 GiB uncompressed, ratio ≤ 200×, ≤ 50 000 files.
* No absolute paths, no ``..``, no symlinks. Safety check runs *before*
  the junk-file filter so traversal hidden in ignored paths
  (``__MACOSX/../etc/passwd``) still rejects.
* Top-level entries ⊆ ``{html, htmlzip, pdf, epub}``. ``html/`` is
  required and must contain ``index.html``.
* Silently tolerated: ``__MACOSX/`` resource forks, hidden
  ``.DS_Store``-style files, backslash separators, directory marker
  entries.
* Error messages never echo entries from the archive — the archive is
  user-supplied input we should not reflect back into our own logs or
  responses.

Limits live as constants in ``uploads.py`` for now; promote to settings
once we have a number we like.

API
---

``POST /api/v3/projects/<p>/versions/<v>/upload/`` —
``multipart/form-data`` with a single ``file`` field. Validates, stores,
sets ``upload_content_hash``, triggers a build via the existing
``trigger_build``. Response mirrors the build-trigger envelope plus
``upload.{sha256, size, top_level_dirs}``.

The endpoint **does not create the version row**. The version must
already exist with ``source_type=upload``. Today that means we
(maintainers) create it via Django admin or shell; a ``CreateModelMixin``
on ``VersionsViewSet`` is in *Open issues*.

Both ``source_type`` and ``upload_content_hash`` are exposed on the
APIv2 ``VersionSerializer`` — without this the builder reads them as
defaults and silently takes the VCS path. APIv2 is otherwise on the way
out, but the builder is its only consumer for this data.

Build pipeline
--------------

In ``UpdateDocsTask.execute()``::

    if self.data.version.is_upload:
        self.execute_upload()
        return

``execute_upload`` does:

1. Stage the archive on the host at
   ``project.checkout_path(version)/upload.zip``. That path is
   bind-mounted into the build container.
2. Spin up the build container via the existing
   ``BuildDirector.create_build_environment()``.
3. Inside the container: ``mkdir -p _readthedocs/`` then ``unzip -q -o
   upload.zip -d _readthedocs/ -x __MACOSX/* */.DS_Store .DS_Store``.
   The host never executes ``unzip`` on user input.
4. Call the existing ``store_build_artifacts()`` (host-side; copies the
   mounted output to permanent storage). It also runs the existing
   ``BUILD_OUTPUT_*`` validations — ``html/index.html`` exists,
   single-file PDF/EPUB/HTMLZIP, etc. — exactly like a normal build.

The build state machine reuses ``CLONING`` and ``BUILDING`` for now;
adding upload-specific states (e.g. ``STAGING``, ``EXTRACTING``) is a
small follow-up once we like the shape.

A missing archive at stage time raises
``MissingUploadedArchiveError`` → ``BuildUserError`` so the dashboard
shows a real notification.

Sync & webhooks
---------------

* ``api/v2/utils.py:_get_deleted_versions_qs`` excludes
  ``source_type=upload``.
* ``projects/models.py:Project.versions_from_name`` excludes
  ``source_type=upload`` so a push whose ref name collides with an
  upload version's ``verbose_name`` doesn't trigger an upload rebuild.

What we don't add
-----------------

A parallel build path, a new Build model, separate Celery queues,
separate concurrency tracking, separate notifications, separate APIv3
build endpoints. All free from reusing ``Build`` and
``store_build_artifacts``.

Tests
-----

* ``projects/tests/test_uploads.py`` — validator: minimal, all formats,
  missing html, no index, root-file hint, traversal, absolute path,
  symlink, empty, non-zip, ``__MACOSX``, hidden files, backslashes,
  directory entries, traversal-in-junk, "errors don't echo user names".
* ``api/v3/tests/test_uploads.py`` — endpoint: trigger, non-upload
  reject, invalid-archive reject, auth, cross-user.
* ``rtd_tests/tests/test_sync_versions.py`` — upload versions survive
  sync; not matched by webhook routing.

Open issues
-----------

* **Retention.** Older archives at the same prefix are not cleaned up.
  Add a per-version "keep last N" task.
* **Creating upload versions.** Today: maintainer-only via admin/shell.
  Add ``CreateModelMixin`` to ``VersionsViewSet`` and a ``source_type``
  field to ``VersionForm`` once the surface is settled.
* **Plan gating.** On .com the upload feature should be gated by
  feature flag / plan tier (e.g. paid plans only) before rollout.
  Implementation TBD; not wired today.
* **Upload reliability for big files.** A 1 GiB ``POST`` over the open
  internet is not a great UX (slow, no resume, easy to retry-storm).
  Worth investigating S3 presigned-PUT or chunked/resumable uploads
  before we recommend the cap actually be 1 GiB.
* **DDoS surface.** The upload endpoint accepts large bodies and
  triggers a Celery build per request. Needs per-user throttling
  (DRF ``UserRateThrottle`` is on the view — confirm the rate is
  appropriate for this action) and probably a per-project quota.
* **Build states.** Reusing ``CLONING``/``BUILDING`` is a stop-gap;
  add ``STAGING``/``EXTRACTING`` (or rename) so the dashboard reads
  cleanly for upload builds.
* **Legacy ``Version.uploaded``.** Left untouched; new
  ``source_type=upload`` exclusion is additive. Drop in a later release.
* **Infra.** Bump the upload-endpoint body size limit (nginx
  ``client_max_body_size`` etc.) to match ``MAX_UPLOAD_SIZE_BYTES``
  **only on the upload URL** — leave the global limit as-is so other
  endpoints don't accept 1 GiB requests.
