Pre-built HTML upload
=====================

Goal
----

Let users host HTML they built outside Read the Docs while keeping every
hosting feature: dashboard, builds, build commands, notifications, addons,
search, redirects, custom domains, APIv3.

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

Upload-type versions are excluded from VCS sync delete and webhook ref
resolution. Same :py:class:`Build` rows, state machine, Celery queues,
APIv3 — all reused.

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
* Silently tolerated: ``__MACOSX/`` resource forks, dotfiles
  (``.DS_Store`` etc.), backslash separators, directory marker entries.

Limits live as constants in ``uploads.py`` for now; promote to settings
once we have a number we like.

API
---

``POST /api/v3/projects/<p>/versions/<v>/upload/`` —
``multipart/form-data`` with a single ``file`` field. Validates, stores,
sets ``upload_content_hash``, triggers a build via the existing
``trigger_build``. Response mirrors the build-trigger envelope plus
``upload.{sha256, size, top_level_dirs}``.

Both ``source_type`` and ``upload_content_hash`` are exposed on the
APIv2 ``VersionSerializer`` — without this the builder reads them as
defaults and silently takes the VCS path.

Build pipeline
--------------

In ``UpdateDocsTask.execute()``::

    if self.data.version.is_upload:
        self.execute_upload()
        return

``execute_upload`` does:

1. ``CLONING`` — wipe and recreate the build's ``_readthedocs/`` dir.
2. ``BUILDING`` — stage the SHA-keyed archive to a tempfile (so
   ``zipfile`` is seekable on any storage backend) and unzip it.
3. ``UPLOADING`` — call the existing ``store_build_artifacts()``, which
   already handles per-format validation, single-file rename, and
   rclone-sync to permanent storage.

A missing archive at extract time raises
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
  symlink, empty, non-zip, ``__MACOSX``, dotfiles, backslashes,
  directory entries, traversal-in-junk.
* ``api/v3/tests/test_uploads.py`` — endpoint: trigger, non-upload
  reject, invalid-archive reject, auth, cross-user.
* ``rtd_tests/tests/test_sync_versions.py`` — upload versions survive
  sync; not matched by webhook routing.

Open issues
-----------

* **Retention.** Older archives at the same prefix are not cleaned up.
  Add a per-version "keep last N" task.
* **Creating upload versions.** Currently admin/shell only. Add to
  ``VersionsViewSet`` (``CreateModelMixin``) and ``VersionForm`` once
  the surface is settled.
* **Plan gating** on .com.
* **In-flight build vs. new upload.** Second upload while a build is
  running just queues another build with the new hash; the first
  finishes with the new artifacts. Matches webhook behavior; fine.
* **Legacy ``Version.uploaded``.** Left untouched; new
  ``source_type=upload`` exclusion is additive. Drop in a later release.
* **Infra.** Remember to bump nginx ``client_max_body_size`` to match
  ``MAX_UPLOAD_SIZE_BYTES`` when this ships.
