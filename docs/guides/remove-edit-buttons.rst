Removing "Edit on ..." Buttons from Documentation
=================================================

When building your documentation, Read the Docs automatically adds buttons at
the top of your documentation that point readers to your repository to make
changes. For instance, if your repository is on GitHub, a button that says "Edit
on GitHub" is added to your documentation to make it easy for readers to author
new changes.

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

Now when you build your documentation, your documentation won't include an edit
button or links to the page source.
