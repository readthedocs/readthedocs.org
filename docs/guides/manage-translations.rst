Manage Translations
===================

This guide walks through the process needed to manage translations of your documentation.
Once this work is done, you can setup your project under Read the Docs to build each language of your documentation by reading :doc:`/localization`.

Overview
--------

There are many different ways to manage documentation in multiple languages by using different tools or services.
All of them have their pros and cons depending on the context of your project or organization.

In this guide we will focus our efforts around two different methods: manual and using Transifex_.

In both methods, we need to follow these steps to translate our documentation:

#. Create translatable files (``.pot`` and ``.po`` extensions) from source language
#. Translate the text on those files from source language to target language
#. Build the documentation in *target language* using the translated texts

Besides these steps, once we have published our first translated version of our documentation,
we will want to keep it updated from the source language. At that time, the workflow would be:

#. Update our translatable files from source language
#. Translate only *new* and *modified* texts in source language into target language
#. Build the documentation using the most up to date translations


Create translatable files
-------------------------

To generate these ``.pot`` files it's needed to run this command from your ``docs/`` directory:

.. code-block:: console

   $ sphinx-build -b gettext . _build/gettext


.. tip::

   We recommend configuring Sphinx to use :ref:`gettext_uuid <sphinx:gettext_uuid>` as ``True``
   and also :ref:`gettext_compact <sphinx:gettext_compact>` as ``False`` to generate ``.pot`` files.


This command will leave the generated files under ``_build/gettext``.


Translate text from source language
-----------------------------------

Manually
~~~~~~~~

We recommend using `sphinx-intl`_ tool for this workflow.

.. _sphinx-intl: https://pypi.org/project/sphinx-intl/

First, you need to install it:

.. code-block:: console

   $ pip install sphinx-intl


As a second step, we want to create a directory with each translated file per target language
(in this example we are using Spanish/Argentina and Portuguese/Brazil).
This can be achieved with the following command:

.. code-block:: console

   $ sphinx-intl update -p _build/gettext -l es_AR -l pt_BR

This command will create a directory structure similar to the following
(with one ``.po`` file per ``.rst`` file in your documentation)::

  locale
  ├── es_AR
  │   └── LC_MESSAGES
  │       └── index.po
  └── pt_BR
      └── LC_MESSAGES
          └── index.po


Now, you can just open those ``.po`` files with a text editor and translate them taking care of no breaking the reST notation.
Example:

.. code-block:: po

   # b8f891b8443f4a45994c9c0a6bec14c3
   #: ../../index.rst:4
   msgid ""
   "Read the Docs hosts documentation for the open source community."
   "It supports :ref:`Sphinx <sphinx>` docs written with reStructuredText."
   msgstr ""
   "FILL HERE BY TARGET LANGUAGE FILL HERE BY TARGET LANGUAGE FILL HERE "
   "BY TARGET LANGUAGE :ref:`Sphinx <sphinx>` FILL HERE."


Using Transifex
~~~~~~~~~~~~~~~

Transifex_ is a platform that simplifies the manipulation of ``.po`` files and offers many useful features to make the translation process as smooth as possible.
These features includes a great web based UI, `Translation Memory`_, collaborative translation, etc.

.. _Transifex: https://www.transifex.com/
.. _Translation Memory: https://docs.transifex.com/setup/translation-memory

You need to create an account in their service and a new project before start.

After that, you need to install the `transifex-client`_ tool which will help you in the process to upload source files, update them and also download translated files.
To do this, run this command:

.. _transifex-client: https://docs.transifex.com/client/introduction

.. code-block:: console

   $ pip install transifex-client

After installing it, you need to configure your account.
For this, you need to create an API Token for your user to access this service through the command line.
This can be done under your `User's Settings`_.

.. _User's Settings: https://www.transifex.com/user/settings/api/


Now, you need to setup it to use this token:

.. code-block:: console

   $ tx init --token $TOKEN --no-interactive


The next step is to map every ``.pot`` file you have created in the previous step to a resource under Transifex.
To achieve this, you need to run this command:

.. code-block:: console

   $ tx config mapping-bulk \
       --project $TRANSIFEX_PROJECT \
       --file-extension '.pot' \
       --source-file-dir docs/_build/gettext \
       --source-lang en \
       --type PO \
       --expression 'locale/<lang>/LC_MESSAGES/{filepath}/{filename}.po' \
       --execute

This command will generate a file at ``.tx/config`` with all the information needed by the ``transifext-client`` tool to keep your translation synchronized.

Finally, you need to upload these files to Transifex platform so translators can start their work.
To do this, you can run this command:

.. code-block:: console

   $ tx push --source


Now, you can go to your Transifex's project and check that there is one resource per ``.rst`` file of your documentation.
After the source files are translated using Transifex, you can download all the translations for all the languages by running:

.. code-block:: console

   $ tx pull --all

This command will leave the ``.po`` files needed for building the documentation in the target language under ``locale/<lang>/LC_MESSAGES``.

.. warning::

   It's important to use always the same method to translate the documentation and do not mix them.
   Otherwise, it's very easy to end up with inconsistent translations or losing already translated text.


Build the documentation in target language
------------------------------------------


Finally, to build our documentation in Spanish(Argentina) we need to tell Sphinx builder the target language with the following command:

.. code-block:: console

   $ sphinx-build -b html -D language=es_AR . _build/html/es_AR

.. note::

   There is no need to create a new ``conf.py`` to redefine the ``language`` for the Spanish version of this documentation.

After running this command, the Spanish(Argentina) version of your documentation will be under ``_build/html/es_AR``.


Summary
-------

Update sources to be translated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have done changes in your documentation, you may want to make these additions/modifications available for translators so they can update it:

#. Create the ``.pot`` files:

   .. code-block:: console

      $ sphinx-build -b gettext . _build/gettext


.. For the manual workflow, we need to run this command

      $ sphinx-intl update -p _build/gettext -l es_AR -l pt_BR


#. Push new files to Transifex

   .. code-block:: console

      $ tx push --sources


Build documentation from up to date translation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When translators have finished their job, you may want to update the documentation by pulling the changes from Transifex:

#. Pull up to date translations from Transifex:

   .. code-block:: console

      $ tx pull --all

#. Commit and push these changes to our repo

   .. code-block:: console

      $ git add locale/
      $ git commit -m "Update translations"
      $ git push

The last ``git push`` will trigger a build per translation defined as part of your project under Read the Docs and make it immediately available.
