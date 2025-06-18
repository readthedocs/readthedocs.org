URL versioning schemes
======================

The URL versioning scheme of your project defines the URL of your documentation,
and if your project supports multiple versions or translations.

Read the Docs supports three different versioning schemes:

- `Multiple versions with translations`_.
- `Multiple versions without translations`_.
- `Single version without translations`_.

.. seealso::

   :doc:`/versions`
     General explanation of how versioning works on Read the Docs.

Multiple versions with translations
-----------------------------------

This is the default versioning scheme, it's the recommend one if your project has multiple versions,
and has or plans to support translations.

The URLs of your documentation will look like:

- ``/en/latest/``
- ``/en/1.5/``
- ``/es/latest/install.html``
- ``/es/1.5/contributing.html``

Multiple versions without translations
--------------------------------------

Use this versioning scheme if you want to have multiple versions of your documentation,
but don't want to have translations.

The URLs of your documentation will look like:

- ``/latest/``
- ``/1.5/install.html``

.. warning::

   This means you can't have translations for your documentation.

Single version without translations
-----------------------------------

Having a single version of a documentation project can be considered the better choice
in cases where there should only always exist one unambiguous copy of your project.
For example:

- A research project may wish to *only* expose readers to their latest list of publications and research data.
- A :abbr:`SaaS (Software as a Service)` application might only ever have one version live.

The URLs of your documentation will look like:

- ``/``
- ``/install.html``

.. warning::

   This means you can't have translations or multiple versions for your documentation.

How to change the URL versioning scheme of your project
-------------------------------------------------------

Changing the versioning scheme of your project will affect the URLs of your documentation,
any existing links to your documentation will break.
If you want to keep the old URLs working, you can create :doc:`redirects </user-defined-redirects>`.

#. Go the :guilabel:`Admin` tab of your project.
#. Click on :guilabel:`Settings`.
#. Select the new versioning scheme in the :guilabel:`URL versioning scheme` dropdown.
#. Click on :guilabel:`Save`.
