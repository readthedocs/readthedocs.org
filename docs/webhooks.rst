Webhooks
========

Webhooks are pretty amazing, and help to turn the web into a push instead of
pull platform. We have support for hitting a URL whenever you commit to your
project and we will try and rebuild your docs. This only rebuilds them if
something has changed, so it is cheap on the server side. As anyone who has
worked with push knows, pushing a doc update to your repo and watching it get
updated within seconds is an awesome feeling.

GitHub
---------

If your project is hosted on GitHub, you can easily add a hook that will rebuild
your docs whenever you push updates:

* Go to the "Settings" page for your project
* Click "Integrations & Services"
* In the "Services" section, click "Add service"
* In the list of available services, click "ReadTheDocs"
* Leave "Active" checked
* Click "Add service"

.. note:: The GitHub URL in your Read the Docs project must match the URL on GitHub. The URL is case-sensitive.

If you ever need to manually set the webhook on GitHub,
you can point it at ``https://readthedocs.org/github``.

Bitbucket
-----------

If your project is hosted on Bitbucket, you can easily add a hook that will rebuild
your docs whenever you push updates:

* Go to the "admin" page for your project
* Click "Services"
* In the available service hooks, select "Read the Docs"
* Click "Add service"

If you ever need to manually set the webhook on Bitbucket,
you can point it at ``https://readthedocs.org/bitbucket``.

Others
------

Your ReadTheDocs project detail page has your post-commit hook on it; it will
look something along the lines of ``http://readthedocs.org/build/<project_name>``.
Regardless of which revision control system you use, you can just hit this URL
to kick off a rebuild.

The following parameters available to customize the behavior of custom webhooks:

* ``'version_slug'``: The build version to trigger build for (defaults to ``'latest'``)

  Example::
  
      $ curl -X POST --data "version_slug=$VERSION" https://readthedocs.org/build/$PROJECT_NAME

You could make this part of a hook using Git_, Subversion_, Mercurial_, or
Bazaar_, perhaps through a simple script that accesses the build URL using
``wget`` or ``curl``.

.. _Git: http://www.kernel.org/pub/software/scm/git/docs/githooks.html
.. _Subversion: http://mikewest.org/2006/06/subversion-post-commit-hooks-101
.. _Mercurial: http://hgbook.red-bean.com/read/handling-repository-events-with-hooks.html
.. _Bazaar: http://wiki.bazaar.canonical.com/BzrHooks
