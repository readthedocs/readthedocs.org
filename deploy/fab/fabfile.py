import os

from fabric.api import cd, env, put, run, sudo, settings
from fabric.decorators import hosts
import fabtools

cwd = os.getcwd()
all_users = ['docs', 'builder']
required_dirs = ['checkouts', 'etc', 'run', 'log']

asgard_ip = '10.176.7.42'
backup_ip = '10.176.4.219'
build_ip = '10.176.11.210'
chimera_ip = '10.176.11.213'
db_ip = '10.176.9.67'


def all():
    install_packages('build')
    install_packages('web')
    install_packages('db')
    users('docs')
    checkout('docs')
    setup_env('docs')


def build():
    users('root')
    users('docs')
    install_packages('build')
    firewall('build')
    checkout('docs')
    setup_env('docs')
    fix_perms('docs')
    sudo('mkdir -p /var/build')
    sudo('chmod 777 /var/build')


def web():
    users('root')
    users('docs')
    install_packages('web')
    firewall('web')
    checkout('docs')
    setup_env('docs')
    fix_perms('docs')
    sudo('mkdir -p /var/build')
    sudo('chmod 777 /var/build')


def db():
    users('root')
    install_packages('db')
    firewall('db')

def backup():
    users('root')
    install_packages('backup')
    firewall('backup')


def install_packages(type=None):
    sudo('apt-get update')
    sudo('apt-get install -y vim software-properties-common')
    sudo('apt-get install -y python-setuptools')
    sudo('easy_install pip')
    sudo('pip install -U virtualenv')

    if type == 'build':
        sudo(
            ' apt-get install -y git-core python-dev '
            ' postgresql-client libpq-dev subversion graphviz '
            ' curl sqlite libxml2-dev libxslt-dev vim g++ python-numpy '
            ' python-scipy build-essential texlive-full libevent-dev '
            ' libmysqlclient-dev python-m2crypto libffi-dev python-matplotlib '
            ' graphviz-dev libenchant1c2a '
        )
        sudo('pip install -U mercurial')
    if type == 'db':
        sudo('apt-get install -y solr-tomcat postgresql ')
    if type == 'web':
        sudo('apt-get install -y nginx git-core python-dev libpq-dev libxml2-dev libxslt-dev')
    if type == 'backup':
        sudo('apt-get install -y rsync')


def users(user=None):
    if user:
        users = [user]
    else:
        users = all_users
    for user in users:
        if user == "root":
           home = "/root" 
        else:
            home = '/home/%s' % user
        if not fabtools.user.exists(user):
            sudo('adduser --gecos "" -q --disabled-password %s' % user)

        if not fabtools.files.is_file('%s/.ssh/authorized_keys' % home):
            sudo('mkdir -p %s/.ssh' % home)
            put('keys/*.pub', '%s/.ssh/authorized_keys' % home, mode=700,
                use_sudo=True)
            sudo('chown -R %s:%s %s' % (user, user, home))
            sudo('chmod -R 700 %s' % home)
    # Docs > Syncer
    #sudo('adduser docs builder')


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
        run(('%s/bin/pip install -U -r %s/checkouts/readthedocs.org/'
             'deploy_requirements.txt') % (home, home))


def setup_env(user=None):
    if user:
        users = [user]
    else:
        users = all_users
    for user in users:
        env.user = user
        home = '/home/%s' % user
        put('files/bash_profile', '%s/.bash_profile' % home)
        #put('files/%s_supervisord.conf' % user,
            #'%s/etc/supervisord.conf' % home)
        #run('%s/bin/pip install -U supervisor ipython gunicorn' % home)


def fix_perms(user=None):
    if user:
        users = [user]
    else:
        users = all_users
    for user in users:
        env.user = user
        home = '/home/%s' % user
        sudo('chown -R %s:%s %s' % (user, user, home))


def setup_db():
    env.user = "docs"
    home = '/home/%s' % env.user
    with cd('%s/checkouts/readthedocs.org/readthedocs' % home):
        run('./manage.py syncdb --noinput')
        run('./manage.py migrate')

def firewall(type):
    sudo('apt-get install ufw')
    sudo('ufw allow 22 #SSH')
    sudo('ufw enable')
    if type == "web":
        sudo('ufw allow 80 #Nginx')
        sudo('ufw allow 443 #Nginx')
    if type == "db":
        for ip in [asgard_ip, chimera_ip, backup_ip]:
            sudo('ufw allow from %s to any port 5432 #Postgres' % ip)
        for ip in [asgard_ip, chimera_ip]:
            sudo('ufw allow from %s to any port 8080 #Solr' % ip)
    if type == "build":
        for ip in [asgard_ip, build_ip, chimera_ip, backup_ip]:
            sudo('ufw allow from %s to any port 6379 #Redis' % ip )
    if type == "backup":
        pass


def host_file():
   host_string = """
%s asgard 
%s backup
%s build
%s chimera
%s db
    """ % (asgard_ip, backup_ip, build_ip, chimera_ip, db_ip)
   sudo("echo '%s' >> /etc/hosts " % host_string) 

def pg_hba():
    hba_string = """
host    all             all             %s/32          trust
host    all             all             %s/32          trust
host    all             all             %s/32          trust
    """ % (asgard_ip, backup_ip, chimera_ip)
    sudo("echo '%s' >> /etc/postgresql/9.1/main/pg_hba.conf " % hba_string) 


@hosts('root@newchimera')
def migrate_html():
    #with cd('/var/build/'):
        #run('rsync -a root@chimera.readthedocs.com:/var/build/user_builds .')
    with settings(host_string='root@newasgard'):
        with cd('/var/build/'):
            run('rsync -a root@chimera:/var/build/user_builds .')

@hosts('docs@newchimera')
def migrate_media():
    with cd('/home/docs/checkouts/readthedocs.org/'):
        run('rsync -a chimera.readthedocs.com:/home/docs/checkouts/readthedocs.org/media .')
    with settings(host_string='docs@newasgard'):
        with cd('/home/docs/checkouts/readthedocs.org/'):
            run('rsync -a chimera:/home/docs/checkouts/readthedocs.org/media .')

@hosts('root@newdb')
def migrate_db():
    run('sudo -iu postgres dropdb docs')
    run('sudo -iu postgres createdb docs --encoding=unicode')
    with settings(host_string='root@db'):
        run('time sudo -iu postgres pg_dump -Fc -C docs | ssh root@newdb.readthedocs.com " sudo -iu postgres pg_restore -C -d docs"')
