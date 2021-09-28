Traffic Analytics
=================

Traffic Analytics lets you see *which* documents your users are reading.
This allows you to understand how your documentation is being used,
so you can focus on expanding and updating parts people are reading most.

To see a list of the top pages from the last month,
go to the :guilabel:`Admin` tab of your project,
and then click on :guilabel:`Traffic Analytics`.

.. figure:: /_static/images/traffic-analytics-demo.png
   :width: 50%
   :align: center
   :alt: Traffic analytics demo

   Traffic analytics demo

You can also access to analytics data from :ref:`search results <server-side-search:analytics>`.

Enabling Google Analytics on your Project
-----------------------------------------

Read the Docs has native support for Google Analytics.
You can enable it by:

* Going to :guilabel:`Admin` > :guilabel:`Advanced Settings` in your project.
* Fill in the **Analytics code** heading with your Google Tracking ID (example `UA-123456674-1`)

Once your documentation rebuilds it will include your Analytics tracking code and start sending data.
Google Analytics usually takes 60 minutes,
and sometimes can take up to a day before it starts reporting data.

.. note::

   Read the Docs takes some extra precautions with analytics to protect user privacy.
   As a result, users with Do Not Track enabled will not be counted
   for the purpose of analytics.

   For more details, see the
   :ref:`Do Not Track section <privacy-policy:Do Not Track>`
   of our privacy policy.

Disabling Google Analytics on your project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Google Analytics can be completely disabled on your own projects.
To disable Google Analytics:

* Going to :guilabel:`Admin` > :guilabel:`Advanced Settings` in your project.
* Check the box **Disable Analytics**.

Your documentation will need to be rebuilt for this change to take effect.
