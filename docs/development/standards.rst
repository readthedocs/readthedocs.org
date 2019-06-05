Development Standards
=====================

These are build standards that are adhered to by the core development team while
developing Read the Docs and related services. If you are a new contributor to
Read the Docs, it might a be a good idea to follow these guidelines as well. The
:doc:`standard installation instructions <../install>` do cover what it takes to
get started with a local installation of Read the Docs and can be used for local
development by non-core team.

Core team standards
-------------------

Core team members expect to have a development environment that closely
approximates our production environment, in order to spot bugs and logical
inconsisencies before they make their way to production.

Celery runs as a separate process
    Celery needs to be run as a separate process, and core team will not use
    in-process task execution via Celery's ``ALWAYS_EAGER`` setting. The
    ``ALWAYS_EAGER`` setting doesn't work correctly, and masks bugs that
    introduce task execution race conditions.

Celery runs multiple processes
    We run celery with multiple worker processes to discover race conditions
    between tasks.

Docker for builds
    Docker is used for a build backend instead of the local host build backend.
    There are a number of differences between the two execution methods in how
    processes are executed, what is installed, and what can potentially leak
    thorugh and mask bugs -- for example, local SSH agent allowing code check
    not normally possible.

Setting ``USE_SUBDOMAIN = True``
    There are a number of resolution bugs and cross-domain behavior that can
    only be caught by using this setting. It requires use of a catch all public
    domain, so we can resolve all subdomains to ``localhost``. For example, here
    are some related settings that affect project URLs::

        PRODUCTION_DOMAIN = 'localhost:8000'
        PUBLIC_DOMAIN = 'dev.readthedocs.io:8001'
        USE_SUBDOMAIN = True

Postgres as a database
    Postgres sould be used as the default database whenever possible, as SQLite
    has issues with our Django version and we use Postgres in production.
    Differences between Postgres and SQLite should be masked for the most part,
    as Django does abstract database procedures, and we don't do any
    Postgres-specific operations yet.

Using Supervisord
~~~~~~~~~~~~~~~~~

An example of how to run all the services required is included in
``contrib/supervisord.conf``. Debugging is harder with this method, so it's not
required for development, but you can also use this configuration to understand
what commands to execute.

To use supervisor to run local processes::

    cd contrib/
    supervisord

Debugging into the detached processes is possible with ``rdb``, and you can see
what is happening in the foreground of the process with ``supervisorctl fg
<process>``. It might be easier to stop the process running in supervisor and
run the command manually if you need to do heavy debugging.
