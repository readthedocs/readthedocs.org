Adding a documentation project
==============================

.. meta::
   :description lang=en: Add your existing technical documentation from version control system into Read the Docs.

This page drives you through the process to add a documentation project to Read the Docs.
If you have :doc:`connected your Read the Docs account </guides/connecting-git-account>` to GitHub, Bitbucket or GitLab you will be able to add your project automatically.
Otherwise, you will need to add it manually and perform some extra steps.

Automatically
-------------

#. Go to your :term:`dashoard`.
#. Click on :guilabel:`Add project`.
#. Type the name of the respository you want to add and click on it.
#. Click on :guilabel:`Continue`.
#. Edit any of the pre-filled fields with information of the repository.
#. Click on :guilabel:`Next`.
#. Add a :term:`configuration file` to your repository if it's doesn't exist yet.
#. Click on :guilabel:`This file exists`.

Manually
--------

#. Go to your :term:`dashoard`.
#. Click on :guilabel:`Add project`.
#. Click on :guilabel:`Configure manually`.
#. Click on :guilabel:`Continue`.
#. Fill all the fields of the form.
#. Click on :guilabel:`Next`.
#. Add a :term:`configuration file` to your repository if it's doesn't exist yet.
#. Click on :guilabel:`This file exists`.

Once your project is created, you'll need to manually configure the repository webhook if you would like to have new changes trigger builds for your project on Read the Docs.

.. seealso::

   :doc:`/guides/setup/git-repo-manual`
      Once you have imported your Git project, use this guide to manually set up basic and additional *webhook* integration.


What's next
-----------

Once your documentation project was created, a build is triggered.
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
