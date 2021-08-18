Read the Docs tutorial
======================

In this tutorial you will create a documentation project on Read the Docs
by importing an Sphinx project from a GitHub repository,
tailor its configuration, and explore several useful features of the platform.

The tutorial is aimed at people interested in learning
how to use Read the Docs to host their documentation projects.
You will fork a fictional software library
similar to the one developed in the :doc:`official Sphinx tutorial <sphinx:tutorial/index>`.
No prior experience with Sphinx is required,
and you can follow this tutorial without having done the Sphinx one.

The only things you will need to follow the are
a web browser, an Internet connection, and a GitHub account
(you can `register for a free account <https://github.com/signup>`_ if you don't have one).
You will use Read the Docs Community, which means that the project will be public.

Getting started
---------------

Preparing your project on GitHub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To start, `sign in to GitHub <https://github.com/login>`_
and navigate to `the tutorial GitHub template <https://github.com/astrojuanlu/tutorial-template/>`_,
where you will see a green "Use this template" button.
Click it to open a new page that will ask you for some details:

* Leave the default "Owner", or optionally change it if you desire.
* Introduce an appropriate "Repository name", for example ``rtd-tutorial``.
* Make sure the project is "Public", rather than "Private".

.. figure:: /_static/images/tutorial/github-template.png
   :width: 80%
   :align: center
   :alt: GitHub template for the tutorial

   GitHub template for the tutorial

After that, click on the green "Create repository from template" button,
which will generate a new repository on your personal account
(or the one of your choosing).
This is the repository you will import on Read the Docs,
and it contains the following files:

``README.rst``
  Basic description of the repository, you will leave it untouched.

``pyproject.toml``
  Python project metadata that makes it installable.
  Useful for automatic documentation generation from sources.

``lumache.py``
  Source code of the fictional Python library.

``docs/``
  Directory holding all the Sphinx documentation sources,
  including some required dependencies in ``docs/requirements.txt``,
  the Sphinx configuration ``docs/source/conf.py``,
  and the root document ``docs/source/index.rst`` written in reStructuredText.

Sign up for Read the Docs
~~~~~~~~~~~~~~~~~~~~~~~~~

To sign up for a Read the Docs account,
navigate to the `Sign Up page <https://readthedocs.org/accounts/signup/>`_
and choose the option "Sign up with GitHub".
On the authorization page, click the green "Authorize readthedocs" button.

.. figure:: /_static/images/tutorial/github-authorization.png
   :width: 60%
   :align: center
   :alt: GitHub authorization page

   GitHub authorization page

.. note::

   Read the Docs needs elevated permissions to perform certain operations
   that ensure that the workflow is as smooth as possible,
   like installing webhooks.
   If you want to learn more,
   check out :ref:`connected-accounts:permissions for connected accounts`.

After that, you will be redirected to Read the Docs,
where you will need to confirm your e-mail and username.
Clicking the "Sign Up »" button will create your account
and redirect you to your *dashboard*.

By now, you should have two email notifications:

* One from GitHub, telling you that "A third-party OAuth application ...
  was recently authorized to access your account". You don't need to do
  anything about it.
* Another one from Read the Docs, prompting you to "verify your email
  address". Click on the link to finalize the process.

Finally, you created your account on Read the Docs
and are ready to import your first project.

Welcome!

.. figure:: /_static/images/tutorial/rtd-empty-dashboard.png
   :width: 80%
   :align: center
   :alt: Read the Docs empty dashboard

   Read the Docs empty dashboard

.. note::

   Our commercial site offers some extra features,
   like support for private projects.
   You can learn more about :doc:`our two different sites </choosing-a-site>`.
