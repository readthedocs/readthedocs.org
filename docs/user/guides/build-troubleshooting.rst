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

   To use private repositories, you need a plan on `Read the Docs for Business <https://app.readthedocs.com>`__.


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
