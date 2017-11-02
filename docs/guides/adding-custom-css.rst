Adding Custom CSS
=================

The easiest way to add custom stylesheets, and ensure that the files are added
in a way that allows for overriding styles of the Read the Docs theme, is to add
these files using a ``conf.py`` Sphinx extension.

Inside your ``conf.py``, if a function ``setup(app)`` exists, Sphinx will call
this function as a normal extension during application setup. Given you have a
custom stylesheet ``_static/css/custom.css``, you can write a ``conf.py``
extension like::

    def setup(app):
        app.add_stylesheet('css/custom.css')

Using an extension to add the stylesheet allows for the file to be added to the
list of stylesheets later in the Sphinx setup process, making overriding parts
of the Read the Docs theme possible.
