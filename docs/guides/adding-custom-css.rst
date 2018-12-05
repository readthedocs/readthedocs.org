Adding Custom CSS or JavaScript to a Sphinx Project
===================================================

The easiest way to add custom stylesheets or scripts, and ensure that the files
are added in a way that allows for overriding of existing styles or scripts, is
to add these files using a ``conf.py`` Sphinx extension. Inside your
``conf.py``, if a function ``setup(app)`` exists, Sphinx will call this function
as a normal extension during application setup.

For example, if a custom stylesheet exists at ``_static/css/custom.css``, a
``conf.py`` extension can be written to add this file to the list of
stylesheets::

    def setup(app):
        app.add_stylesheet('css/custom.css')

Using an extension to add the stylesheet allows for the file to be added to the
list of stylesheets later in the Sphinx setup process, making overriding parts
of the Read the Docs theme possible.

The same method can be used to add additional scripts that might override
previously initialized scripts::

    def setup(app):
        app.add_javascript('js/custom.js')
