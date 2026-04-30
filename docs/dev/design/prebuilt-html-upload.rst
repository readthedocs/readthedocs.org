Pre-built HTML upload
=====================

Goal
----

Let users host HTML they built outside of Read the Docs while keeping every
hosting feature: dashboard, builds list, build commands, notifications,
addons, search, redirects, custom domains and the existing APIv3.

Renaming, marketing names and "rename ``latest``" are explicitly **out of
scope**: the existing :py:class:`~readthedocs.builds.forms.VersionForm`
already lets users edit the slug of any non-machine version.

Shape of the change
-------------------

A new :py:attr:`Version.source_type` field selects how the builder fetches
the version's source:

``vcs`` (default)
    Clone the project repository and run the configured build tool. This is
    the existing behavior for every existing row.

``upload``
    Skip the clone and unzip an archive that the user uploaded via the API.

Versions with ``source_type=upload`` are excluded from VCS sync delete and
from webhook ref resolution. Everything else — Build objects, state machine,
artifact upload, notifications, APIv3 — is reused as-is.

Data model
----------

In ``readthedocs/builds/models.py``::

    source_type = CharField(choices=SOURCE_TYPES, default="vcs")
    upload_content_hash = CharField(max_length=64, null=True, blank=True)

The hash is the SHA256 of the most recent uploaded archive. It doubles as the
storage key segment so two uploads with identical content reuse the same
object and so the builder always knows which object to fetch.

Migration: ``builds/migrations/0072_version_source_type_upload_content_hash.py``,
``Safe.before_deploy()`` (additive, nullable, default).

Storage layout
--------------

Archives live on ``build_media_storage`` at::

    uploads/<project_slug>/<version_slug>/<sha256>.zip

The builder reads the same key. Old objects are overwritten on re-upload of
identical content; older distinct archives are left in place for now (see
*Open issues*).

Validation contract (``projects/tasks/uploads.validate_archive``)
-----------------------------------------------------------------

Performed on the web side **before** anything is persisted:

* Archive size ≤ 1 GiB compressed; uncompressed ≤ 5 GiB; ratio ≤ 200×.
* ≤ 50 000 entries.
* No absolute paths, no ``..`` traversal, no symlinks.
* Top-level entries must be a subset of ``{html, htmlzip, pdf, epub}``.
* ``html/`` is required.

All limits are constants in ``uploads.py`` so they can be lifted to settings
later.

API
---

``POST /api/v3/projects/<project>/versions/<version>/upload/``
    ``multipart/form-data`` with a single ``file`` field containing the zip.
    Validates the archive, stores it, sets ``upload_content_hash``, and
    triggers a build via the existing ``trigger_build``. Returns the same
    envelope the build-trigger endpoint uses, plus ``upload.{sha256, size,
    top_level_dirs}``.

``source_type`` is exposed read-only on the version serializer; creating an
``upload`` version is a separate concern handled by the existing version
admin / management surface and is **not** part of this change.

Build pipeline
--------------

In ``UpdateDocsTask.execute()``::

    if self.data.version.is_upload:
        self.execute_upload()
        return

``execute_upload`` short-circuits the VCS+Docker pipeline:

1. ``BUILD_STATE_CLONING`` — wipe and recreate
   ``project.artifact_path("html").parent`` (the ``_readthedocs/`` dir).
2. ``BUILD_STATE_BUILDING`` — download the archive from
   ``build_media_storage`` and unzip into that directory.
3. ``BUILD_STATE_UPLOADING`` — call the existing
   ``store_build_artifacts()`` which already handles per-format validation,
   renaming and rclone-sync to permanent storage.

No Docker, no language env, no build tool — there is nothing to run.

Sync & webhook routing
----------------------

* ``api/v2/utils.py:_get_deleted_versions_qs`` excludes
  ``source_type=upload`` from the delete candidate queryset, so a future VCS
  sync won't drop manually-created upload versions.
* ``projects/models.py:Project.versions_from_name`` excludes
  ``source_type=upload``, so a push event whose ref name happens to collide
  with an upload version's ``verbose_name`` does not trigger an upload
  rebuild.

Reuse summary
-------------

What we **don't** add: a parallel build path, a new Build model, separate
Celery queues, separate concurrency tracking, separate notifications,
separate APIv3 build endpoints. All of that comes for free from reusing
``Build`` and ``store_build_artifacts``.

What we **do** add: one field, one migration, one helper module
(``projects/tasks/uploads.py``), one task method (``execute_upload``), one
DRF action (``VersionsViewSet.upload``).

Tests
-----

* ``projects/tests/test_uploads.py`` — zip validation: minimal, all formats,
  missing html, unknown top-level dir, traversal, absolute path, empty,
  non-zip, plus ``get_upload_storage_path``.
* ``api/v3/tests/test_uploads.py`` — endpoint: trigger flow with mocked
  ``store_uploaded_archive`` and ``trigger_build``; rejects non-upload
  versions, rejects invalid archives, requires auth, forbids other users.
* ``rtd_tests/tests/test_sync_versions.py`` — upload versions survive sync;
  upload versions excluded from webhook routing.

GitHub Actions
--------------

``docs/user/examples/github-actions-upload.yml`` shows the end-to-end CI
flow: build with ``sphinx-build``, assemble the ``html/`` (and optional
``epub/``, ``pdf/``, ``htmlzip/``) directories into a zip, ``curl`` to the
upload endpoint with a token from secrets.

Open issues / follow-ups
------------------------

* **Retention.** The current code does *not* delete older archives at the
  same prefix when content changes. Add a small task that keeps the last N
  (configurable) per version once we have a number we like.
* **In-flight build vs. new upload.** A second upload while a build is
  running just queues another build with the new hash; the first finishes
  with the old artifacts and is then overwritten. This matches webhook
  behavior and is probably fine, but worth confirming.
* **Plan gating.** On readthedocs.com the upload feature should likely be
  gated by feature flag / plan tier. Not wired up here.
* **Creating upload versions.** Adding a CreateModelMixin to
  ``VersionsViewSet`` (so users can create the upload version itself via
  API) is a small follow-up. For now creation is via dashboard / admin.
* **Legacy ``Version.uploaded`` field.** Left untouched; the new exclusion
  in ``_get_deleted_versions_qs`` is additive (``.exclude(uploaded=True)``
  is preserved alongside ``.exclude(source_type=SOURCE_TYPE_UPLOAD)``).
  Drop ``uploaded`` in a later release once we are sure nothing else reads
  it.
