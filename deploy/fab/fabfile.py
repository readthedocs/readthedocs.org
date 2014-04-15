import os

from fabric.api import cd, env, put, run, sudo, settings
from fabric.decorators import hosts
from fabric.contrib.files import upload_template
import fabtools

cwd = os.getcwd()
all_users = ['docs', 'builder']
required_dirs = ['checkouts', 'etc', 'run', 'log']

asgard_ip = '10.176.7.42'
backup_ip = '10.176.4.219'
bari_ip = '10.176.13.14'
build_ip = '10.176.11.210'
chimera_ip = '10.176.11.213'
db_ip = '10.176.9.67'

@hosts('root@newchimera', 'root@newasgard', 'root@newbuild', 'root@lb', 'root@bari')
def ntp():
    sudo('ntpdate-debian')

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

def install_python(version=2):
    # Python 3
    if version == 3:
        sudo('apt-get install -y python3.3 python3.3-dev')
        sudo('easy_install3 pip')
        sudo('pip3 install -U virtualenv')

    # Python 2
    if version == 2:
        sudo('easy_install-2.7 pip')
        sudo('pip2 install -U virtualenv')


def install_packages(type=None):
    sudo('apt-get update')
    sudo('apt-get install -y vim software-properties-common')
    sudo('apt-get install -y python-setuptools')

    if type == 'build':
        install_python()
        sudo(
            ' apt-get install -y git-core python-dev '
            ' postgresql-client libpq-dev subversion graphviz '
            ' curl sqlite libxml2-dev libxslt-dev vim g++ python-numpy '
            ' python-scipy build-essential texlive-full libevent-dev '
            ' libmysqlclient-dev python-m2crypto libffi-dev python-matplotlib '
            ' graphviz-dev libenchant1c2a pandoc'
            ' latex-cjk-chinese-arphic-gbsn00lp latex-cjk-chinese-arphic-gkai00mp',
            ' latex-cjk-chinese-arphic-bsmi00lp latex-cjk-chinese-arphic-bkai00mp'
        )
        sudo('pip2 install -U mercurial')
    if type == 'db':
        sudo('apt-get install -y solr-tomcat postgresql ')
    if type == 'search':
        sudo('add-apt-repository ppa:webupd8team/java')
        sudo('apt-get update')
        #sudo('apt-get install oracle-java7-installer')
    if type == 'web':
        sudo('apt-get install -y  nginx-extras git-core python-dev libpq-dev libxml2-dev libxslt-dev libjson-perl libi18n-acceptlanguage-perl')
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

        # Always update keys for now
        sudo('mkdir -p %s/.ssh' % home)
        put('keys/*.pub', '%s/.ssh/authorized_keys' % home, mode=700,
            use_sudo=True)
        sudo('chown -R %s:%s %s/.ssh' % (user, user, home))
        sudo('chmod 700 %s/.ssh' % home)
        sudo('chmod 600 %s/.ssh/*' % home)
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
            run('virtualenv2 %s' % home)
        run(('%s/bin/pip2 install --allow-all-external --allow-unverified bzr --allow-unverified launchpadlib --allow-unverified lazr.authentication -U -r %s/checkouts/readthedocs.org/'
             'deploy_requirements.txt') % (home, home))


def setup_env(user=None, role=None):
    if user:
        users = [user]
    else:
        users = all_users
    for user in users:
        env.user = user
        home = '/home/%s' % user
        put('files/bash_profile', '%s/.bash_profile' % home)
        if role:
            put('files/%s_supervisord.conf' % role,
                '%s/etc/supervisord.conf' % home)
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

def all_firewall():
    # Webs
    with settings(host_string='root@newasgard'):
        firewall('web')
        firewall('munin')
    with settings(host_string='root@newchimera'):
        firewall('web')
        firewall('munin')

    # Build servers
    with settings(host_string='root@bari'):
        firewall('build')
        firewall('munin')
    with settings(host_string='root@newbuild'):
        firewall('build')
        firewall('munin')

    # Backup
    with settings(host_string='root@newbackup'):
        firewall('backup')
        firewall('search')
        firewall('munin')

    # DB
    with settings(host_string='root@newdb'):
        firewall('db')
        firewall('search')
        firewall('munin')


