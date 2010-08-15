Installation
=============

Installing RTD is pretty simple. Here is a step by step plan on how to do it.

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
