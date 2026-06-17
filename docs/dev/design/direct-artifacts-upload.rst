Build anywhere, host with the best
==================================

Goals
-----

- Build the documentation anywhere, and upload the artifacts to Read the Docs.
  Zip it, ship it, host it.
- Integrate with existing modeling as much as possible.
- Easy to transition/test from our current build system for existing projects.

Non-goals
---------

- Complete re-design of the build/version system/modeling.
- Deprecate our current build system for existing projects.
  We want to support both for a while, and let users transition at their own pace.

Motivation
----------

- Most requested feature since ever.
- Security: we would no longer run arbitrary code on our servers.
- Performance: some projects have very long build times, our builders are slow compared to other CI services.
- Flexibility: we aren't as flexible as other CI services. We aren't a CI service.
- Easy to integrate: users already build their docs in their CI, no need to replicate that on our side.
- Best of both worlds: users can build their docs anywhere as they want, but still get the benefits of hosting on Read the Docs.

Proposed architecture
---------------------

This is a high level overview of the proposed architecture for the new build system.
The details about each phase of the process are explained in the following sections.

- Users build their documentation artifacts (HTML, PDF, ePub, etc.) in their CI or locally.
- Users call a script or GH action to upload the artifacts to Read the Docs.
  - A token is previously generated on Read the Docs and provided to the user to interact with the upload API (internal API).
  - Some pre-checks can be done on the client side before uploading, like checking the size of the artifacts, validating the metadata, etc.
    This is only to avoid unnecessary uploads and provide faster feedback to users.
    All the checks will be also done on the server side.
  - All artifacts are zipped into a single file.
  - A post request is made to the upload API with some metadata like Git branch/tag, commit hash, configuration, etc.
  - A build object is created in Read the Docs with the status "pending" and a signed URL is returned to the user to upload the artifacts.
  - The zip file is uploaded to the signed URL.
  - A post request is made to the upload API to notify that the upload is complete and the build can be processed.
- Read the Docs triggers a task to process the build.
  - A docker container is created to process the build (like our current builders do).
  - The zip file is downloaded from the signed URL.
  - The artifacts are extracted and validated.
  - The artifacts are uploaded to their final destination and pre-processed for indexing (same process as our current builders).
  - The build status is updated to "success" or "failure" depending on the result.
- The documentation is available to be served to users.

Versions
--------

Versions are created when the upload is initiated and linked to a Git branch/tag/commit, just like our current versions.
We don't enforce that the branch/tag/commit exists in the Git repository, we just assume it does.
This is useful to keep the same modeling for versions, and most of the UI the same.
If the version for that Git branch/tag/commit already exists, it will be reused for the new build.

Versions will have a new field to indicate the source of their latest build (build_source), either "rtd-build" or "external-upload".
This will allow us to do some checks and validations.

Versions marked as active and where their latest build is from an external upload can't be built using our current build system.
This is to avoid overwriting the documentation built from an external upload with a build from our current build system.
This should mainly happen while users migrate to the new system, new users should only use the new upload system.

We will no longer update the version to keep in sync with the Git branch/tag/commit,
this will be updated after the upload is complete and the build is processed for that version.

.. note::

   It's kind weird that we keep active/built versions in sync with the Git branch/tag/commit.
   Active versions should reflect the state from where the documentation was built.

Versions that are deleted from the Git repository will be deleted from Read the Docs if an automation rule is configured to do so.
This includes versions created from external uploads, as they are still linked to a Git branch/tag/commit.

.. note::

   With this new system, we don't have the need to keep a copy of the Git repository versions in Read the Docs.
   We can discuss in the future how we want to handle that.

Builds
------

Builds will have a new field to indicate the source of the build (build_source), either "rtd-build" or "external-upload".
This will allow us to differentiate between builds that were triggered by our current build system and builds that were triggered by the new upload system.

Latest build wins, previous build is cancelled. Just like our current build system.

Statuses:

- A build is created when the upload is initiated, with the state "uploading".
  The "triggered"/"building" state could be re-used.
