Skip builds based on conditions
================================

Read the Docs provides a special build cancellation mechanism that allows you to programmatically skip builds
based on custom conditions. This is useful when you want to avoid unnecessary documentation builds,
saving build time and resources.

.. contents:: Table of contents
   :local:
   :backlinks: none
   :depth: 2

How it works
------------

When any command in your build process exits with the special exit code ``183``,
Read the Docs will immediately cancel the build.
The build will be marked as cancelled and will not consume build time or resources beyond that point.

.. note:: Why exit code 183?

   The exit code 183 was chosen because it represents the word "skip" encoded in ASCII.

   .. code-block:: pycon

      >>> sum(list("skip".encode("ascii")))
      439
      >>> 439 % 256  # Unix exit codes are limited to 0-255
      183

   The 256 modulo operation is necessary because `Unix exit codes are limited to 0-255 <https://tldp.org/LDP/abs/html/exitcodes.html>`_,
   and any value larger than 255 is automatically reduced by taking the modulo 256.

When to skip builds
-------------------

There are several scenarios where you might want to skip documentation builds:

**Save resources on irrelevant changes**
   Skip builds when changes don't affect documentation,
   such as changes only to source code, tests, or CI configuration files.

**Avoid redundant builds**
   Skip builds for draft pull requests, work-in-progress branches,
   or commits with specific markers like ``[skip ci]`` in the commit message.

**Conditional documentation updates**
   Only build documentation when specific files or directories are modified,
   such as the ``docs/`` folder or configuration files.

**Branch-specific logic**
   Skip builds on certain branches that don't require documentation updates,
   such as experimental or development branches.

Examples
--------

The following examples demonstrate common use cases for skipping builds.
All examples use the :ref:`config-file/v2:build.jobs` configuration key
in your ``.readthedocs.yaml`` file.

Skip builds when documentation files haven't changed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example skips pull request builds when there are no changes to documentation-related files
compared to the ``main`` branch:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.12"
     jobs:
       post_checkout:
         # Cancel building pull requests when there aren't changes in the docs directory or YAML file.
         # If there are no changes (git diff exits with 0) we force the command to return with 183.
         # This is a special exit code on Read the Docs that will cancel the build immediately.
         - |
           if [ "$READTHEDOCS_VERSION_TYPE" = "external" ] && git diff --quiet origin/main -- docs/ .readthedocs.yaml;
           then
             exit 183;
           fi

You can customize this example by:

* Adding more paths to check: ``docs/ .readthedocs.yaml requirements/docs.txt``
* Checking against a different branch: ``origin/develop`` instead of ``origin/main``
* Using different comparison operators to check for specific file patterns

Skip builds based on commit message
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example skips builds when the commit message contains ``[skip ci]`` or ``[ci skip]``:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.12"
     jobs:
       post_checkout:
         # Use `git log` to check if the latest commit contains "skip ci",
         # in that case exit the command with 183 to cancel the build
         - (git --no-pager log --pretty="tformat:%s -- %b" -1 | paste -s -d " " | grep -viq "skip ci") || exit 183

This pattern is commonly used in CI/CD systems to skip builds for administrative commits,
such as version bumps or documentation typos.

Skip builds for specific branch patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example skips builds for branches that match certain patterns,
such as personal development branches:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.12"
     jobs:
       post_checkout:
         # Skip builds for branches starting with "dev/" or "experiment/"
         - |
           if echo "$READTHEDOCS_GIT_IDENTIFIER" | grep -qE "^(dev|experiment)/"; then
             exit 183;
           fi

Skip builds based on file types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example skips builds when all changes are to non-documentation files,
such as only images or data files:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2
   build:
     os: "ubuntu-22.04"
     tools:
       python: "3.12"
     jobs:
       post_checkout:
         # Skip if only non-documentation files changed (e.g., only images or data files)
         - |
           if [ "$READTHEDOCS_VERSION_TYPE" = "external" ]; then
             # Get list of changed files
             CHANGED_FILES=$(git diff --name-only origin/main)
             # Check if any changed files are documentation-related.
             # If ALL files are non-documentation (grep finds no documentation files),
             # then we skip the build by exiting with 183.
             if ! echo "$CHANGED_FILES" | grep -qE "\.(rst|md|py|yaml|yml|txt|toml)$"; then
               exit 183;
             fi
           fi

Best practices
--------------

When implementing skip build logic, consider these best practices:

**Test your conditions locally**
   Before deploying skip build logic, test your bash conditions locally
   to ensure they work as expected. Remember that the condition failing will cancel your build.

**Be specific with your conditions**
   Write clear and specific conditions to avoid accidentally skipping builds
   that should run. Overly broad conditions might prevent important documentation updates.

**Document your skip logic**
   Add comments in your ``.readthedocs.yaml`` file explaining why builds are skipped
   and under what conditions. This helps future maintainers understand the configuration.

**Consider the impact on pull requests**
   If you skip builds on pull requests, reviewers won't have preview documentation.
   Make sure this aligns with your team's review process.

**Use environment variables**
   Leverage :doc:`Read the Docs environment variables </reference/environment-variables>`
   like ``READTHEDOCS_VERSION_TYPE`` to make your conditions more precise.

Limitations
-----------

Be aware of these limitations when using the skip build feature:

**No partial cancellation**
   Once a build is cancelled with exit code 183, the entire build stops immediately.
   You cannot selectively skip only certain parts of the build process.

**Not available in configuration file**
   You cannot skip builds using conditions in the ``.readthedocs.yaml`` configuration syntax itself.
   All logic must be implemented in bash commands.

**Build is counted as cancelled**
   Cancelled builds appear in your build history as cancelled, not as skipped or successful.
   This is different from builds that never start due to branch/version filters.

**Webhook notifications still trigger**
   Even though the build is cancelled, webhook notifications (if configured) may still be sent
   with a cancelled status.

Troubleshooting
---------------

**Build is not being skipped**
   * Verify your condition logic is correct by testing it locally
   * Check that the command is returning exit code 183 specifically
   * Ensure you're using the correct :doc:`environment variables </reference/environment-variables>`
   * Review the build logs to see if your condition is being evaluated

**Builds are being skipped unexpectedly**
   * Review your condition logic to ensure it's not too broad
   * Check for syntax errors in your bash commands
   * Verify that file paths and branch names are correct
   * Test the condition in different scenarios (PRs, branches, tags)

**Cannot access Git information**
   * Some Git operations require a full clone. If you need Git history,
     you might need to `unshallow the clone <https://docs.readthedocs.io/en/stable/build-customization.html#unshallow-git-clone>`_
   * Ensure you're running your skip logic in ``post_checkout`` to have access to the repository
