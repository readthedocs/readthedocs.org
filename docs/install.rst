.. _installing-read-the-docs:

Installation
=============

Here is a step by step plan on how to install Read the Docs.
It will get you to a point of having a local running instance.

.. warning::

    Read the Docs does not itself run under Python 3 (though it does support
    building documentation for Python 3 projects). Please ensure the subsequent
    steps are performed using Python 2.7.


First, obtain `Python 2.7`_ and virtualenv_ if you do not already have them. Using a
virtual environment will make the installation easier, and will help to avoid
clutter in your system-wide libraries. You will also need Git_ in order to
clone the repository. If you plan to import Python 3 project to your RTD then you'll
need to install Python 3 with virtualenv in your system as well.


.. _Python 2.7: http://www.python.org/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Git: http://git-scm.com/
.. _Homebrew: http://brew.sh/
.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _PostgreSQL: https://www.postgresql.org/
.. _Redis: https://redis.io/


.. note::

    If you are having trouble on OS X Mavericks (or possibly other versions of
    OS X) with building ``lxml``, you probably might need to use Homebrew_
    to ``brew install libxml2``, and invoke the install with::

        CFLAGS=-I/usr/local/opt/libxml2/include/libxml2 \
        LDFLAGS=-L/usr/local/opt/libxml2/lib \
        pip install -r requirements.txt

.. note::

    Linux users may find they need to install a few additional packages
    in order to successfully execute ``pip install -r requirements.txt``.
    For example, a clean install of Ubuntu 14.04 LTS will require the
    following packages::

        sudo apt-get install build-essential
        sudo apt-get install python-dev python-pip python-setuptools
        sudo apt-get install libxml2-dev libxslt1-dev zlib1g-dev

    Users of other Linux distributions may need to install the equivalent
    packages, depending on their system configuration.

.. note::

   If you want full support for searching inside your Read the Docs
   site you will need to install Elasticsearch_.

   Ubuntu users could install this package as following::

        sudo apt-get install elasticsearch

.. note::

   Besides the Python specific dependencies, you will also need Redis_.

   Ubuntu users could install this package as following::

        sudo apt-get install redis-server


You will need to verify that your pip version is higher than 1.5 you can do this as such::

    pip --version

If this is not the case please update your pip version before continuing::

    pip install --upgrade pip

Once you have these, create a virtual environment somewhere on your disk, then
activate it::

    virtualenv rtd
    cd rtd
    source bin/activate

Create a folder in here, and clone the repository::

    mkdir checkouts
    cd checkouts
    git clone https://github.com/rtfd/readthedocs.org.git

Next, install the dependencies using ``pip`` (included inside of virtualenv_)::

    cd readthedocs.org
    pip install -r requirements.txt

This may take a while, so go grab a beverage. When it's done, build your
database::

    python manage.py migrate

Then please create a superuser account for Django::

    python manage.py createsuperuser

Now let's properly generate the static assets::

    python manage.py collectstatic

By now, it is the right time to load in a couple users and a test project::

    python manage.py loaddata test_data

.. note::

    If you do not opt to install test data, you'll need to create an account for
    API use and set ``SLUMBER_USERNAME`` and ``SLUMBER_PASSWORD`` in order for
    everything to work properly.

Finally, you're ready to start the webserver::

    python manage.py runserver

Visit http://127.0.0.1:8000/ in your browser to see how it looks; you can use
the admin interface via http://127.0.0.1:8000/admin (logging in with the
superuser account you just created).

