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

If your custom stylesheet is ``_static/css/custom.css``,
you can add that CSS file to the documentation using the
Sphinx option `html_css_files`_::

    ## conf.py

    # These folders are copied to the documentation's HTML output
    html_static_path = ['_static']

    # These paths are either relative to html_static_path
    # or fully qualified paths (eg. https://...)
    html_css_files = [
        'css/custom.css',
    ]


A similar approach can be used to add JavaScript files::

    html_js_files = [
        'js/custom.js',
    ]



.. _html_css_files: https://www.sphinx-doc.org/page/usage/configuration.html#confval-html_css_files

.. note::

    The Sphinx HTML options ``html_css_files`` and ``html_js_files``
    where added in Sphinx 1.8.
    Unless you have a good reason to use an older version,
    you are strongly encouraged to upgrade.
    Sphinx is almost entirely backwards compatible.


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
