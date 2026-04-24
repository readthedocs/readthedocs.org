How to install private python packages
======================================

.. warning::

   This guide is for :doc:`/commercial/index`.

Read the Docs uses :ref:`pip <config-file/v2:python.install>` to install your Python packages.
If you have private dependencies, you can install them from
a :ref:`private Git repository <guides/private-python-packages:From a Git repository>` or
a :ref:`private repository manager <guides/private-python-packages:From a repository manager other than PyPI>`.

From a Git repository
---------------------

Pip supports installing packages from a :ref:`Git repository <pip:vcs support>` using the URI form:

- ``git+https://gitprovider.com/user/project.git@{version}`` (public repository)
- ``git+https://{token}@gitprovider.com/user/project.git@{version}`` (private repository)

Where ``version`` can be a tag, a branch, or a commit, and ``token`` is a personal access token with read only permissions from your provider.

.. TODO: We should add the git+ssh form when we support running the ssh-agent in the build step.

To install a private package from a Git repositories, add the URI to your :ref:`requirements file <config-file/v2:Requirements file>`. Make sure to use an environment variable for the token, so you don't have to hard code it in the URI.

`Pip automatically  expands <https://pip.pypa.io/en/stable/reference/requirements-file-format/#using-environment-variables>`__ environment variables in POSIX format: using only uppercase letters and ``_``, and including a dollar sign and curly brackets around the name, like ``${API_TOKEN}``.

See :doc:`using environment variables in Read the Docs </environment-variables>` for more information.

.. contents:: How to get a personal access token from our supported providers
   :local:

GitHub
~~~~~~

You need to create a fine-grained personal access token with the ``Contents`` repository permission set to ``Read-only``.
Follow the `GitHub documentation <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token>`__
on how to create a fine-grained personal access token.

URI example:

.. code::

   git+https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/user/project.git@{version}

GitLab
~~~~~~

You need to create a deploy token with the ``read_repository`` scope for the repository you want to install the package from.
Follow the `GitLab documentation <https://docs.gitlab.com/ee/user/project/deploy_tokens/#creating-a-deploy-token>`__
on how to create a deploy token.

URI example, where ``GITLAB_TOKEN_USER`` is the user from the deploy token you created, not your GitLab user:

.. code::

   git+https://${GITLAB_TOKEN_USER}:${GITLAB_TOKEN}@gitlab.com/user/project.git@{version}

Bitbucket
~~~~~~~~~

You need to create an app password with ``Read repositories`` permissions.
Follow the `Bitbucket documentation <https://confluence.atlassian.com/bitbucket/app-passwords-828781300.html>`__
on how to create an app password.

URI example:

.. code::

   git+https://${BITBUCKET_USER}:${BITBUCKET_APP_PASSWORD}@bitbucket.org/user/project.git@{version}'

Here ``BITBUCKET_USER`` is your Bitbucket user.

.. warning::

   Bitbucket doesn't support app passwords per repository.
   An app password will grant read access to all repositories the user has access to.
   You can create a `machine user <https://confluence.atlassian.com/bitbucketserver/ssh-access-keys-for-system-use-776639781.html>`__ to give read access only to the repositories you need.

From a repository manager other than PyPI
-----------------------------------------

By default Pip installs your packages from `PyPI <https://pypi.org/>`__.
If you are using a different repository manager like *pypiserver*, or *Nexus Repository*,
you need to get the index URL from your repository manager and set the :option:`pip:--index-url` option in one of the following ways:

- Set the ``PIP_INDEX_URL`` :doc:`environment variable in Read the Docs </environment-variables>` with the index URL.
  See the Requirements File `environment variables <https://pip.pypa.io/en/stable/reference/requirements-file-format#using-environment-variables>`__ reference.
- Put ``--index-url=https://my-index-url.com/`` at the top of your requirements file.
  See :ref:`pip:requirements-file-format`.
