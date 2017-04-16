=====================
Development Standards
=====================

Front End Development
=====================

Background
----------

.. note::

    Consider this the canonical resource for contributing Javascript and CSS. We
    are currently in the process of modernizing our front end development
    procedures. You will see a lot of different styles around the code base for
    front end JavaScript and CSS.

Our modern front end development stack includes the following tools:

* `Gulp`_
* `Bower`_
* `Browserify`_
* `Debowerify`_
* And soon, `LESS`_

We use the following libraries:

* `Knockout`_
* `jQuery`_
* Several jQuery plugins

Previously, JavaScript development has been done in monolithic files or inside
templates. jQuery was added as a global object via an include in the base
template to an external source. There are no standards currently to JavaScript
libraries, this aims to solve that.

The requirements for modernizing our front end code are:

* Code should be modular and testable. One-off chunks of JavaScript in templates
  or in large monolithic files are not easily testable. We currently have no
  JavaScript tests.
* Reduce code duplication.
* Easy JavaScript dependency management.

Modularizing code with `Browserify`_ is a good first step. In this development
workflow, major dependencies commonly used across JavaScript includes are
installed with `Bower`_ for testing, and vendorized as standalone libraries via
`Gulp`_ and `Browserify`_. This way, we can easily test our JavaScript libraries
against jQuery/etc, and have the flexibility of modularizing our code. See
`JavaScript Bundles`_ for more information on what and how we are bundling.

To ease deployment and contributions, bundled JavaScript is checked into the
repository for now. This ensures new contributors don't need an additional front
end stack just for making changes to our Python code base. In the future, this
may change, so that assets are compiled before deployment, however as our front
end assets are in a state of flux, it's easier to keep absolute sources checked
in.

Getting Started
---------------

You will need a working version of Node and NPM to get started. We won't cover
that here, as it varies from platform to platform.

To install these tools and dependencies::

    npm install

This will install locally to the project, not globally. You can install globally
if you wish, otherwise make sure ``node_modules/.bin`` is in your PATH.

Next, install front end dependencies::

    bower install

The sources for our bundles are found in the per-application path
``static-src``, which has the same directory structure as ``static``. Files in
``static-src`` are compiled to ``static`` for static file collection in Django.
Don't edit files in ``static`` directly, unless you are sure there isn't a
source file that will compile over your changes.

To test changes while developing, which will watch source files for changes and
compile as necessary, you can run `Gulp`_ with our development target::

    gulp dev

Once you are satisfied with your changes, finalize the bundles (this will
minify library sources)::

    gulp build

If you updated any of our vendor libraries, compile those::

    gulp vendor

Make sure to check in both files under ``static`` and ``static-src``.

Making Changes
--------------

If you are creating a new library, or a new library entry point, make sure to
define the application source file in ``gulpfile.js``, this is not handled
automatically right now.

If you are bringing in a new vendor library, make sure to define the bundles you
are going to create in ``gulpfile.js`` as well.

Tests should be included per-application, in a path called ``tests``, under the
``static-src/js`` path you are working in. Currently, we still need a test
runner that accumulates these files.

Deployment
----------

If merging several branches with JavaScript changes, it's important to do a
final post-merge bundle. Follow the steps above to rebundle the libraries, and
check in any changed libraries.

JavaScript Bundles
------------------

There are several components to our bundling scheme:

    Vendor library
        We repackage these using `Browserify`_, `Bower`_, and `Debowerify`_ to
        make these libraries available by a ``require`` statement.  Vendor
        libraries are packaged separately from our JavaScript libraries, because
        we use the vendor libraries in multiple locations. Libraries bundled
        this way with `Browserify`_ are available to our libraries via
        ``require`` and will back down to finding the object on the global
        ``window`` scope.

        Vendor libraries should only include libraries we are commonly reusing.
        This currently includes `jQuery` and `Knockout`. These modules will be
        excluded from libraries by special includes in our ``gulpfile.js``.

    Minor third party libraries
        These libraries are maybe used in one or two locations. They are
        installed via `Bower`_ and included in the output library file. Because
        we aren't reusing them commonly, they don't require a separate bundle or
        separate include. Examples here would include jQuery plugins used on one
        off forms, such as jQuery Payments.

    Our libraries
        These libraries are bundled up excluding vendor libraries ignored by
        rules in our ``gulpfile.js``. These files should be organized by
        function and can be split up into multiple files per application.

        Entry points to libraries must be defined in ``gulpfile.js`` for now. We
        don't have a defined directory structure that would make it easy to
        imply the entry point to an application library.

.. _`Bower`: http://bower.io
.. _`Gulp`: http://gulpjs.com
.. _`Browserify`: http://browserify.org
.. _`Debowerify`: https://github.com/eugeneware/debowerify
.. _`LESS`: http://lesscss.org

.. _`jQuery`: http://jquery.com
.. _`Knockout`: http://knockoutjs.com