For builds to properly kick off as expected, it is necessary the port
you're serving on (i.e. ``runserver 0.0.0.0:8080``) match the port defined
in ``PRODUCTION_DOMAIN``. You can utilize ``local_settings.py`` to modify this.
(By default, it's ``localhost:8000``)

While the webserver is running, you can build documentation for the latest version of
a project called 'pip' with the ``update_repos`` command.  You can replace 'pip'
with the name of any added project::

   python manage.py update_repos pip

Serving RTD with Apache2 and WSGI
=================================

.. note::

    The following assumes Ubuntu 16.04 Server and Apache >= 2.4.

Serving **Read the Docs** using `Apache`_ and `mod_wsgi`_ starts off similar to running a
local instance. Follow the instructions above, but instead place your virtualenv somewhere
nice (perhaps ``/usr/local/pythonenvs/rtfd``) and clone the repo into ``/var/www/rtfd``::

    cd /usr/local/
    sudo mkdir pythonenvs
    sudo virutalenv rtfd
    cd /var/www
    sudo git clone https://github.com/rtfd/readthedocs.org.git rtfd
    
.. note::

    You'll likely need to prepend sudo on all of the commands, since ``/var/www`` is owned by the
    ``root`` user by default.
    
After performing all of the above steps, change the owner of the ``/var/www/rtfd`` directory to
``www-data`` so that mod_wsgi can do its thing.

::

    sudo chown -R www-data:www-data /var/www/rtfd

.. _Apache: https://httpd.apache.org/
.. _mod_wsgi: https://modwsgi.readthedocs.io/en/develop/

Getting a externally-visuble server up an running requires:

1. Installing Apache and mod_wsgi.
2. Creating a Django settings file.
3. Updating ``readthedocs/wsgi.py`` with the virtualenv information.
4. Creating an Apache .conf file for your site.

1. Installing Apache and mod_wsgi
---------------------------------

::

    sudo apt install apache2
    sudo apt install libapache2-mod-wsgi

2. Creating a Django settings file
----------------------------------

This settings file should contain all of your Django settings. The example below simply
takes the default settings from Read the Docs and adds a missing item.

.. code:: python

    # readthedocs/settings/mysite.py
    import os

    from .base import CommunityBaseSettings
    
    CommunityBaseSettings.load_settings(__name__)

    DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': '/var/www/rtfd/dev.db',
          'USER': 'username',       # from the `python manage.py createsuperuser` step
          'PASSWORD': 'password',   # from the `python manage.py createsuperuser` step
          }
    }
    
    SECRET_KEY = 'replace_me'

    if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
        try:
            from .local_settings import *       # noqa
        except ImportError:
            pass
            
.. note::

    Make sure to also set ``SECRET_KEY`` to, well, a secret!

3. Updating ``readthedocs/wsgi.py`` with the virtualenv information
-------------------------------------------------------------------

Modify ``readthedocs\wsgi.py`` so that it looks like so:

.. code:: python

    import os
    import site
    import system
    
    # Add our virtualenv to the site-dirs.
    site.addsitedir('/path/to/virtualenv/lib/python2.7/site-packages')
    sys.path.insert(0, 'var/www/rtfd')

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'readthedocs.settings.mysite')
    
    # This application object is used by any WSGI server configured to use this
    # file. This includes Django's development server, if the WSGI_APPLICATION
    # setting points here.
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    
    # Apply WSGI middleware here.
    # from helloworld.wsgi import HelloWorldApplication
    # application = HelloWorldApplication(application)

4. Creating an Apache .conf file for your site
----------------------------------------------

The last thing to do is set up the Apache config. Create the following file:
``/etc/apache2/sites-available/rtfd.conf``. Note that the file name, ``rtfd.conf`` does not need
to match anything - you can name it anything you'd like. In fact, if you're already hosting
other sites on your chosen server, you can just add to your primary VirtualHost in your Apache
``.conf`` file. Populate the new file with::

    <VirtualHost *:80>
        # General server information
        ServerName myserver
        ServerAlias myalias
        ServerAdmin admin@email.com
        
        # App: Read the Docs
        WSGIDaemonProcess rtfd user=www-data group=www-data
        WSGIScriptAlias / /var/www/rtfd/readthedocs/wsgi.py
        <Location />
            WSGIProcessGroup rtfd
        </Location>
        <Directory /var/www/rtfd/readthedocs>
            <Files wsgi.py>
                Require all granted
            </Files>
        </Directory>
        
        # Server Logging
        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined
    </VirtualHost>

Finally, we need to restart the apache server::

    sudo service apache2 restart

On another machine, navigate to your server's IP address in your web browser and verify
that you see the Read the Docs homepage. You should be all set up at this point, but you'll
probably want to update your DNS so that you don't have to use an IP address all the time.

What's available
----------------

After registering with the site (or creating yourself a superuser account),
you will be able to log in and view the `dashboard <http://localhost:8000/dashboard/>`_.

From the dashboard you can import your existing
docs provided that they are in a git or mercurial repo.


Creating new Docs
^^^^^^^^^^^^^^^^^

One of the goals of `readthedocs.org <http://readthedocs.org>`_ is to make it
easy for any open source developer to get high quality hosted docs with great
visibility!  We provide a simple editor and two sample pages whenever
a new project is created.  From there its up to you to fill in the gaps - we'll
build the docs, give you access to history on every revision of your files,
and we plan on adding more features in the weeks and months to come.


Importing existing docs
^^^^^^^^^^^^^^^^^^^^^^^

The other side of `readthedocs.org <http://readthedocs.org>`_ is hosting the
docs you've already built.  Simply provide us with the clone url to your repo,
we'll pull your code, extract your docs, and build them!  We make available
a post-commit webhook that can be configured to update the docs on our site
whenever you commit to your repo, effectively letting you 'set it and forget it'.
