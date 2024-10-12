Version file tree diff
======================

Goals
-----

- Compare files from two versions to identify the files that have been added, removed, or modified.
- Provide an API for this feature.
- Integrate this feature to suggest redirects on files that were removed.
- Integrate this feature to list the files that changed in a pull request.

Non-goals
---------

- Replace the `docdiff <https://github.com/readthedocs/addons?tab=readme-ov-file#docdiff>`__ feature from addons.
  That works on the client side, and it's good for comparing the content of files.

Current problems
----------------

Currently, when a user opens a PRs, they need to manually search for the files of interest (new and modified files).
We have a GitHub action that links to the root of the documentation preview, that helps a little, but it's not enough.

When files are removed or renamed, users may not be aware that a redirect may be needed.
We track 404s in our traffic analytics, but they don't keep track of the version,
and it may be too late to add a redirect when users are already seeing a 404.

In the past, we haven't implemented those features, because it's hard to map the source files to the generated files,
since that depends on the build tool and configuration used by the project.

Git providers may already offer a way to compare file trees, but again,
they work on the source files, and not on the generated files.

All hope was lost for having nice features like this, until now.

Proposed solution
-----------------

Since redirects and files of interest are related to the generated files,
instead of working over the source files, we will work over the generated files, which we have access to.

The key points of this feature are:

- Get the diff of the file tree between two versions.
- Expose that as an API.
- Integrate that in PR previews.

Diff between two versions
-------------------------

Using a manifest
~~~~~~~~~~~~~~~~

We can create a manifest that contains the hashes and other important metadata of the files,
we can save this manifest in storage or in the DB.

When a build finishes, we generate this manifest for all HTML files, and store it.
When we need to compare two versions, we can just compare the manifests.

This doesn't require downloading the files, but it requires building a version to generate the manifest.

The manifest will be a JSON object with the following structure:

.. code:: json

   {
       "build": {
           "id": 1
       },
       "files": {
          "index.html": {
              "hash": "1234567890"
          },
          "path/to/file.html": {
              "hash": "1234567890"
          }
       }
   }

Using rclone
~~~~~~~~~~~~

.. note::

   This solution won't be used in the final implementation, it's kept here for reference.

