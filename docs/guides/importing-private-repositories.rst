Manually Importing Private Repositories
=======================================

.. warning::

   This guide is for users of :doc:`/commercial/index`.
   **If you are using GitHub, GitLab, or Bitbucket**,
   we recommend :doc:`connecting your account </connected-accounts>` and importing your project from
   https://readthedocs.com/dashboard/import instead of importing it manually.

If you are using an unsupported integration, or don't want to connect your account,
you'll need to do some **extra steps in order to have your project working**.

#. **Manually import your project using an SSH URL**
#. **Allow access to your project using an SSH key**
#. **Setup a webhook to build your documentation on every commit**

.. contents:: Table of contents
   :local:
   :backlinks: none
   :depth: 3

Importing your project
----------------------

#. Go to https://readthedocs.com/dashboard/import/manual/
#. Fill the :guilabel:`Repository URL` field with the SSH form of your repository's URL,
   e.g ``git@github.com:readthedocs/readthedocs.org.git``
#. Fill the other required fields
#. Click :guilabel:`Next`

Giving access to your project with an SSH key
---------------------------------------------

After importing your project the build will fail,
because Read the Docs doesn't have access to clone your repository.
To give access, you'll need to add your project's public SSH key to your VCS provider.

Copy your project's public key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can find the public SSH key of your Read the Docs project by:

#. Going to the :guilabel:`Admin` tab of your project
#. Click on :guilabel:`SSH Keys`
#. Click on the fingerprint of the SSH key (it looks like ``6d:ca:6d:ca:6d:ca:6d:ca``)
#. Copy the text from the :guilabel:`Public key` section

.. note::

   The private part of the SSH key is kept secret.

Add the public key to your project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

GitHub
''''''

For GitHub, you can use
`deploy keys with read only access <https://docs.github.com/en/developers/overview/managing-deploy-keys#deploy-keys>`__.

#. Go to your project on GitHub
#. Click on :guilabel:`Settings`
#. Click on :guilabel:`Deploy Keys`
#. Click on :guilabel:`Add deploy key`
#. Put a descriptive title and paste the
   :ref:`public SSH key from your Read the Docs project <guides/importing-private-repositories:copy your project's public key>`
#. Click on :guilabel:`Add key`

GitLab
''''''

For GitLab, you can use `deploy keys with read only access <https://docs.gitlab.com/ee/user/project/deploy_keys/index.html>`__.

#. Go to your project on GitLab
#. Click on :guilabel:`Settings`
#. Click on :guilabel:`Repository`
#. Expand the :guilabel:`Deploy Keys` section
#. Put a descriptive title and paste the
   :ref:`public SSH key from your Read the Docs project <guides/importing-private-repositories:copy your project's public key>`
#. Click on :guilabel:`Add key`

Bitbucket
'''''''''

For Bitbucket, you can use `access keys with read only access <https://confluence.atlassian.com/bitbucket/access-keys-294486051.html>`__.

#. Go your project on Bitbucket
#. Click on :guilabel:`Repository Settings`
#. Click on :guilabel:`Access keys`
#. Click on :guilabel:`Add key`
#. Put a descriptive label and paste the
   :ref:`public SSH key from your Read the Docs project <guides/importing-private-repositories:copy your project's public key>`
#. Click on :guilabel:`Add SSH key`

Azure DevOps
''''''''''''

For Azure DevOps, you can use `SSH key authentication <https://docs.microsoft.com/en-us/azure/devops/repos/git/use-ssh-keys-to-authenticate?view=azure-devops>`__.

#. Go your Azure DevOps page
#. Click on :guilabel:`User settings`
#. Click on :guilabel:`SSH public keys`
#. Click on :guilabel:`New key`
#. Put a descriptive name and paste the
   :ref:`public SSH key from your Read the Docs project <guides/importing-private-repositories:copy your project's public key>`
#. Click on :guilabel:`Add`

Others
''''''

If you are not using any of the above providers,
Read the Docs will still generate a pair of SSH keys.
You'll need to add the :ref:`public SSH key from your Read the Docs project <guides/importing-private-repositories:copy your project's public key>`
to your repository.
Refer to your provider's documentation for the steps required to do this.

Webhooks
--------

To build your documentation on every commit,
you'll need to manually add a webhook, see :doc:`/webhooks`.
If you are using an unsupported integration,
you may need to setup a custom integration
using our :ref:`generic webhook <webhooks:using the generic api integration>`.
