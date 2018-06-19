Public API
==========

This section of the documentation details the public API
usable to get details of projects, builds, versions and other details
from Read the Docs.

.. warning::

    Originally, the Read the Docs API allowed connections over insecure HTTP.
    Starting in January 2019, requests over HTTP
    will be automatically redirected to HTTPS
    and non-GET/HEAD requests over insecure HTTP will fail.

.. tip::

    It is a good idea to put your email address, application name,
    or Read the Docs username into the user agent header of your requests.
    That way we Read the Docs' team can contact you in the event of issues.


.. toctree::
    :maxdepth: 3

    v2
    v1
