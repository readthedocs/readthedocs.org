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

Webhooks and status API
-----------------------

Configuration file
------------------

Upload API
----------

Upload script / GitHub Action
-----------------------------

Pull requests
-------------

Possible issues
---------------

First iteration
---------------

Future improvements and ideas
-----------------------------

References
----------

- https://github.com/readthedocs/readthedocs.org/issues/1083
- https://github.com/readthedocs/readthedocs.org/pull/13011
- https://aws.amazon.com/blogs/storage/automated-extraction-of-compressed-files-on-amazon-s3-using-aws-batch-and-amazon-ecs/
- https://aws.amazon.com/blogs/storage/automatically-decompress-files-in-amazon-s3-using-aws-step-functions/
