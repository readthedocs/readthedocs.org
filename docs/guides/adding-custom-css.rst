Adding Custom CSS or JavaScript to Sphinx Documentation
=======================================================

.. meta::
   :description lang=en:
       How to add additional CSS stylesheets or JavaScript files
       to your Sphinx documentation
       to override your Sphinx theme or add interactivity with JavaScript.

Adding additional CSS or JavaScript files to your Sphinx documentation
can let you customize the look and feel of your docs
or add additional functionality.
For example, with a small snippet of CSS,
your documentation could use a custom font or have a different background color.

If a custom stylesheet exists at ``_static/css/custom.css``,
you can add that CSS file to the documentation using the
:meth:`~sphinx:sphinx.application.Sphinx.add_css_file` method::

    ## conf.py

    ...

    # These folders are copied to the documentation's HTML output
    html_static_path = ['_static']

    ...

    def setup(app):
        # This path must exist relative to html_static_path
        app.add_css_file('css/custom.css')


A similar approach can be used to add JavaScript files::

    def setup(app):
        app.add_js_file('js/custom.js')


Unless you are already overriding some Sphinx functionality,
the ``setup()`` method may not exist in your ``conf.py`` file.
If it doesn't exist, add it to the end of your ``conf.py``
and Sphinx will call this method during the build process.
Congratulations, you've technically created
your first :ref:`Sphinx Extension <sphinx:dev-extensions>`!

.. note::

    The Sphinx APIs :meth:`~sphinx:sphinx.application.Sphinx.add_css_file`
    and :meth:`~sphinx:sphinx.application.Sphinx.add_js_file`
    where renamed in Sphinx 1.8 from ``add_stylesheet()`` and ``add_javascript()``.


Overriding or replacing a theme's stylesheet
--------------------------------------------

The above approach is preferred for adding additional stylesheets or JavaScript,
but it is also possible to completely replace a Sphinx theme's stylesheet
with your own stylesheet.

If your replacement stylesheet exists at ``_static/css/yourtheme.css``,
you can replace your theme's CSS file by setting ``html_style`` in your ``conf.py``::

    ## conf.py

    html_style = 'css/yourtheme.css'

If you only need to override a few styles on the theme,
you can include the theme's normal CSS using the CSS
`@import rule <https://developer.mozilla.org/en-US/docs/Web/CSS/@import>`_ .

.. code-block:: css

    /** css/yourtheme.css **/

    /* This line is theme specific - it includes the base theme CSS */
    @import '../alabaster.css';  /* for Alabaster */
    /*@import 'theme.css';       /* for the Read the Docs theme */

    body {
        /* ... */
    }
