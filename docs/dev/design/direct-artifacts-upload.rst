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
This should mainly happen while users migrate to the new system.

We will no longer update the version to keep in sync with the Git branch/tag/commit,
this will be updated after the upload is complete and the build is processed for that version.

.. note::

   It's kind weird that we keep active/built versions in sync with the Git branch/tag/commit.
   Active versions should reflect the state from where the documentation was built.

Versions that are deleted from the Git repository will be deleted from Read the Docs if an automation rule is configured to do so.
This includes versions created from external uploads, as they are still linked to a Git branch/tag/commit.

Builds
------

TBD

Builds will have a new field to indicate the source of the build (build_source), either "rtd-build" or "external-upload".
This will allow us to differentiate between builds that were triggered by our current build system and builds that were triggered by the new upload system.

Latest build wins, previous build is cancelled. Just like our current build system.

New build statuses?

Aliases: latest/stable
----------------------

TBD

Webhooks and status API
-----------------------

TBD

Configuration file
------------------

TBD

Upload API
----------

TBD

S3
--

TBD

- Have a bucket for uploaded builds
- Clean up artifacts after they are processed and uploaded to their final destination.
- Set expiration time for the uploaded artifacts (12 hours? 24 hours?)

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
