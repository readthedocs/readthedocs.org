Installation
=============

Installing RTD is pretty simple. Here is a step by step plan on how to do it.
::

    virtualenv rtd
    cd rtd
    . bin/activate
    mkdir checkouts
    cd checkouts
    git clone http://github.com/beetletweezers/tweezers.git
    cd tweezers
    pip install -r pip_requirements.txt
    #Have a beer
    ./manage.py syncdb
    #Make sure you create a user here
    ./manage.py migrate
    ./manage.py update_repos
    #Have another beer
    ./manage.py runserver


Now you should be seeing a page with the list of projects that you can click around on. I recommend logging in to see more of the sites functionality, and to create or edit more repos.


What's available
----------------

After registering with the site (or creating yourself a superuser account),
you will be able to log in and view the `dashboard <http://readthedocs.org/dashboard/`_

From the dashboard you can either create new documentation, or import your existing
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
