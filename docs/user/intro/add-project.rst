Adding a documentation project
==============================

.. meta::
   :description lang=en: Add your existing documentation from a Git repository into Read the Docs.

This page takes you through the process of adding a documentation project to Read the Docs.
If you have :doc:`connected your Read the Docs account </guides/connecting-git-account>` to GitHub, Bitbucket, or GitLab,
and you have admin access to the repository you want to add,
you will be able to add your project automatically.
Otherwise, you will need to add it manually and perform some extra steps.

Automatically add your project
------------------------------

#. Go to your :term:`dashboard`.
#. Click on :guilabel:`Add project`.
#. Type the name of the repository you want to add and click on it.
   If you are using our :ref:`reference/git-integration:GitHub App`,
   make sure you have installed the :ref:`Read the Docs GitHub App <reference/git-integration:Troubleshooting>` in your repository.
#. Click on :guilabel:`Continue`.
#. Edit any of the pre-filled fields with information of the repository.
#. Click on :guilabel:`Next`.
#. Add a :term:`configuration file` to your repository if it doesn't exist yet.
#. Click on :guilabel:`This file exists`.

.. seealso::

   :doc:`/reference/git-integration`
      Your project will be automatically configured with a Git integration.
      Learn more about all the features enabled by that integration on this page.

Manually add your project
-------------------------

#. Go to your :term:`dashboard`.
#. Click on :guilabel:`Add project`.
#. Click on :guilabel:`Configure manually`.
#. Click on :guilabel:`Continue`.
#. Fill all the fields of the form.
#. Click on :guilabel:`Next`.
#. Add a :term:`configuration file` to your repository if it doesn't exist yet.
#. Click on :guilabel:`This file exists`.

Once your project is created, you'll need to manually configure the repository webhook if you would like to have new changes trigger builds for your project on Read the Docs.

.. seealso::

   :doc:`/guides/setup/git-repo-manual`
      Additional setup steps required for manually created projects. This guide covers setting up SSH keys and webhook integrations.

What's next
-----------

Once your documentation project is created, a build will be triggered.
It will automatically fetch the code from your repository and build the documentation.
You can see the logs for the build process from your :term:`dashboard`.

.. seealso::

   :doc:`/builds`
      Explanation about the build process.

   :doc:`/config-file/index`
      Practical steps to add a configuration file to your documentation project.

   :doc:`/versions`
      Manage multiple versions of your documentation project.

If you have any trouble, don't hesitate to reach out to us.
The :doc:`support </support>` page has more information on getting in touch.
