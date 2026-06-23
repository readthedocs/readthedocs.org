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
  We want to support both for the long term. 

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
    All the checks will also be done on the server side.
  - All artifacts are zipped into a single file.
  - A post request is made to the upload API with some metadata like Git branch/tag, commit hash, configuration, etc.
  - A build object is created in Read the Docs with the status "pending" and a presigned URL is returned to the user to upload the artifacts.
  - The zip file is uploaded to the presigned URL to a temporary location in S3.
  - A post request is made to the upload API to notify that the upload is complete and the build can be processed.
- Read the Docs triggers a task to process the build.
  - A docker container is created to process the build (like our current builders do).
  - The zip file is downloaded from the presigned URL.
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

Versions will have a new field to indicate the source of their latest build (``build_source``), either "rtd-build" or "external-upload".
This will allow us to do some checks and validations.

Versions marked as active and where their latest build is from an external upload can't be built using our current build system.
This is to avoid overwriting the documentation built from an external upload with a build from our current build system.
This should mainly happen while users migrate to the new system, new users should only use the new upload system.

We will no longer update the version to keep in sync with the Git branch/tag/commit,
as they will be created when the upload is initiated.

Versions that are deleted from the Git repository will be deleted from Read the Docs if an automation rule is configured to do so.
This includes versions created from external uploads, as they are still linked to a Git branch/tag/commit.

.. note::

   With this new system, we don't have the need to keep a copy of the Git repository versions in Read the Docs.
   We can discuss in the future how we want to handle that.
   The only reason to keep it is to be able to trigger builds from our current build system (while projects migrate),
   and to keep automation rules working on deleted versions.

The "build version" option should be disabled/hidden for versions created from external uploads.

Builds
------

Builds will have a new field to indicate the source of the build (``build_source``), either "rtd-build" or "external-upload".
This will allow us to differentiate between builds that were triggered by our current build system and builds that were triggered by the new upload system.

Latest triggered build wins, previous build is cancelled. Just like our current build system.

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

The "rebuild" option should be disabled/hidden for builds created from external uploads.

Upload API
----------

The upload API will be a private API, and will require an "upload token" to authenticate the requests.
This token can be generated by admins of the project from the project settings page,
and it's linked to the project, not to a user.

.. note::

   The user token can be re-used for initial testing.

POST /api/v3/_internal/upload/initiate:
  Initiate the upload process and create a build object with the state "uploading".
  This endpoint will receive some metadata like Git branch/tag/commit, configuration, etc,
  and return build object and the presigned URL to upload the artifacts.

  If we don't find a version for the Git branch/tag, we can create a new version for it,
  and attach the build to that version.

  ::
      {
         // If using a project-scoped token,
         // this isns't needed. But maybe still require it to be explicit?
         "project": "slug",
         "version": {
            "name": "main",  // name of the Git branch/tag or PR number.
            "type": "branch",  // or "tag" or "external" (PR).
            "commit": "abc123", // full commit hash
            // Optional, if not provided, it's derived from the name of the branch/tag.
            // If the version with that slug exists, but it points to a different Git ref, we error out.
            "slug": "main",
            // Only relevant for RTD business (default to private).
            "privacy_level": "public",  // or "private"
         }
         "configuration": {
            "search": {
            }
         }
      }

   ::
      {
         // Same as the object returned by API V3.
         "build": {
            "id": 123,
            ...
         },
         // Same as the object returned by API V3.
         "version": {
            "id": 456,
            ...
         },
         // Exactly as generated by boto3's generate_presigned_post.
         "upload_url": {
            "url": "https://amzn-s3-demo-bucket.s3.amazonaws.com",
            "fields": {
               'acl': "private",
               'key': "mykey",
               'signature': "mysignature",
               'policy': "mybase64 encoded policy"
            }
         }
      }

   The presigned URL will have a limit on the size (1GB, see "Artifacts size" section), content type (zip), and expiration time (30 minutes).
   See https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/generate_presigned_post.html.

   The zip to upload should contain all artifacts in the following structure:

   - html/index.html
   - pdf/documentation.pdf
   - epub/documentation.epub
   - htmlzip/documentation.zip

   The names of pdf/epub/zip files can be anything, as long as there is just one.

POST /api/v3/_internal/upload/complete:
  Notify that the upload is complete and the build can be processed.
  This endpoint will receive the build ID.

  ::
      {
         "build": 123,
         "status": "uploaded", // or "failed" if the upload failed and the build should be cancelled.
      }

  ::
      {
         // Same as the object returned by API V3.
         "build": {
            "id": 123,
            ...
         }
      }

  This endpoint will trigger a task similar to our builders.
  This task will start a docker container (we can re-use the docker image used to clone the repository),
  download the artifacts, validate them, upload them to their final destination, and update the build status,
  send the webhooks, update the commit status, etc.
  Just like our current builders do.

  The zip validation includes checking that the expected files are present,
  and that the size of the artifacts is within the limits.

  This endpoint could also be used to notify that the upload has failed,
  so the build is cancelled and the status is updated to "failure".

  We also need to have a task to cancel builds that are in "uploading" state for a long time,
  in case the upload is never completed.
  We can cancel builds after 45 minutes of inactivity.

  .. note::

     S3 sends events when a file is uploaded, while we can use that to trigger the processing task,
     it's better to have an explicit endpoint, it lets us report failures easily.

