import os

from fabric.api import *
import fabtools
from fabtools import require

env.code_dir = '/home/docs/checkouts/readthedocs.org'
env.virtualenv = '/home/docs/'

cwd = os.getcwd()

def all():
    users()
    install_packages()
    checkout()
    setup_env()

def users():
    env.user = 'root'
    users = ['docs', 'eric']
    for user in users:
        if not fabtools.user.exists(user):
            sudo('adduser --gecos "" -q --disabled-password %s' % user)

    if not fabtools.files.is_file('/home/docs/.ssh/authorized_keys'):
        sudo('mkdir -p /home/%s/.ssh' % user)
        put('keys/*.pub', '/home/%s/.ssh/authorized_keys' % user, mode=700)
        sudo('chown -R %s:%s /home/%s/' % (user, user, user))
        sudo('chmod -R 700 /home/%s/.ssh' % (user))

def install_packages():
    env.user = 'root'
    sudo('apt-get update')
    sudo('apt-get install -y git-core python-setuptools python-dev postgresql-client libpq-dev subversion graphviz curl sqlite libxml2-dev libxslt-dev vim')
    sudo ('easy_install pip')
    sudo ('pip install -U virtualenv mercurial')

    # Prod Packages
    sudo('apt-get install -y redis-server memcached')


def checkout():
    env.user = 'docs'
    run('mkdir -p /home/docs/checkouts/')
    run('mkdir -p /home/docs/etc/')
    run('mkdir -p /home/docs/run/')
    run('mkdir -p /home/docs/log/')
    if not fabtools.files.is_dir(env.code_dir):
        with cd('/home/docs/checkouts/'):
            run('git clone git://github.com/rtfd/readthedocs.org.git')
    if not fabtools.files.is_file('/home/docs/bin/python'):
        run('virtualenv %s' % env.virtualenv)
    run('/home/docs/bin/pip install -U -r /home/docs/checkouts/readthedocs.org/deploy_requirements.txt')

def setup_env():
    env.user = 'docs'
    put('files/bash_profile', '/home/docs/.bash_profile')
    put('files/supervisord.conf', '/home/docs/etc/supervisord.conf')
    run('/home/docs/bin/pip install -U supervisor ipython gunicorn')
    with cd('/home/docs/checkouts/readthedocs.org/readthedocs'):
        run('./manage.py syncdb --noinput')
        run('./manage.py migrate')
