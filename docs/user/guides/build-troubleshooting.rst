Troubleshooting build errors
============================

.. include:: /shared/contribute-to-troubleshooting.rst

This guide provides some common errors and resolutions encountered in the :doc:`build process </builds>`.

Git errors
----------

In the examples below, we use ``github.com``, however error messages are similar for GitLab, Bitbucket etc.


terminal prompts disabled
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   fatal: could not read Username for 'https://github.com': terminal prompts disabled

**Resolution:** This error can be quite misleading. It usually occurs when a repository could not be found because of a typo in the repository name or because the repository has been deleted. Verify your repository URL in :guilabel:`Admin > Settings`.

This error also occurs if you have changed a ``public`` repository to ``private`` and you are using ``https://`` in your git repository URL.

.. note::

   To use private repositories, you need a plan on `Read the Docs Business <https://app.readthedocs.com>`__.


error: pathspec
~~~~~~~~~~~~~~~

.. code-block:: text

   error: pathspec 'main' did not match any file(s) known to git

**Resolution:** A specified branch does not exist in the git repository.
This might be because the git repository was recently created (and has no commits nor branches) or because the default branch has changed name. If for instance, the default branch on GitHub changed from ``master`` to ``main``, you need to visit :guilabel:`Admin > Settings` to change the name of the default branch that Read the Docs expects to find when cloning the repository.


Permission denied (publickey)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   git@github.com: Permission denied (publickey).

   fatal: Could not read from remote repository.

**Resolution:** The git repository URL points to a repository, user account or organization that Read the Docs does not have credentials for. Verify that the public SSH key from your Read the Docs project is installed as a *deploy key* on your VCS (GitHub/GitLab/Bitbucket etc):

.. This should be included as a snippet since it's used 2 times already

1. Navigate to :guilabel:`Admin > SSH Keys`
2. Copy the contents of the public key.
3. Ensure that the key exists as a deploy key at your Git provider. Here are direct links to access settings for verifying and changing deploy keys - customize the URLs for your Git provider and repository details:

   - ``https://github.com/<username>/<repo>/settings/keys``
   - ``https://gitlab.com/<username>/<repo>/-/settings/repository``
   - ``https://bitbucket.org/<username>/<repo>/admin/access-keys/``


ERROR: Repository not found.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   ERROR: Repository not found.
   fatal: Could not read from remote repository.

**Resolution:** This error usually occurs on private git repositories that no longer have the public SSH key from their Read the Docs project installed as a *deploy key*.

1. Navigate to :guilabel:`Admin > SSH Keys`
2. Copy the contents of the public key.
3. Ensure that the key exists as a deploy key at your Git provider. Here are direct links to access settings for verifying and changing deploy keys - customize the URLs for your VCS host and repository details:

   - ``https://github.com/<username>/<repo>/settings/keys``
   - ``https://gitlab.com/<username>/<repo>/-/settings/repository``
   - ``https://bitbucket.org/<username>/<repo>/admin/access-keys/``

This error is rare for public repositories. If your repository is public and you see this error, it may be because you have specified a wrong domain or forgotten a component in the path.


Build timeouts and out-of-memory errors
---------------------------------------

If your build is cancelled with a message like ``Build exited due to time out`` or
``Build exited due to excessive memory consumption``, your project is exceeding
the :ref:`build resource limits <builds:Build resources>`.

The following steps can help you stay within limits, in order of least to most disruptive:

1. **Reduce the output formats you build.**
   Building ``htmlzip`` or ``pdf`` in addition to ``html`` uses significantly more memory and time.
   You can disable these in your :doc:`configuration file </config-file/v2>` using the
   :ref:`formats <config-file/v2:formats>` setting.

2. **Trim your documentation dependencies.**
   If you reuse your project's main ``requirements.txt`` for docs, create a separate, smaller
   requirements file that only installs what Sphinx or MkDocs actually needs.
   See :doc:`/guides/reproducible-builds` for guidance.

3. **Switch from autodoc to autoapi.**
   If you are using ``sphinx.ext.autodoc`` and installing your entire package to generate
   API docs, consider `sphinx-autoapi`_ instead.
   It generates the same API documentation output by statically analysing your source code,
   without needing to install or import your package.
   This can dramatically reduce both memory usage and build time.

4. **Use mamba instead of conda.**
   If your build uses conda, switching to :ref:`mamba <guides/conda:Making builds faster with mamba>`
   reduces memory usage and is faster at solving environments.

5. **Request a limit increase.**
   If none of the above steps help, you can email support@readthedocs.org with your
   project URL and an explanation of why you need more resources.
   On |com_brand|, contact support@readthedocs.com.

.. _sphinx-autoapi: https://sphinx-autoapi.readthedocs.io/


Configuration file errors
--------------------------

If your build fails with an error message that mentions ``.readthedocs.yaml``,
the most common causes are:

**Invalid or unsupported setting**
   Read the Docs validates every configuration file and will fail the build if it
   encounters an unsupported key or an invalid value.
   Check the :doc:`configuration file reference </config-file/v2>` to verify that
   all of your settings are correct and supported.

**Missing configuration file**
   If you have enabled the requirement for a configuration file in your project
   settings but the file does not exist in the repository (or is in the wrong
   location), the build will fail.
   The file must be named ``.readthedocs.yaml`` and placed at the root of your
   repository by default.

**More than one configuration file found**
   Only one ``.readthedocs.yaml`` file is expected per repository (unless you
   are using a monorepo with a custom configuration path).
   If multiple configuration files are detected in unexpected locations, remove
   the extras.

For a complete description of all available settings and their accepted values,
see the :doc:`configuration file reference </config-file/v2>`.


General build failures
-----------------------

If your build fails without a clear error message related to your content or
configuration, it may be caused by a transient infrastructure issue on the
Read the Docs side.

**What to do:**

1. Check the `Read the Docs status page`_ to see if there is an ongoing incident.
2. Try triggering a new build by clicking :guilabel:`Build version` from your
   project dashboard. Many transient failures resolve on a retry.
3. If the problem persists, send an email to support@readthedocs.org (or
   support@readthedocs.com for |com_brand|) and include:

   - The **project slug** (the name in the URL of your project dashboard).
   - The **build ID** from the failing build's URL
     (for example, in ``https://app.readthedocs.org/projects/myproject/builds/12345678/``
     the build ID is ``12345678``).

   Including the build ID lets the support team look up the exact logs for
   your build, even if the failure is not visible in the UI.

.. _Read the Docs status page: https://status.readthedocs.org/