.. note::

   `OIDC <https://docs.github.com/en/actions/concepts/security/openid-connect>`__ can be explored in the future for tokenless authentication.

S3
--

All artifacts will be uploaded to S3, and then processed from there.
We'll have a separate bucket for the uploaded artifacts,
with a lifecycle policy to clean up the artifacts after a certain period of time.
See https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-expire-general-considerations.html,
https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html.

Artifacts will be uploaded as a zip file, in the path: {project_id}/{build_id}/artifacts.zip.
Once the build is processed, the artifacts will be extracted and uploaded to their final destination as we do now.

Upload script / GitHub Action
-----------------------------

In theory, given the token, users can upload the artifacts from anywhere,
but we shouldn't encourage users to manually call the API directly.
We can provide a simple bash script that can be downloaded and used to upload the artifacts,
or a GitHub Action that can be used in their workflows.

When run from GitHub, we can automatically get the Git branch/tag/commit information from the environment variables,
and pass it to the API, when run outside of GitHub, we could still try to get this information from the environment,
but we should make it explicit to start with.

The action/script should be called after the documentation is built, and it will handle the upload process.
The action/script will make sure to generate the zip file with the correct structure,
given the paths to the artifacts.

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

Aliases: latest/stable
----------------------

After a build has been processed, we can decide if latest or stable aliases should point to the results of that build.
If so, we trigger a task to update the latest/stable.

This task will only do a copy of the artifacts from the version to the latest/stable location.
While this task won't spin up a docker container, it will create a build object with some dummy output
to keep the same modeling as our current builders, and to be able to send the same webhooks.

.. note::

   We can start thinking about making latest/stable real aliases instead of copying the artifacts to a new location,
   or duplicating builds for the same source.

As we allow right now, users can also manually create versions named "latest" or "stable" to skip our logic.

Pull requests
-------------

Since a token is required to upload the artifacts, sharing this token in a public repository is not a good idea,
as anyone can see it and use it to upload builds for that project.

Building from PRs that originate from the same repository is straightforward, as the user has access to the repository and can generate a token to upload the artifacts.
But for PRs that originate from forks, it's more complicated, as the user doesn't have access to the repository and can't generate a token to upload the artifacts,
there are ways to share this token using a ``pull_request_target`` event in GitHub Actions, but it can be easily misused to run malicious code in the context of the base repository.

We can try to offer a token that's only scoped for PR builds.
This token should still be kept secret, as it can be used to upload builds to the pull request previews domain of the project,
but the impact of the token being leaked is much smaller, as it doesn't affect production documentation.

Webhooks and status API
-----------------------

Webhook events:

- Build triggered: we can emit this one when the upload is initiated,
  or replace it with "uploading".
- Build passed: we can emit this one when the build is finished and successful.
  Same as our current "build passed" event.
- Build failed: we can emit this one when the build is finished and failed.
  Same as our current "build failed" event.

Commit status doesn't require any changes, we can update the status as we do now with the three states: pending, success, failure.

First iteration
---------------

The first iteration would be like a half polished proof of concept, to validate the architecture and the implementation.
While not all things discussed in this document will be implemented in the first iteration,
this first iteration can be improved in the following weeks without major changes.

- Implement the upload API and the processing task.
- Internal bash script to upload the artifacts using the API.
  Almost no client side validations (size, structure, etc),
  server side validations will be done when processing the build.
- Skip search configuration.
- Add the new S3 bucket with the lifecycle policy.
- Skip latest/stable logic.
- Re-use the user token for authentication.
- Minimal integration in the UI.
- Minimal checks/enforcement for versions and builds created from external uploads.

This first iteration is not a beta, it will be used for our own projects only.

Future improvements and ideas
-----------------------------

- Use a more lightweight docker image to unzip the artifacts.
- Use a lambda instead of a docker container to process the build.
  Lambdas have a maximum storage of 10GB, which may not be enough for some builds.
  But AWS has some other options for big files:

  - https://aws.amazon.com/blogs/storage/automated-extraction-of-compressed-files-on-amazon-s3-using-aws-batch-and-amazon-ecs/
  - https://aws.amazon.com/blogs/storage/automatically-decompress-files-in-amazon-s3-using-aws-step-functions/

- Support OIDC for authentication instead of API tokens.
- Make latest/stable real aliases instead of copying the artifacts to a new location.
- Sign the script used to upload the artifacts.
- Do indexing tasks (search, file tree diff) just after the artifacts are uploaded to their final destination,
  instead of querying the files again from storage.

References
----------

- https://github.com/readthedocs/readthedocs.org/issues/1083
- https://github.com/readthedocs/readthedocs.org/pull/13011

