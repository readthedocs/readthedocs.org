Contrib
=======

Building development Docker image
---------------------------------

If you run Linux, you likely need to build a local Docker image that extends our
default image::

    contrib/docker_build.sh latest

Running Read the Docs via Supervisord
-------------------------------------

This is the easiest way to start all of the commands you'll need for development
in an environment relatively close to the production evironment. All you need is
``supervisord`` and ``redis-server``. Installation of ``redis-server`` is
outside the scope of this documentation, but once installed, all you need to run
from ``supervisord`` is::

    pip install supervisor
    cd contrib/
    supervisord

This will bring up a web instance for the dashboard, a web instance for
documentation serving, two celery instances, and redis-server. 

If you already are running redis-server, this will complain about the port
already being in use, but will still load.

Debugging
---------

To debug, set trace points like normal, with ``pdb``/``ipdb``. Then you can
connect to the process by bringing it to the foreground::

    supervisorctl fg main

You'll still see logging to STDERR on the main supervisord process page.
