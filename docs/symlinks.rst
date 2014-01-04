How we use symlinks
===================

Read the Docs stays highly available by serving all documentation pages out of nginx.
This means that they never hit our Python layer,
meaning that they never hit out database.
This reduces the total number of servers to serve a request to 1,
each of which is redundant.

Nginx
-----

We handle a couple of different types of requests in nginx:

* Requests to a readthedocs.org subdomain
* Requests to a CNAME

Subdomains
----------

For subdomains this is a simple lookup.
This doesn't require symlinks,
but it shows the basic logic that we need to replicate.

When a user navigates to ``http://pip.readthedocs.org/en/latest/``,
we know that they want the pip documentation.
So we simply serve them the documentation:

.. code-block:: nginx

    location ~ ^/en/(.+)/(.*) {
        alias /home/docs/checkouts/readthedocs.org/user_builds/$domain/rtd-builds/$1/$2;
        error_page 404 = @fallback;
        error_page 500 = @fallback;
    } 

    location @fallback {
        proxy_pass http://127.0.0.1:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        add_header X-Deity Asgard;
    }

.. note:: The ``@fallback`` directive is hit when we don't find the proper file.
          This will cause things to hit the Python backend,
          so that proper action can be taken.

CNAMEs
------

CNAMEs add a bit of difficulty,
because at the nginx layer we don't know what documentation to serve.
When someone requests ``http://docs.fabfile.org/en/latest/``,
we can't look at the URL to know to serve the ``fabric`` docs.

This is where symlinks come in.
When someone requests ``http://docs.fabfile.org/en/latest/`` the first time,
it hits the Python layer.
In that Python layer we record that ``docs.fabfile.org`` points at ``fabric``.
When we build the ``fabric`` docs,
we create a symlink for all domains that have pointed at ``fabric`` before.

So,
when we get a request for ``docs.fabfile.org`` in the future,
we will be able to serve it directly from nginx.
In this example,
$host would be ``docs.fabfile.org``:

.. code-block:: nginx

    location ~ ^/en/(?P<doc_verison>.+)/(?P<path>.*) {
        alias /home/docs/checkouts/readthedocs.org/cnames/$host/$doc_verison/$path;
        error_page 404 = @fallback;
        error_page 500 = @fallback;
    }

Notice that nowhere in the above path is the projects slug mentioned.
It is simply there in the symlink in the cnames directory,
and the docs are served from there.