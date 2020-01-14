Link to Other Projects' Documentation With Intersphinx
======================================================

You may be familiar with using the :ref:`:ref: role <sphinx:ref-role>` to link to any location of your docs.
It helps you to keep all links within your docs up to date and warns you if a reference target moves or changes
so you can ensure that your docs don't have broken cross-references.

Some times you may need to link to a location of another documentation project.
We could just link to where the documentation is hosted,
and use Sphinx's ``linkcheck`` builder to check for broken links.

Another way is using :doc:`Intersphinx <sphinx:usage/extensions/intersphinx>`.
Intersphinx allows you to use all :ref:`cross-reference roles <sphinx:xref-syntax>` from Sphinx with objects in other projects.
That is, you could use the ``:ref:`` role to link to sections of other documentation projects.
Sphinx will ensure that your cross-references to the other project exist and will raise a warning if they are deleted or changed so you can keep your docs up to date.

Using Intersphinx
-----------------

To use Intersphinx you need to add it to the list of extensions in your ``conf.py`` file.


.. code:: python

   # conf.py file

   extensions = [
       'sphinx.ext.intersphinx',
   ]

And use the ``intersphinx_mapping`` configuration to indicate the name and link of the projects you want to use.

.. code:: python

   # conf.py file

   intersphinx_mapping = {
       'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
   }


Now we can use the ``sphinx`` name with a cross-reference role:

.. code:: rst

   - :ref:`sphinx:ref-role`
   - :ref:`:ref: role <sphinx:ref-role>`
   - :doc:`sphinx:usage/extensions/intersphinx`
   - :doc:`Intersphinx <sphinx:usage/extensions/intersphinx>`

Result:

- :ref:`sphinx:ref-role`
- :ref:`:ref: role <sphinx:ref-role>`
- :doc:`sphinx:usage/extensions/intersphinx`
- :doc:`Intersphinx <sphinx:usage/extensions/intersphinx>`

Intersphinx in Read the Docs
----------------------------

You can use Intersphinx to link to subprojects, translations, another version or any other project hosted in Read the Docs.
For example:

.. code:: python

   # conf.py file

   intersphinx_mapping = {
       # Links to "v2" version of the "docs" project.
       'docs-v2': ('https://docs.readthedocs.io/en/v2', None),
       # Links to the French translation of the "docs" project.
       'docs-fr': ('https://docs.readthedocs.io/fr/latest', None),
       # Links to the "apis" subproject of the "docs" project.
       'sub-apis': ('https://docs.readthedocs.io/projects/apis/en/latest', None),
   }

Intersphinx with private projects
---------------------------------

If you are using :doc:`/commercial/index`,
Intersphinx will not be able to fetch the inventory file from private docs.

Intersphinx supports `URLs with Basic Authorization <https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#using-intersphinx-with-inventory-file-under-basic-authorization>`__,
which Read the Docs supports :ref:`using a token <commercial/sharing:Basic Authorization>`.
You need to generate a token for each project you want to use with Intersphinx.

#. Go the project you want to use with Intersphinx
#. Click :guilabel:`Admin` > :guilabel:`Sharing`
#. Select ``HTTP Header Token``
#. Set an expiration date long enough to use the token when building your project
#. Click on ``Share!``.

Now we can add the link to the private project with the token like:

.. code:: python

   # conf.py file

   intersphinx_mapping = {
       # Links to a private project named "docs"
       'docs': ('https://<token-for-docs>:@readthedocs-docs.readthedocs-hosted.com/en/latest', None),
       # Links to the private French translation of the "docs" project
       'docs': ('https://<token-for-fr-translation>:@readthedocs-docs.readthedocs-hosted.com/fr/latest', None),
       # Links to the private "apis" subproject of the "docs" project
       'docs': ('https://<token-for-apis>:@readthedocs-docs.readthedocs-hosted.com/projects/apis/en/latest', None),
   }


.. note::

   Sphinx will strip the token from the URLs when generating the links.

You can use your tokens with environment variables,
so you don't have to hard code them in your ``conf.py`` file.
See :doc:`/guides/environment-variables` to use environment variables inside Read the Docs.

For example,
if you create an environment variable named ``RTD_TOKEN_DOCS`` with the token from the "docs" project.
You can use it like this:

.. code:: python

   # conf.py file

   import os
   RTD_TOKEN_DOCS = os.environ.get('RTD_TOKEN_DOCS')

   intersphinx_mapping = {
       # Links to a private project named "docs"
       'docs': (f'https://{RTD_TOKEN_DOCS}:@readthedocs-docs.readthedocs-hosted.com/en/latest', None),
   }

.. note::

   Another way of using Intersphinx with private projects is to download the inventory file and keep it in sync when the project changes.
   The inventory file is by default located at ``objects.inv``, for example ``https://readthedocs-docs.readthedocs-hosted.com/en/latest/objects.inv``.

   .. code:: python
      
      # conf.py file

      intersphinx_mapping = {
          # Links to a private project named "docs" using a local inventory file.
          'docs': ('https://readthedocs-docs.readthedocs-hosted.com/en/latest', 'path/to/local/objects.inv'),
      }
