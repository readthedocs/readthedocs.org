Using Private Git Submodules with Read the Docs for Business
============================================================

Read the Docs uses SSH keys (with read only permissions) in order to clone private repositories.
An SSH key is automatically generated and added to your main repository, but not on your submodules.
In order to give Read the Docs access to clone your submodules you'll need to add the public SSH key to each repository of your submodules.

.. note::

   You can manage which submodules Read the Docs should clone using a configuration file.
   See :ref:`config-file/v2:submodules`.

Project's SSH Key
-----------------

You can find the public SSH key of your Read the Docs project by

- Going to the :guilabel:`Admin` tab of your project
- Click on ``SSH Keys``
- Click on the fingerprint of the SSH key (it looks like ``6d:ca:6d:ca:6d:ca:6d:ca``).

.. note::
   
   The private part of the SSH key is kept secret.

GitHub
------

For GitHub, Read the Docs uses `deploy keys with read only access <https://developer.github.com/v3/guides/managing-deploy-keys/#deploy-keys>`__.
GitHub doesn't allow you to reuse a deploy key across different repositories.
But you can use `machine users <https://developer.github.com/v3/guides/managing-deploy-keys/#machine-users>`__
to give read access to several repositories using only one SSH key.

- Remove the SSH deploy key that was added to the main repository on GitHub

  - Go to the project's settings on GitHub
  - Click on :guilabel:`Deploy Keys`
  - Delete the key added by ``Read the Docs Commercial (readthedocs.com)``

- Create a GitHub user and give it read only permissions to all the necessary repositories.
  You can do this by adding the account
  as a `collaborator <https://help.github.com/en/github/setting-up-and-managing-your-github-user-account/inviting-collaborators-to-a-personal-repository>`__,
  as an `outside collaborator <https://help.github.com/en/github/setting-up-and-managing-organizations-and-teams/adding-outside-collaborators-to-repositories-in-your-organization>`__,
  or to a `team in an organization <https://help.github.com/en/github/setting-up-and-managing-organizations-and-teams/adding-organization-members-to-a-team>`__.
- Attach the public SSH key from your project on Read the Docs to the GitHub user you just created

  - Go to the user's settings
  - Click on :guilabel:`SSH and GPG keys`
  - Click on :guilabel:`New SSH key`
  - Put a descriptive title and paste the :ref:`public SSH key from your Read the Docs project <guides/private-submodules:Project's SSH key>`
  - Click on :guilabel:`Add SSH key`

Refer to the `GitHub documentation <https://developer.github.com/v3/guides/managing-deploy-keys/#machine-users>`__ for more information about machine users.

GitLab
------

For GitLab, Read the Docs uses `deploy keys with read only access <https://docs.gitlab.com/ee/ssh/#deploy-keys>`__.
GitLab allows you to reuse a deploy key across different repositories.
Since Read the Docs already added the public SSH key on your main repository,
you only need to add it to each repository of your submodules.

- Go to the project's settings on GitLab
- Click on :guilabel:`Repository`
- Expand the ``Deploy Keys`` section
- Put a descriptive title and paste the :ref:`public SSH key from your Read the Docs project <guides/private-submodules:Project's SSH key>`
- Click on :guilabel:`Add key`
- Repeat the previous steps for each submodule.

Bitbucket
---------

For Bitbucket, Read the Docs uses `access keys with read only access <https://confluence.atlassian.com/bitbucket/access-keys-294486051.html>`__.
Bitbucket allows you to reuse an access key across different repositories.
Since Read the Docs already set the public SSH key on your main repository,
you only need to add it to each repository of your submodules.

- Go to the project's settings on Bitbucket
- Click on :guilabel:`Access keys`
- Click on :guilabel:`Add key`
- Put a descriptive label and paste the :ref:`public SSH key from your Read the Docs project <guides/private-submodules:Project's SSH key>`
- Click on :guilabel:`Add key`
- Repeat the previous steps for each submodule.

Others
------

If you are not using any of the above providers.
Read the Docs will still generate a pair of SSH keys.
You'll need to add the :ref:`public SSH key from your Read the Docs project <guides/private-submodules:Project's SSH key>`
to the main repository and each of its submodules.
Refer to your provider's documentation for the steps.
