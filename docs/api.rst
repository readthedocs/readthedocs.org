Read the Docs Public API
=========================

We have a limited public API that is available for you to get data out of the site. This page will only show a few of the basic parts, please file a ticket or ping us on IRC if you have feature requests.


In all of these examples, replace `pip` with your own project.


Project Details
---------------

cURL
~~~~~
Feel free to use cURL and python to look at formatted json examples. You can also look at them in your browser, if it handles returned json.

`curl http://readthedocs.org/api/v1/project/pip/?format=json |python -mjson.tool`


URL
~~~
http://readthedocs.org/api/v1/project/pip/?format=json


Build List
----------

URL
~~~
http://readthedocs.org/api/v1/build/pip/?format=json

Version List
-------------

URL
~~~
http://readthedocs.org/api/v1/version/pip/?format=json


Highest Version
----------------

URL
~~~
http://readthedocs.org/api/v1/version/pip/highest/?format=json

Filtered Highest Version
--------------------------

URL
~~~
http://readthedocs.org/api/v1/version/pip/highest/0.9/?format=json

The filter expression at the end (0.9), will have the version numbers filtered against.
