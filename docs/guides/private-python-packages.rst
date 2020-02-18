Installing Private Python Packages
==================================

.. warning::

   This guide is for :doc:`/commercial/index`.

Read the Docs uses :doc:`pip <pip:index>` to install your Python packages.
If you have private dependencies, you can install them from
a :ref:`private Git repository <guides/private-python-packages:From a Git repository>` or
a :ref:`private repository manager <guides/private-python-packages:From a repository manager other than PyPI>`.

From a Git repository
---------------------

Pip supports installing packages from a :ref:`Git repository <pip:vcs support>` using the URI form:

.. code::
   
   git+https://gitprovider.com/user/project.git@{version}#egg={package-name}

Or if your repository is private:

.. code::
   
   git+https://{token}@gitprovider.com/user/project.git@{version}#egg={package-name}

Where ``version`` can be a tag, a branch, or a commit.
And ``token`` is a personal access token with read only permissions from your provider.

.. We should add the git+ssh form when we support running the ssh-agent in the build step.

To install the package,
you need to add the URI in your :ref:`requirements file <config-file/v2:Requirements file>`.
Pip will automatically expand environment variables in your URI,
so you don't have to hard code the token in the URI.
See :doc:`using environment variables in Read the Docs </guides/environment-variables>`.

Bellow you can find how to get a personal access token from our supported providers.
We will be using environment variables for the token.

GitHub
~~~~~~

You need to create a personal access token with the ``repo`` scope.
Check the `GitHub documentation <https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line#creating-a-token>`__
on how to create a personal token.

URI example:

.. code::
   
   git+https://${GITHUB_TOKEN}@github.com/user/project.git@{version}#egg={package-name}

.. warning::

   GitHub doesn't support tokens per repository.
   A personal token will grant read and write access to all repositories the user has access to.
   You can create a `machine user <https://developer.github.com/v3/guides/managing-deploy-keys/#machine-users>`__
   to give read access only to the repositories you need.

GitLab
~~~~~~

You need to create a deploy token with the ``read_repository`` scope for the repository you want to install the package from.
Check the `GitLab documentation <https://docs.gitlab.com/ee/user/project/deploy_tokens/#creating-a-deploy-token>`__
on how to create a deploy token.

URI example:

.. code::
   
   git+https://${GITLAB_TOKEN_USER}:${GITLAB_TOKEN}@gitlab.com/user/project.git@{version}#egg={package-name}

Here ``GITLAB_TOKEN_USER`` is the user from the deploy token you created, not your GitLab user.

Bitbucket
~~~~~~~~~

You need to create an app password with ``Read repositories`` permissions.
Check the `Bitbucket documentation <https://confluence.atlassian.com/bitbucket/app-passwords-828781300.html>`__
on how to create an app password.

URI example:

.. code::
   
   git+https://${BITBUCKET_USER}:${BITBUCKET_APP_PASSWORD}@bitbucket.org/user/project.git@{version}#egg={package-name}'

Here ``BITBUCKET_USER`` is your Bitbucket user.

.. warning::

   Bitbucket doesn't support app passwords per repository.
   An app password will grant read access to all repositories the user has access to.

From a repository manager other than PyPI
-----------------------------------------

Pip by default will install your packages from `PyPI <https://pypi.org/>`__.
If you use a repository manager like *pypiserver*, or *Nexus Repository*,
you need to set the :option:`pip:--index-url` option.
You have two ways of set that option:

- Set the ``PIP_INDEX_URL`` :doc:`environment variable in Read the Docs </guides/environment-variables>` with the index URL.
  See :ref:`pip:using environment variables`.
- Put ``--index-url=https://my-index-url.com/`` at the top of your requirements file.
  See :ref:`pip:requirements file format`.

.. note::

   Check your repository manager's documentation to obtain the appropriate index URL.
