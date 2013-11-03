Read the Docs Theme
===================

.. image:: /img/screen_mobile.png

By default, Read the Docs will use its own custom sphinx theme unless you set one yourself
in your ``conf.py`` file. Likewise, setting the theme to ``default`` will accomplish the
same behavior. The theme can be found on `github here`_ and is meant to work
independently of Read the Docs itself if you want to just use the theme locally.

This `blog post`_ provides some info about the design, but
in short, the theme aims to solve the limitations of Sphinx's default navigation setup,
where only a small portion of your docs were accessible in the sidebar. Our theme is also
meant to work well on mobile and tablet devices.

If you have issues or feedback, please `open an issue`_ on the theme's GitHub repository
which itself is a submodule within the larger RTD codebase.

How the Table of Contents builds
--------------------------------

Currently the left menu will build based upon any ``toctree(s)`` defined in your ``index.rst`` file.
It outputs 2 levels of depth, which should give your visitors a high level of access to your
docs. If no toctrees are set in your index.rst file the theme reverts to sphinx's usual
local toctree which is based upon the heading set on your current page.

It's important to note that if you don't follow the same styling for your rST headers across
your documents, the toctree will misbuild, and the resulting menu might not show the correct
depth when it renders.

Other style notes
-----------------

* As a responsive style, your should not set a height and width to your images.
* Wide tables will add a horizontal scroll bar to maintain the responsive layout.

.. _github here: https://www.github.com/snide/sphinx_rtd_theme
.. _blog post: http://ericholscher.com/blog/2013/nov/4/new-theme-read-the-docs/
.. _open an issue: https://github.com/snide/sphinx_rtd_theme/issues
