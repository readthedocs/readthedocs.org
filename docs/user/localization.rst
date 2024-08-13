Localization and Internationalization
======================================

In this article, we explain high-level approaches to internationalizing and localizing your documentation.

By default, Read the Docs assumes that your documentation is or *might become* multilingual one day.
The initial default language is English and
therefore you often see the initial build of your documentation published at ``/en/latest/``,
where the ``/en`` denotes that it's in English.
By having the ``en`` URL component present from the beginning,
you are ready for the eventuality that you would want a second language.

Read the Docs supports hosting your documentation in multiple languages.
Read below for the various approaches that we support.

.. contents::
    :local:

Projects with one language
--------------------------

If your documentation isn't in English (the default),
you should indicate which language you have written it in.

It is easy to set the *Language* of your project.
On the project *Admin* page (or *Import* page),
simply select your desired *Language* from the dropdown.
This will tell Read the Docs that your project is in the language.
The language will be represented in the URL for your project.

For example,
a project that is in Spanish will have a default URL of ``/es/latest/`` instead of ``/en/latest/``.

Projects with multiple translations (Sphinx-only)
-------------------------------------------------

.. seealso::

   :doc:`guides/manage-translations-sphinx`
     Describes the whole process for a documentation with multiples languages in the same repository and how to keep the translations updated on time.

This situation is a bit more complicated. Each language must have its own project. You will choose one to be the parent project, and add each of the other projects as "Translations" of the parent project. 

Let's use ``phpmyadmin`` as an example.

The ``phpmyadmin`` project is the parent. Each translation then has its own project, for example ``phpmyadmin-spanish``. The *Language* for ``phpmyadmin-spanish`` is set to ``Spanish``. Then, on the  *Translations* page of the ``phpmyadmin`` project, ``phpmyadmin-spanish`` is set as translation.

This has the results of serving:

* ``phpmyadmin`` at ``https://phpmyadmin.readthedocs.io/en/latest/``
* ``phpmyadmin-spanish`` at ``https://phpmyadmin.readthedocs.io/es/latest/``

It also gets included in the Read the Docs :term:`flyout menu`:

.. image:: /img/translation_bar.png

.. note::
    The default language of a custom domain is determined by the language of the
    parent project that the domain was configured on. See
    :doc:`/custom-domains` for more information.

.. note:: You can include multiple translations in the same repository,
          with same ``conf.py`` and ``.rst`` files,
          but each project must specify the language to build for those docs.

.. note:: You must commit the ``.po`` files for Read the Docs to translate your documentation.


Translation workflows
~~~~~~~~~~~~~~~~~~~~~

When you work with translations,
the workflow of your translators becomes a critical component.

Considerations include:

* Are your translators able to use a git workflow? For instance, are they able to translate directly via GitHub?
* Do you benefit from machine translation?
* Do you need different roles, for instance do you need translators and editors?
* What is your source language?
* When are your translated versions published?

By using Sphinx and .po files,
you will be able to automatically synchronize between your documentation source messages on your git platform and your translation platform.

There are many translation platforms that support this workflow.
These include:

* `Weblate <https://weblate.org/>`_
* `Transifex <https://www.transifex.com/>`_
* `Crowdin <https://crowdin.com/>`_

Because Read the Docs builds your git repository,
you can use any of the above solutions.
Any solution that synchronizes your translations with your git repository
will ensure that your translations are automatically published with Read the Docs.
