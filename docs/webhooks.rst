Webhooks
========

Web hooks are pretty amazing, and help to turn the web into a push instead of
pull platform. We have support for hitting a URL whenever you commit to your
project and we will try and rebuild your docs. This only rebuilds them if
something has changed, so it is cheap on the server side. As anyone who has
worked with push knows, pushing a doc update to your repo and watching it get
updated within seconds is an awesome feeling.

Github
---------

If your project is hosted on Github, you can easily add a hook that will rebuild
your docs whenever you push updates:

* Go to the "admin" page for your project
* Click "Service Hooks"
* In the available service hooks, click "ReadTheDocs"
* Check "Active"
* Click "Update Settings"

Bitbucket
-----------

If your project is hosted on Bitbucket, you can easily add a hook that will rebuild
your docs whenever you push updates:

* Go to the "admin" page for your project
* Click "Services"
* In the available service hooks, click "POST"
* Put "http://readthedocs.org/bitbucket" as the URL
* Click "Save Settings"

Others
------

Your ReadTheDocs project detail page has your post-commit hook on it; it will
look something along the lines of ``http://readthedocs.org/build/<pk>``.
Regardless of which revision control system you use, you can just hit this URL
to kick off a rebuild.

You could make this part of a hook using Git_, Subversion_, Mercurial_, or
Bazaar_, perhaps through a simple script that accesses the build URL using
``wget`` or ``curl``.

.. _Git: http://www.kernel.org/pub/software/scm/git/docs/githooks.html
.. _Subversion: http://mikewest.org/2006/06/subversion-post-commit-hooks-101
.. _Mercurial: http://hgbook.red-bean.com/read/handling-repository-events-with-hooks.html
.. _Bazaar: http://wiki.bazaar.canonical.com/BzrHooks
