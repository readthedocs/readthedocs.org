import os

from fabric.api import *
import fabtools
from fabtools import require

cwd = os.getcwd()
all_users = ['docs', 'eric', 'syncer']
checkout_users = ['docs', 'syncer']
required_dirs =['checkouts', 'etc', 'run', 'log']

def all():
    install_packages()
    users()
    checkout()
    setup_env()

def install_packages():
    env.user = 'root'
    sudo('apt-get update')
    sudo('apt-get install -y git-core python-setuptools python-dev postgresql-client libpq-dev subversion graphviz curl sqlite libxml2-dev libxslt-dev vim')
    sudo ('easy_install pip')
    sudo ('pip install -U virtualenv mercurial')

    # Prod Packages
    sudo('apt-get install -y redis-server memcached')

def users():
    env.user = 'root'
    for user in all_users:
        home = '/home/%s' % user
        if not fabtools.user.exists(user):
            sudo('adduser --gecos "" -q --disabled-password %s' % user)

        if not fabtools.files.is_file('%s/.ssh/authorized_keys' % home):
            sudo('mkdir -p %s/.ssh' % home)
            put('keys/*.pub', '%s/.ssh/authorized_keys' % home, mode=700)
            sudo('chown -R %s:%s %s' % (user, user, home))
            sudo('chmod -R 700 %s' % home)

def checkout(user):
    if user:
        users = [user]
    else:
        users = checkout_users
    for user in users:
        env.user = user
        home = '/home/%s' % user
        for dir in required_dirs:
            run('mkdir -p %s/%s' % (home, dir))
        if not fabtools.files.is_dir('%s/checkouts/readthedocs.org' % home):
            with cd('%s/checkouts/' % home):
                run('git clone git://github.com/rtfd/readthedocs.org.git')
        if not fabtools.files.is_file('%s/bin/python' % home):
            run('virtualenv %s' % home)
        run('%s/bin/pip install -U -r %s/checkouts/readthedocs.org/deploy_requirements.txt' % (home, home))

def setup_env(user):
    if user:
        users = [user]
    else:
        users = checkout_users
    for user in users:
        env.user = user
        home = '/home/%s' % user
        put('files/bash_profile', '%s/.bash_profile' % home)
        put('files/%s_supervisord.conf' % user, '%s/etc/supervisord.conf' % home)
        run('%s/bin/pip install -U supervisor ipython gunicorn' % home)

def setup_db():
    env.user = "docs"
    home = '/home/%s' % user
    with cd('%s/checkouts/readthedocs.org/readthedocs' % home):
        run('./manage.py syncdb --noinput')
        run('./manage.py migrate')