def firewall(type):
    if type == "setup":
        sudo('apt-get install ufw')
        sudo('ufw allow 22 #SSH')
        sudo('ufw enable')
    if type == "munin":
        sudo('ufw allow from %s to any port 4949 #Munin' % backup_ip)
    if type == "web":
        sudo('ufw allow 80 #Nginx')
        sudo('ufw allow 443 #Nginx')
    if type == "db":
        for ip in [asgard_ip, chimera_ip, backup_ip]:
            sudo('ufw allow from %s to any port 5432 #Postgres' % ip)
        for ip in [asgard_ip, chimera_ip]:
            sudo('ufw allow from %s to any port 8080 #Solr' % ip)
    if type == "build":
        for ip in [asgard_ip, build_ip, chimera_ip, backup_ip, bari_ip]:
            sudo('ufw allow from %s to any port 6379 #Redis' % ip )
    if type == "backup":
        pass
    if type == "search":
        for ip in [asgard_ip, chimera_ip, backup_ip, db_ip]:
            sudo('ufw allow proto tcp from %s to any port 9200:9400 #ES' % ip)

def host_file():
   host_string = """
%s asgard 
%s backup
%s build
%s chimera
%s db
%s bari
    """ % (asgard_ip, backup_ip, build_ip, chimera_ip, db_ip, bari_ip)
   sudo("echo '%s' >> /etc/hosts " % host_string) 

def nginx_configs():
    with settings(host_string='root@lb'):
        context = {'host': 'Asgard'}
        upload_template('../nginx/app.nginx.conf', '/etc/nginx/sites-enabled/readthedocs', context=context, backup=False)
        upload_template('../nginx/lb.nginx.conf', '/etc/nginx/sites-enabled/lb', context=context, backup=False)
        upload_template('../nginx/main.nginx.conf', '/etc/nginx/nginx.conf', context=context, backup=False)
        # Perl config
        sudo('mkdir -p /usr/share/nginx/perl/')
        put('../salt/nginx/perl/lib/ReadTheDocs.pm', '/usr/share/nginx/perl/ReadTheDocs.pm')
    with settings(host_string='root@newasgard'):
        context = {'host': 'Asgard'}
        upload_template('../nginx/app.nginx.conf', '/etc/nginx/sites-enabled/readthedocs', context=context, backup=False)
        upload_template('../nginx/lb.nginx.conf', '/etc/nginx/sites-enabled/lb', context=context, backup=False)
        upload_template('../nginx/main.nginx.conf', '/etc/nginx/nginx.conf', context=context, backup=False)
        # Perl config
        sudo('mkdir -p /usr/share/nginx/perl/')
        put('../salt/nginx/perl/lib/ReadTheDocs.pm', '/usr/share/nginx/perl/ReadTheDocs.pm')
    with settings(host_string='root@newChimera'):
        context = {'host': 'Chimera'}
        upload_template('../nginx/app.nginx.conf', '/etc/nginx/sites-enabled/readthedocs', context=context, backup=False)
        upload_template('../nginx/lb.nginx.conf', '/etc/nginx/sites-enabled/lb', context=context, backup=False)
        upload_template('../nginx/main.nginx.conf', '/etc/nginx/nginx.conf', context=context, backup=False)
        # Perl config
        sudo('mkdir -p /usr/share/nginx/perl/')
        put('../salt/nginx/perl/lib/ReadTheDocs.pm', '/usr/share/nginx/perl/ReadTheDocs.pm')

def nginx_reload():
    with settings(host_string='root@lb'):
        sudo('/etc/init.d/nginx reload')
    with settings(host_string='root@newasgard'):
        sudo('/etc/init.d/nginx reload')
    with settings(host_string='root@newChimera'):
        sudo('/etc/init.d/nginx reload')

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
    #run('sudo -iu postgres dropdb docs')
    #run('sudo -iu postgres createdb docs --encoding=unicode')
    with settings(host_string='root@db'):
        run('time sudo -iu postgres pg_dump -Fc -C docs | ssh root@newdb.readthedocs.com " sudo -iu postgres pg_restore -C -d docs"')
