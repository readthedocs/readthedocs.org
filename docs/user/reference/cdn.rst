Content Delivery Network (CDN) and caching
==========================================

A CDN is used for making documentation pages *fast* for your users.
This is done by caching the documentation page content in multiple data centers around the world,
and then serving docs from the data center closest to the user.

We support CDNs on both of our sites:

* On |org_brand|,
    we are able to provide a CDN to all the projects that we host.
    This service is graciously sponsored by `Cloudflare`_.
* On |com_brand|,
    the CDN is included as part of our all of our plans.
    We use `Cloudflare`_ for this as well.

CDN Benefits
------------

Having a CDN in front of your documentation has many benefits:

* **Improved reliability**: Since docs are served from multiple places, one can go down and the docs are still accessible.
* **Improved performance**: Data takes time to travel across space, so connecting to a server closer to the user makes documentation load faster.

CDN Features
------------

Our integration between building and hosting documentation allows to do many smart things to make the experience seemless.

We automatically refresh the cache on the CDN when the following actions happen:

* Your project is saved.
* Your domain is saved.
* A new version of your documentation is built.

This means that you should **never see outdated content**,
but it's always as fast a possible for your users.

.. _Cloudflare: https://www.cloudflare.com/
