Removing "Edit on ..." Buttons from Documentation
=================================================

When building your documentation, Read the Docs automatically adds buttons at
the top of your documentation and in the versions menu that point readers to your repository to make
changes. For instance, if your repository is on GitHub, a button that says "Edit
on GitHub" is added in the top-right corner to your documentation to make it easy for readers to author
new changes.


Remove links from top-right corner
----------------------------------

The only way to remove these links currently is to override the Read the Docs
theme templates:

* In your Sphinx project path, create a directory called ``_templates``. If you
  use a different ``templates_path`` option in your ``conf.py``, substitute that
  directory name.
* Create a file in this path called ``breadcrumbs.html``

The new ``breadcrumbs.html`` should look like this::

    {%- extends "sphinx_rtd_theme/breadcrumbs.html" %}

    {% block breadcrumbs_aside %}
    {% endblock %}


Remove "On ..." section from versions menu
------------------------------------------

This section can be removed with a custom CSS rule to hide them.
Follow the instructions under :doc:`adding-custom-css` and put the following content into the ``.css`` file:

.. code-block:: css

   /* Hide "On GitHub" section from versions menu */
   div.rst-versions > div.rst-other-versions > div.injected > dl:nth-child(4) {
       display: none;
   }


.. warning::

   You may need to change the ``4`` number in ``dl:nth-child(4)`` for a different one in case your project has more sections in the versions menu.
   For example, if your project has translations into different languages, you will need to use the number ``5`` there.

Now when you build your documentation, your documentation won't include an edit
button or links to the page source.