Attachments
-----------

Artifacts size
~~~~~~~~~~~~~~

We are logging this information in
https://github.com/readthedocs/readthedocs.org/blob/c026c537983e83bb71ed489832acc1bffdee65ed/readthedocs/projects/tasks/builds.py#L1050-L1065

Using the following in New Relic

::
   SELECT count(*) FROM Log 
   WHERE allColumnSearch('Build artifacts directory size.', insensitive: true) 
   FACET size

We get:

::
   Size (in megabytes), Count (in thousands)
   1, 69
   10, 58
   11, 32
   13, 32
   14, 30
   2, 32
   4, 31
   5, 44
   7, 78
   8, 48

Allowing uploads of 5GB uncompressed (and 1G compressed) should be enough for most projects.

Zip file validation
~~~~~~~~~~~~~~~~~~~

Zip file validation using unzip/zipinfo provided by Claude:

.. code-block:: python

   import os, stat, zipfile

   MAX_TOTAL = 5 * 1024**3  # uncompressed cap
   MAX_FILES = 50_000
   MAX_RATIO = 100  # uncompressed/compressed

   with zipfile.ZipFile(path) as zf:
       total = comp = 0
       for info in zf.infolist():
           mode = info.external_attr >> 16
           if stat.S_ISLNK(mode):  # no symlinks
               raise ValueError("symlink entry")
           norm = os.path.normpath(info.filename)
           if norm.startswith(("/", "..")) or os.path.isabs(info.filename):
               raise ValueError("path traversal")  # zip-slip
           total += info.file_size
           comp += info.compress_size
       if (
           total > MAX_TOTAL
           or len(zf.infolist()) > MAX_FILES
           or (comp and total / comp > MAX_RATIO)
       ):
           raise ValueError("archive too large / bomb")
       zf.extractall(dest)  # already strips leading "/" and ".." components

Two things worth knowing:
  zipfile.extractall already neutralizes zip-slip (it sanitizes .. and leading slashes), but it does not guard against bombs or restore-then-write-through symlinks — that's why the explicit checks above exist. If you reach for the unzip CLI instead, you get none of these guards, so I'd stay in Python.
  Header sizes can lie. The central-directory ``file_size`` is attacker-controlled, so the pre-scan is a fast first gate, not the real boundary. Back it with container limits so a lying header still can't hurt you: ``ulimit -f``, a size-capped tmpfs (or disk quota) for dest, non-root, no network. Defense in depth — cheap given you already have the container.

.. code-block:: bash

   zip=artifacts.zip; dest=out

   # 1. Integrity — CRC-check every entry, decompress to memory, no disk write.
   #    Catches truncated/corrupt uploads. (Still does full CPU work, so gate size first if paranoid.)
   unzip -tqq "$zip" || exit 1

   # 2. Summary line: count + uncompressed + compressed → size and ratio in one shot.
   zipinfo -t "$zip"
   #   -> "412 files, 5242880 bytes uncompressed, 524288 bytes compressed:  90.0%"
   zipinfo -t "$zip" | awk '{u=$3; c=$6}
   END { if (u > 5*1024*1024*1024) { print "too big"; exit 1 }
         if (c>0 && u/c > 100)     { print "suspicious ratio"; exit 1 } }' || exit 1

   # 3. Reject absolute paths / traversal. -1 prints bare filenames, one per line.
   zipinfo -1 "$zip" | grep -Eq '^/|(^|/)\.\.(/|$)' && { echo "unsafe path"; exit 1; }

   # 4. Reject symlinks & other non-regular entries via the permission column
   #    (symlink rows start with 'l', also block p/b/c/s).
   zipinfo "$zip" | grep -Eq '^[lpbcs]' && { echo "non-regular entry"; exit 1; }

   # 5. Extract under hard limits regardless of what the headers claimed.
   mkdir -p "$dest"
   ( ulimit -f 2097152                 # max ~1 GiB per file (unit = 512B blocks)
   timeout 300 unzip -qq -o "$zip" -d "$dest" )

Notes that matter:
  ``zipinfo -t`` field positions can shift with locale/version, so sanity-check the awk columns ($3 uncompressed, $6 compressed) against your actual image once.
  unzip already refuses ../ traversal by default (it skips and warns), so step 3 is belt-and-suspenders — but keep it, since the listing check lets you reject the whole upload instead of silently dropping entries. Don't add -j (it flattens directories and would destroy the html/ layout).
  Steps 2–4 read only the central directory, which is attacker-controlled and can lie. So step 5's ``ulimit -f`` + ``timeout`` + a size-capped destination (``tmpfs -o size=`` or a quota) is the part that's actually load-bearing; the rest is fast-fail.

If Python's in the image (it will be), ``python -m zipfile -l artifacts.zip`` lists contents, and the zipfile pre-scan I showed earlier does steps 2–4 more robustly than parsing zipinfo text — but the commands above are the pure-shell answer you asked for.
