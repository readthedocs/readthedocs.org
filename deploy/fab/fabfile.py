import os

from fabric.api import *
import fabtools

cwd = os.getcwd()
all_users = ['docs', 'builder']
required_dirs = ['checkouts', 'etc', 'run', 'log']

def build():
    install_packages('build')
    users('build')
    checkout('build')
    setup_env()


def web():
    install_packages('web')
    users('docs')
    checkout('docs')
    setup_env()


def db():
    install_packages('db')


def install_packages(type):
    sudo('apt-get update')
    sudo('easy_install pip')
    sudo('pip install -U virtualenv')

    if type == 'build':
        sudo(
            'apt-get install -y git-core python-setuptools python-dev postgresql-client libpq-dev subversion graphviz curl sqlite libxml2-dev libxslt-dev vim g++')
        sudo('pip install -U mercurial')
    if type == 'db':
        sudo('apt-get install -y solr-tomcat redis-server postgresql ')
    if type == 'web':
        sudo('apt-get install -y nginx')


def users(user=None):
    if user:
        users = [user]
    else:
        users = all_users
    for user in users:
        home = '/home/%s' % user
        if not fabtools.user.exists(user):
            sudo('adduser --gecos "" -q --disabled-password %s' % user)

        if not fabtools.files.is_file('%s/.ssh/authorized_keys' % home):
            sudo('mkdir -p %s/.ssh' % home)
            put('keys/*.pub', '%s/.ssh/authorized_keys' % home, mode=700, use_sudo=True)
            sudo('chown -R %s:%s %s' % (user, user, home))
            sudo('chmod -R 700 %s' % home)
    sudo('mkdir -p /var/build')
    sudo('chmod 777 /var/build')
    # Docs > Syncer
    sudo('adduser docs builder')


def checkout(user=None):
    if user:
        users = [user]
    else:
        users = all_users
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


def setup_env(user=None):
    if user:
        users = [user]
    else:
        users = all_users
    for user in users:
        env.user = user
        home = '/home/%s' % user
        put('files/bash_profile', '%s/.bash_profile' % home)
        put('files/%s_supervisord.conf' % user, '%s/etc/supervisord.conf' % home)
        #put('files/%s_local_settings.py' % user, '%s/checkouts/readthedocs.org/readthedocs/settings/local_settings.py' % home)
        run('%s/bin/pip install -U supervisor ipython gunicorn' % home)


def setup_db():
    env.user = "docs"
    home = '/home/%s' % user
    with cd('%s/checkouts/readthedocs.org/readthedocs' % home):
        run('./manage.py syncdb --noinput')
        run('./manage.py migrate')
