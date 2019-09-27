Advertising Details
===================

.. NOTE: This document is linked from:
.. https://media.readthedocs.org/javascript/readthedocs-analytics.js

Read the Docs largely funds our operations and development through advertising.
However, we aren't willing to compromise our values, document authors,
or site visitors simply to make a bit more money.
That's why we created our
:doc:`ethical advertising <ethical-advertising>` initiative.

We get a lot of inquiries about our approach to advertising which range
from questions about our practices to requests to partner.
The goal of this document is to shed light on the advertising industry,
exactly what we do for advertising, and how what we do is different.
If you have questions or comments,
`send us an email <mailto:ads@readthedocs.org>`_
or `open an issue on GitHub <https://github.com/readthedocs/readthedocs.org/issues>`_.


Other ad networks' targeting
----------------------------

Some ad networks build a database of user data in order to predict the types
of ads that are likely to be clicked.
In the advertising industry, this is called *behavioral targeting*.
This can include data such as:

* sites a user has visited
* a user's search history
* ads, pages, or stories a user has clicked on in the past
* demographic information such as age, gender, or income level

Typically, getting a user's page visit history is accomplished by the use of trackers
(sometimes called beacons or pixels).
For example, if a site uses a tracker from an ad network and a user visits that site,
the site can now target future advertising to that user -- a known past visitor --
with that network. This is called *retargeting*.

Other ad predictions are made by grouping similar users
together based on user data using machine learning.
Frequently this involves an advertiser uploading personal data on users
(often past customers of the advertiser)
to an ad network and telling the network to target similar users.
The idea is that two users with similar demographic information
and similar interests would like the same products.
In ad tech, this is known as *lookalike audiences* or *similar audiences*.

Understandably, many people have concerns about these targeting techniques.
The modern advertising industry has built enormous value by centralizing
massive amounts of data on as many people as possible.


Our targeting details
---------------------

**Read the Docs doesn't use the above techniques**.
Instead, we target based solely upon:

* Details of the page where the advertisement is shown including:

  * The name, keywords, or programming language associated with the project being viewed
  * Content of the page (eg. H1, title, theme, etc.)
  * Whether the page is being viewed from a mobile device

* General geography

  * We allow advertisers to target ads to a list of countries or to exclude
    countries from their advertising. For ads targeting the USA, we also support
    targeting by state or by metro area (DMA specifically).
  * We geolocate a user's IP address to a country when a request is made.

Read the Docs uses GeoLite2 data created by `MaxMind <http://maxmind.com>`_.


Where ads are shown
-------------------

We can place ads in:

* the sidebar navigation
* the footer of the page
* on search result pages
* a small footer fixed to the bottom of the viewport
* on 404 pages (rare)

We show no more than one ad per page so you will never see both
a sidebar ad and a footer ad on the same page.


Do Not Track Policy
-------------------

Read the Docs supports Do Not Track (DNT) and respects users' tracking preferences.
For more details, see the :ref:`Do Not Track section <privacy-policy:Do Not Track>`
of our privacy policy.


Analytics
---------

Analytics are a sensitive enough issue that they require their own section.
In the spirit of full transparency, Read the Docs uses Google Analytics (GA).
We go into a bit of detail on our use of GA in our :doc:`/privacy-policy`.

GA is a contentious issue inside Read the Docs and in our community.
Some users are very sensitive and privacy conscious to usage of GA.
Some authors want their own analytics on their docs to see the usage their docs get.
The developers at Read the Docs understand that different users have different priorities
and we try to respect the different viewpoints as much as possible while also accomplishing
our own goals.

We have taken steps to address some of the privacy concerns surrounding GA.
These steps apply both to analytics collected by Read the Docs and when
:doc:`authors enable analytics on their docs </guides/google-analytics>`.

* Users can opt-out of analytics by using the Do Not Track feature of their browser.
* Read the Docs instructs Google to anonymize IP addresses sent to them.
* The cookies set by GA expire in 30 days rather than the default 2 years.

Why we use analytics
~~~~~~~~~~~~~~~~~~~~

Advertisers ask us questions that are easily answered with an analytics solution like
"how many users do you have in Switzerland browsing Python docs?". We need to be able
to easily get this data. We also use data from GA for some development decisions such
as what browsers to support (or not) or how much usage a particular page or feature gets.

Alternatives
~~~~~~~~~~~~

We are always exploring our options with respect to analytics.
There are alternatives but none of them are without downsides.
Some alternatives are:

* Run a different cloud analytics solution from a provider other than Google
  (eg. Parse.ly, Matomo Cloud, Adobe Analytics).
  We priced a couple of these out based on our load and they are very expensive.
  They also just substitute one problem of data sharing with another.
* Send data to GA (or another cloud analytics provider) on the server side and
  strip or anonymize personal data such as IPs before sending them.
  This would be a complex solution and involve additional infrastructure,
  but it would have many advantages. It would result in a loss of data on
  "sessions" and new vs. returning visitors which are of limited value to us.
* Run a local JavaScript based analytics solution (eg. Matomo community).
  This involves additional infrastructure that needs to be always up.
  Frequently there are very large databases associated with this.
  Many of these solutions aren't built to handle Read the Docs' load.
* Run a local analytics solution based on web server log parsing.
  This has the same infrastructure problems as above while also
  not capturing all the data we want (without additional engineering) like the
  programming language of the docs being shown or
  whether the docs are built with Sphinx or something else.
