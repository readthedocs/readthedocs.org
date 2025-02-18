Search analytics
================

When someone visits your documentation and uses the built-in :doc:`server side search </server-side-search/index>` feature,
Read the Docs will collect analytics on their search queries.

These are aggregated into a simple view of the
"Top queries in the past 30 days".
You can also download this data.

This is helpful to optimize your documentation in alignment with your readers' interests.
You can discover new trends and expand your documentation to new needs.

Using search analytics
----------------------

To see a list of the top queries and an overview from the last month,
go to the :guilabel:`Admin` tab of your project,
and then click on :guilabel:`Search Analytics`.

.. figure:: /_static/images/search-analytics-demo.png
   :width: 50%
   :align: center
   :alt: Search analytics demo

   How the search analytics page looks.

In **Top queries in the past 30 days**,
you see all the latest searches ordered by their popularity.
The list itself is often longer than what meets the eye,
Scroll downwards on the list itself to see more results.

Understanding your analytics
----------------------------

In **Top queries in the past 30 days**, you can see the most popular terms that users have searched for.
Next to the search query, the number of actual **results** for that query is shown.
The number of times the query has been used in a search is displayed as the **searches** number.

* If you see a search term that doesn't have any results,
  you could apply that term in documentation articles or create new ones.
  This is a great way to understand missing gaps in your documentation.

* If a search term is often used but the documentation article exists,
  it can also indicate that it's hard to navigate to the article.

* Repeat the search yourself and inspect the results to see if they are relevant.
  You can add keywords to various pages that you want to show up for searches on that page.

In **Daily search totals**, you can see trends that might match special events in your project's publicity.
If you wish to analyze these numbers in details, click :guilabel:`Download all data`
to get a CSV formatted file with all available search analytics.

Data storage
------------

The duration of analytics data stored depends on which site you're using:

* On |org_brand|, the last 90 days are stored.
* On |com_brand|, storage duration starts at 30 days and increases with plan level.

.. seealso::

   `Our plan pricing <https://about.readthedocs.com/pricing/>`_
      Compare our plan pricing and analytics storage duration.

   :doc:`/traffic-analytics`
      See how users are using your documentation.