We are already using ``rclone`` to speed up uploads to S3,
``rclone`` has a command (``rclone check``) to return the diff between two directories.
For this, it uses the metadata of the files, like size and hash
(it doesn't download the files).

.. code:: console

   $ ls a
   changed.txt  new.txt  unchanged.txt
   $ ls b
   changed.txt  deleted.txt  unchanged.txt
   $ rclone check --combined=- /usr/src/app/checkouts/readthedocs.org/a /usr/src/app/checkouts/readthedocs.org/b
   + new.txt
   - deleted.txt
   = unchanged.txt
   * changed.txt

The result is a list of files with a mark indicating if they were added, removed, or modified, or if they were unchanged.
The result is easy to parse.
There is no option to exclude the files that were unchanged when using ``--combined``,
another option can be to output each type of change to a different file (``--missing-on-dst``, ``--missing-on-src``, ``--differ``).

To start, we will only consider HTML files (``--include=*.html``).

Changed files
-------------

Listing the files that were added or deleted is straightforward,
but when listing the files that were modified, we want to list files that had relevant changes only.

For example, if the build injects some content that changes on every build (like a timestamp or commit),
we don't want to list all files as modified.

We have a couple of options to improve this list.

Hashing the main content
~~~~~~~~~~~~~~~~~~~~~~~~

Timestamps and other metadata is usually added in the footer of the files, outside the main content.
Instead of hashing the whole file, we can hash only the main content of the file,
and use that hash to compare the files.

This will allow us to better detect files that were modified in a meaningful way.

Since we don't need a secure hash, we can use MD5, since it's built-in in Python.

Lines changed between two files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

   This solution won't be used in the final implementation, it's kept here for reference.

In order to provide more useful information, we can sort the files by some metrics,
like the number of lines that changed.

Once we have the list of files that changed, we can use a tool like ``diff`` to get the lines that changed.
This is useful to link to the most relevant files that changed in a PR.

.. code:: console

   $ cat a.txt
   One
   Two
   Three
   Four
   Five
   $ cat b.txt
   Ore
   Three
   Four
   Five
   Six
   $ diff --side-by-side --suppress-common-lines a.txt b.txt
   One                                                           | Ore
   Two                                                           <
                                                                 > Six

.. note::

   Taken from https://stackoverflow.com/questions/27236891/diff-command-to-get-number-of-different-lines-only.

The command will return only the lines that changed between the two files.
We can just count the lines, or maybe even parse each symbol to check if the line was added or removed.

Another alternative is to use the `difflib <https://docs.python.org/3/library/difflib.html>`__ module,
the only downside is that it doesn't distinguish lines that were changed from lines that were added or removed.
But maybe that's ok? Do we really need to know if a line was changed instead of added or removed?

.. code:: python

   import difflib

   diff = difflib.ndiff(["one", "two", "three", "four"], ["ore", "three", "four", "five"])
   print(list(diff))
   # ['+ ore', '- one', '- two', '  three', '  four', '+ five']

A good thing of using Python is that we don't need to write the files to disk,
and the result is easier to parse.

Alternative metrics
+++++++++++++++++++

.. note::

   This solution won't be used in the final implementation, it's kept here for reference.

Checking the number of lines that changed is a good metric, but it requires downloading the files.
Another metric we could use is the size of the files, that can be obtained from the metadata (no need of downloading the files),
The most a file size has changed, the most lines have likely been added or removed,
this still leaves lines that changed with the same amount of characters as irrelevant in the listing.

Storing results
---------------

Doing a diff between two versions can be expensive, so we need to store the results.

We can store the results in the DB (``VersionDiff``).
The information to store would contain some information about the versions compared, the builds, and the diff itself.

.. code:: python

   class VersionDiff(models.Model):
       version_a = models.ForeignKey(
           Version, on_delete=models.CASCADE, related_name="diff_a"
       )
       version_b = models.ForeignKey(
           Version, on_delete=models.CASCADE, related_name="diff_b"
       )
       build_a = models.ForeignKey(Build, on_delete=models.CASCADE, related_name="diff_a")
       build_b = models.ForeignKey(Build, on_delete=models.CASCADE, related_name="diff_b")
       diff = JSONField()

The diff will be a JSON object with the files that were added, removed, or modified.
With an structure like this:

.. code:: json

   {
       "added": [{"file": "new.txt"}],
       "removed": [{"file": "deleted.txt"}],
       "modified": [{"file": "changed.txt", "lines": {"added": 1, "removed": 1}}]
   }

The information is stored in a similar way that it will be returned by the API.
Things important to note:

- We need to take into consideration the diff of the latest successful builds only.
  If any of the builds from the stored diff don't match the latest successful build of any of the versions,
  we need to the diff again.
- Once we have the diff between versions ``A`` and ``B``, we can infer the diff between ``B`` and ``A``.
  We can store that information as well, or just calculate it on the fly.
- The list of files are objects, so we can store additional information in the future.
- When a file has been modified, we also store the number of lines that changed.
  We could also show this for files that were added or removed.
- If a project or version is deleted (or deactivated), we should delete the diff as well.
- Using the DB to save this information will serve as the lock for the API,
  so we don't calculate the diff multiple times for the same versions.

We could store the changed files sorted by the number of changes, or make that an option in the API,
or just let the client sort the files as they see fit.

API
---

The initial diff operation can be expensive, so we may consider not exposing this feature to unauthenticated users.
And a diff can only be done between versions of the same project that the user has access to.

The endpoint will be:

   GET /api/v3/projects/{project_slug}/diff/?version_a={version_a}&version_b={version_b}

And the response will be:

.. code:: json

   {
       "version_a": {"id": 1, "build": {"id": 1}},
       "version_b": {"id": 2, "build": {"id": 2}},
       "diff": {
           "added": [{"file": "new.txt"}],
           "removed": [{"file": "deleted.txt"}],
           "modified": [{"file": "changed.txt", "lines": {"added": 1, "removed": 1}}]
       }
   }

The version and build can be the full objects, or just the IDs and slugs.

We will generate a lock on this request, to avoid multiple calls to the API for the same versions.
We can reply with a ``202 Accepted`` if the diff is being calculated in another request.

Integrations
------------

You may be thinking that once we have an API, it will be just a matter of calling that API from a GitHub action. Wrong!

Doing the API call is easy, but knowing *when* to call it is hard.
We need to call the API after the build has finished successfully,
or we will be comparing the files of an incomplete or stale build.

Luckily, we have a webhook that tells us when a build has finished successfully.
But, we don't want users to have to implement the integration by themselves.

We could:

- Use this as an opportunity to explore using GitHub Apps.
- Request additional permissions in our existing OAuth2 integration (``project`` scope). Probably not a good idea.
- Expose this feature in the dashboard for now, and use our GitHub action to simply link to the dashboard.
  Maybe don't even expose the API to the public, just use it internally.
- Use a custom `repository dispatch event <https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#repository_dispatch>`__
  to trigger the action from our webhook. This requires the user to do some additional setup,
  and for our webhooks to support custom headers.
- Hit the API repeatedly from the GitHub action until the diff is ready.
  This is not ideal, some build may take a long time, and the action may time out.
- Expose this feature in the addons API only, which will hit the service when a user views the PR preview.

Initial implementation
----------------------

For the initial implementation, we will:

- Generate a manifest of all HTML files from the versions that we want to compare.
  This will be done at the end of the build.
- Generate the hash based on the main content of the file,
  not the whole file.
- MD5 will be the hashing algorithm used.
- Only expose the files that were added, removed, or modified (HTML files only).
  The number of lines that changed won't be exposed.
- Don't store the results in the DB,
  we can store the results in a next iteration.
- Expose this feature only via the addons feature.
- Allow to diff an external version against the version that points to the default branch/tag of the project only.
- Use a feature flag to enable this feature on projects.

Other features that are not mentioned here, like exposing the number of lines that changed,
or a public API, will not be implemented in the initial version,
and may be considered in the future (and their implementation is subject to change).

Possible issues
---------------

In the case that we use a manifest,
hashing the contents of the files may add some overhead to the build.

In the case that we use ``rclone``,
even if we don't download files from S3, we are still making calls to S3, and AWS charges for those calls.
But since we are doing this on demand, and we can cache the results, we can minimize the costs
(maybe is not that much).

``rclone check`` returns only the list of files that changed,
if we want to make additional checks over those files, we will need to make additional calls to S3.

We should also just check a X number of files, we don't want to run a diff of thousands of files,
and also a limit on the size of the files.

Future improvements and ideas
-----------------------------

- Detect moved files.
  This will imply checking the hashes of deleted and added files,
  if that same hash of a file that was deleted matches one from a file that was added,
  we have a move.
  In case we use rclone, since we don't have access to those hashes after rclone is run,
  we would need to re-fetch that metadata from S3.
  Could be a feature request for rclone.
- Detect changes in sections of HTML files.
  We could reuse the code we have for search indexing.
- Expand to other file types
- Allow doing a diff between versions of different projects
- Allow to configure how the main content of the file is detected
  (like a CSS selector).
- Allow to configure content that should be ignored when hashing the file
  (like a CSS selector).
