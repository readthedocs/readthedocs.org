Configuration of the production servers
=======================================

This document is to help people who are involved in the production instance of Read the Docs running on readthedocs.org. It contains implementation details and useful hints for the people handling operations of the servers.

Elastic Search Setup
--------------------

::

    from search.indexes import Index, PageIndex, ProjectIndex
     
    # Create the index.
    index = Index()
    index_name = index.timestamped_index()
    index.create_index(index_name)
    index.update_aliases(index_name)
    # Update mapping
    proj = ProjectIndex()
    proj.put_mapping()
    page = PageIndex()
    page.put_mapping()


Servers
-------
The servers are themed somewhere between Norse mythology and Final Fantasy Aeons. I tried to keep them topical, and have some sense of their historical meaning and their purpose in the infrastructure.

Domain
~~~~~~

  * readthedocs.com

Load Balancer (nginx)
~~~~~~~~~~~~~~~~~~~~~
    * Asgard

Important Files
```````````````
    * /etc/nginx/sites-enabled/default

Important Services
``````````````````
    * nginx running from init

Web
~~~
    * Chimera
    * Asgard

Important Files
```````````````
    * /etc/nginx/sites-enabled/readthedocs
    * /home/docs/sites/readthedocs.org/run/gunicorn.log

Important Services
``````````````````
    * nginx running from init
    * gunicorn (running from supervisord as docs user)

Build
~~~~~
    * Build

Important Files
```````````````
    * /home/docs/sites/readthedocs.org/run/celery.log

Important Services
``````````````````
    * celery (running from supervisord as docs user)

Database
~~~~~~~~
    * DB

Solr
~~~~
    * DB

Redis
~~~~~
    * DB

Site Checkout
-------------

``/home/docs/sites/readthedocs.org/checkouts/readthedocs``

Bash Aliases
~~~~~~~~~~~~

    * `chk` - Will take you to the checkout directory
    * `run` - Will take you to the run directory

Deploying
---------

Pushing code to servers. This updates code & media::

    fab push

Restart the webs::

    fab restart

Restart the build servers celery::

    fab celery


