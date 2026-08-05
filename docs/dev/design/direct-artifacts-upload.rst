Direct artifacts upload
=======================

This document explains the architecture behind `direct artifacts upload`_,
a feature that lets users build their documentation in their own CI system
and upload the resulting artifacts to Read the Docs,
instead of having Read the Docs clone the repository and run the build itself.

The goal of this document is to show how the new code fits into the existing build pipeline:
what is new, what is reused, and where both flows converge.

.. warning::

   This describes the draft implementation from `direct artifacts upload`_,
   and may not match the final implementation.

.. _direct artifacts upload: https://github.com/readthedocs/readthedocs.org/pull/13178

The two pipelines at a glance
-----------------------------

.. code-block:: text

    Built by Read the Docs (existing)         Direct artifacts upload (PR #13178)

    ┌────────────────────────────────┐        ┌────────────────────────────────────────┐
    │ Git provider                   │        │ User's own CI                          │
    │ (GitHub / GitLab / Bitbucket)  │        │ builds docs itself → artifacts.zip     │
    └───────────────┬────────────────┘        └──────────────────┬─────────────────────┘
                    │ push → webhook                             │ ① POST …/upload/initiate/
                    ▼                                            ▼
    ┌────────────────────────────────┐        ┌────────────────────────────────────────┐
    │ Web servers                    │        │ Web servers: UploadInitiateView        │
    │ trigger_build()                │        │ · token auth, admin, feature flag,     │
    │ prepare_build():               │        │   active project, pending-upload limit │
    │ · Build (state=triggered)      │        │ · get or create Version                │
    │ · BuildAPIKey                  │        │ · Build (triggered, is_uploaded=True)  │
    └───────────────┬────────────────┘        │ · presigned S3 POST URL                │
                    │ Celery:                 └──────────────────┬─────────────────────┘
                    │ update_docs_task                           │ ② upload artifacts.zip
                    │                                            ▼
                    │                              (S3 bucket: build-uploads)
                    │                                            │
                    │                                            │ ③ POST …/upload/complete/
                    │                                            ▼
                    │                         ┌────────────────────────────────────────┐
                    │                         │ Web servers: UploadCompleteView        │
                    │                         │ · concurrency check                    │
                    │                         │ · BuildAPIKey                          │
                    │                         └──────────────────┬─────────────────────┘
                    │                                            │ Celery:
                    ▼                                            │ process_uploaded_build
    ┌────────────────────────────────┐                           ▼
    │ Builder                        │        ┌────────────────────────────────────────┐
    │ · clone the repository         │        │ Builder                                │
    │ · install tools + deps         │        │ · download artifacts.zip               │
    │ · run Sphinx / MkDocs          │        │   (read-only scoped credentials)       │
    │   (inside Docker)              │        │ · unzip inside Docker                  │
    │ → _readthedocs/<format>/       │        │ · validate _readthedocs/ layout        │
    └───────────────┬────────────────┘        └──────────────────┬─────────────────────┘
                    │ rclone sync                                │ rclone sync
                    ▼                                            ▼
    ┌──────────────────────────────────────────────────────────────────────────────────┐
    │ build-media storage (S3) — canonical build artifacts, shared by both pipelines   │
    └─────────────────────────────────────────┬────────────────────────────────────────┘
                                              │
                     same post-build tasks for both pipelines:
              search indexing (Elasticsearch) · build notifications
              (webhooks / email) · commit status sent to the Git provider
                                              │
                                              ▼
    ┌──────────────────────────────────────────────────────────────────────────────────┐
    │ El Proxito serves the documentation to readers                                   │
    └──────────────────────────────────────────────────────────────────────────────────┘

The important architectural property is that **only the way artifacts are produced changes**.
In the existing pipeline, our builders clone the repository, install dependencies,
and run the documentation tool.
In the new pipeline, the user produces the artifacts on their own infrastructure,
and our builders only validate and ingest them.
Both pipelines write to the same ``build-media`` storage using the same code path,
so everything downstream of it is shared and unchanged:
serving through El Proxito, search indexing, notifications, and commit statuses.

The upload API
--------------

The new ``readthedocs.upload`` app exposes two endpoints under ``/api/v3/upload/``,
authenticated with the user's API token
(not to be confused with the per-build ``BuildAPIKey`` used by builders).
Uploading is a three-step handshake:

.. code-block:: text

    User's CI                          Web servers                        S3: build-uploads
        │                                   │                                   │
        │ ① POST /api/v3/upload/initiate/   │                                   │
        │   {project, version {name, type,  │                                   │
        │    commit, privacy_level}}        │                                   │
        │──────────────────────────────────►│                                   │
        │                                   │ token auth + project admin check  │
        │                                   │ feature flag + active project     │
        │                                   │ pending-uploads limit             │
        │                                   │ get or create Version             │
        │                                   │ create Build (state=triggered,    │
        │                                   │   is_uploaded=True)               │
        │                                   │ cancel other running builds       │
        │                                   │ pending commit status → Git       │
        │◄──────────────────────────────────│                                   │
        │ 201 {build, version,              │                                   │
        │      upload_url {url, fields}}    │                                   │
        │                                   │                                   │
        │ ② POST artifacts.zip using the presigned URL and fields               │
        │   (zip only, ≤ 1 GB, URL expires in 30 minutes)                       │
        │──────────────────────────────────────────────────────────────────────►│
        │                                   │                                   │
        │ ③ POST /api/v3/upload/complete/   │                                   │
        │   {build, status success|failed}  │                                   │
        │──────────────────────────────────►│                                   │
        │                                   │ failed → finish build as errored  │
        │                                   │ success → concurrency check,      │
        │                                   │   create BuildAPIKey, queue       │
        │                                   │   process_uploaded_build          │
        │◄──────────────────────────────────│                                   │
        │ 202 Accepted                      │                                   │

The upload itself goes directly to S3 using a presigned POST URL,
so the (potentially large) zip file never passes through our web servers.

The feature is gated by the ``ALLOW_DIRECT_ARTIFACTS_UPLOAD`` feature flag on the project,
and limited to ``RTD_UPLOAD_MAX_PENDING_UPLOADS`` builds waiting for an upload,
so a misbehaving client can't create unlimited pending builds.

The zip file must contain the same layout the regular build process produces
in the ``_readthedocs/`` output directory:
an ``html/`` directory (required),
and optionally ``pdf/``, ``epub/``, and ``htmlzip/`` directories
containing exactly one file each.
The repository includes ``upload.sh``, an example client for the whole flow.

Processing uploaded artifacts on the builders
---------------------------------------------

``ProcessUploadedBuildTask`` (``readthedocs/upload/tasks.py``) is a sibling of
``UpdateDocsTask`` (``readthedocs/projects/tasks/builds.py``), the task that runs regular builds.
It reuses the same infrastructure:
it runs on the builders,
communicates all state through API v2 using a per-build ``BuildAPIKey``
(revoked when the task finishes),
uses ``acks_late``, scale-in protection, ``clean_build()``,
and the same ``on_failure`` / ``on_retry`` / ``after_return`` handlers,
including retries, soft time limits, and builder instance termination.

Because it drives the same ``Build`` model through the same states,
an uploaded build renders in the dashboard like any other build.
The task creates synthetic build commands
("Downloading artifacts from storage", "Extracting artifacts", and so on)
so the build detail page shows a familiar timeline.
The states map to different work in each task:

.. list-table::
   :header-rows: 1

   * - Build state
     - ``update_docs_task`` (existing)
     - ``process_uploaded_build`` (new)
   * - Triggered
     - Waiting in the Celery queue.
     - Waiting for the user to upload, then for the Celery queue.
   * - Cloning
     - Clone the user's repository.
     - Download ``artifacts.zip`` from ``build-uploads`` storage.
   * - Installing
     - Install build tools and dependencies.
     - Skipped, there is nothing to install.
   * - Building
     - Run Sphinx / MkDocs / build commands inside Docker.
     - Unzip inside Docker and validate the artifacts layout.
   * - Uploading
     - Sync ``_readthedocs/<format>/`` to ``build-media`` with rclone.
     - Same code path.
   * - Finished
     - Search indexing, notifications, commit status, spam check.
     - Same tasks.

Storage and credentials
-----------------------

The feature adds a third storage bucket, ``build-uploads``,
next to the existing ``build-media`` (final artifacts) and ``build-tools`` (cached tools).
It is a staging area only:
uploaded zips live under ``<project_id>/<build_id>/artifacts.zip``
and are never served to readers.

.. code-block:: text

                 ① write: presigned POST                  ② read: STS-scoped credentials
                   zip only, single key, ≤ 1 GB,             read-only, single key, via the
                   URL expires in 30 minutes                 API v2 credentials endpoint
    User's CI ─────────────────────────► build-uploads ─────────────────────────► Builder
                                         <project>/<build>/artifacts.zip             │
                                                                        ③ rclone     │
                                                                          sync       ▼
    Readers ◄──────── El Proxito ◄────── build-media ◄───────────────────────────────┘
                                         html / pdf / epub / htmlzip

Neither side of the transfer holds real AWS credentials:

* The client uploads with a **presigned POST** generated by the web servers
  (``RTDS3Storage.generate_presigned_post()``),
  valid only for the exact object key, only for ``application/zip`` content,
  capped at 1 GB, and expiring after 30 minutes.
* The builder downloads with **temporary STS credentials**
  requested through the existing API v2 endpoint
  (``/api/v2/build/<id>/credentials/storage/`` with type ``build_uploads``),
  scoped by an inline policy to read-only access on that build's single key.
  This is the same mechanism regular builds already use
  for ``build-media`` and ``build-tools`` access.

The contents of the zip file can't be trusted,
so it is extracted inside a Docker container,
reusing ``DockerBuildEnvironment`` just like regular build commands.

Data model changes
------------------

Two new boolean flags mark uploaded content:

* ``Build.is_uploaded``: set at creation time by the initiate endpoint.
* ``Version.is_uploaded``: set by a ``post_save`` signal
  when an uploaded build for the version finishes successfully.

Once a version is marked as uploaded, the two pipelines become mutually exclusive for it:

.. code-block:: text

    build created by the upload API finishes successfully
         │
         │ post_save signal on Build
         ▼
    Version.is_uploaded = True
         │
         ├──► prepare_build() refuses new builds for this version
         │    (webhooks and the dashboard can no longer trigger builds for it)
         │
         └──► POST /api/v3/projects/<slug>/versions/<slug>/builds/ returns 400
              ("Cannot trigger a build for an uploaded version")

This prevents a Git-triggered build and an uploaded build
from fighting over the same version's artifacts.

What stays the same
-------------------

Everything not listed above is untouched, notably:

* The ``Build`` and ``Version`` models, dashboard, and build detail pages.
* The build state machine and concurrency limits
  (uploaded builds count against the same per-project limit).
* The security model for builders:
  per-build API keys and STS-scoped storage credentials.
* The ``build-media`` storage layout, and with it El Proxito,
  which serves uploaded documentation exactly as it serves built documentation.
* Post-build behavior: search indexing, build notifications and webhooks,
  commit statuses reported to the Git provider,
  spam checks, and disabling projects after consecutive failures.