- When the upload is complete, the state is "uploaded" (can also be "in queue" or "ready to process").
  The "triggered"/"building" state could be re-used for this.
- When the build is being processed, the state is "processing".
  The "building" state could be re-used for this.
- When the assets are validated and uploaded to their final destination, the state is "finished".
- The success attribute is updated to "true" or "false" depending on the result of the processing.
- If the build is cancelled, the state is "cancelled".
  Builds are cancelled when a new build is triggered for the same version,
  or when the user cancels the build manually.
  Just like our current build system,

Aliases: latest/stable
----------------------

TBD

Webhooks and status API
-----------------------

Webhook events:

- Build triggered: we can emit this one when the upload is initiated,
  or replace it with "uploading".
- Build passed: we can emit this one when the build is finished and successful.
  Same as our current "build passed" event.
- Build failed: we can emit this one when the build is finished and failed.
  Same as our current "build failed" event.

Commit status:

No changes needed, we can just update the status as we do now with the three states: pending, success, failure.

Configuration file
------------------

In the case of the GH action, we can use the action inputs to provide the settings,
or fallback to read the configuration file from the repository if it exists.

When the upload is initiated, we can pass the configuration to the API,
which will be stored in the build object and used when processing the build.
We already store the configuration in the build object.

.. note::

   Currently, only the search configuration is relevant for processing the artifacts.
   It can be left out for a future iteration if we want to simplify the initial implementation.

Upload API
----------

The upload API will be a private API, and will require an "upload token" to authenticate the requests.
This token can be generated by users in their project settings.

.. note::

   The user token can be re-used for initial testing.

POST /api/v3/_internal/upload/initiate:
  Initiate the upload process and create a build object with the state "uploading".
  This endpoint will receive some metadata like Git branch/tag/commit, configuration, etc,
  and return build object and the signed URL to upload the artifacts.

  If we don't find a version for the Git branch/tag, we can create a new version for it,
  and attach the build to that version.

  ::
      {
         "ref_name": "main",
         "ref_type": "branch",
         "ref_sha": "abc123",
         # Optional, if not provided, it's derived from the ref_name.
         # If the version with that slug exists, but it points to a different Git ref, we error out.
         "version_slug": "main",
         "configuration": {
            "search": {
            }
         }
      }

POST /api/v3/_internal/upload/complete:
  Notify that the upload is complete and the build can be processed.
  This endpoint will receive the build ID.

  This endpoint will trigger a task similar to our builders.
  This task will start a docker container, download the artifacts, validate them,
  upload them to their final destination, and update the build status,
  send the webhooks, update the commit status, etc.
  Just like our current builders do.

S3
--

All artifacts will be uploaded to S3, and then processed from there.
We'll have a separate bucket for the uploaded artifacts,
with a lifecycle policy to clean up the artifacts after a certain period of time.
See https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-expire-general-considerations.html.

Artifacts will be uploaded as a zip file, in the following format: {project_id}/{build_id}/artifacts.zip.

Upload script / GitHub Action
-----------------------------

TBD

Pull requests
-------------

TBD

From branches from the same repository, that's okay.
From forks, that's more complicated, we don't want to allow random people to upload builds for a project they don't have access to.
But this is kind of already possible...
But how do we share the API key for the upload?
We can make use of the ``pull_request_target`` event, which runs in the context of the base repository, and has access to the secrets of the base repository.
But this event is easy for users to mess up and run malicious code in the context of the base repository.
Maybe we are okay with not supporting PR builds from forks.

Possible issues
---------------

TBD

First iteration
---------------

TBD

Future improvements and ideas
-----------------------------

TBD

References
----------

- https://github.com/readthedocs/readthedocs.org/issues/1083
- https://github.com/readthedocs/readthedocs.org/pull/13011
- https://aws.amazon.com/blogs/storage/automated-extraction-of-compressed-files-on-amazon-s3-using-aws-batch-and-amazon-ecs/
- https://aws.amazon.com/blogs/storage/automatically-decompress-files-in-amazon-s3-using-aws-step-functions/
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
