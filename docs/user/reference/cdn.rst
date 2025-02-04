Content Delivery Network (CDN) and caching
==========================================

A CDN is used for making documentation pages *fast* for your users.
CDNs increase speed by caching documentation content in multiple data centers around the world,
and then serving docs from the data center closest to the user.

We support CDNs on both of our sites:

* On |org_brand|,
    we are able to provide a CDN to all the projects that we host.
    This service is graciously sponsored by `Cloudflare`_.
* On |com_brand|,
    the CDN is included as part of all of our plans.
    We use `Cloudflare`_ for this as well.

CDN benefits
------------

Having a CDN in front of your documentation has many benefits:

* **Improved reliability**: Since docs are served from multiple places, one can go down and the docs are still accessible.
* **Improved performance**: Data takes time to travel across space, so connecting to a server closer to the user makes documentation load faster.

Automatic cache refresh
-----------------------

We automatically refresh the cache on the CDN when the following actions happen:

* Your project is saved.
* Your domain is saved.
* A new version of your documentation is built.

By refreshing the cache according to these rules,
readers should **never see outdated content**.
This makes the end-user experience seamless and fast.

.. _Cloudflare: https://www.cloudflare.com/
