from fabric.api import cd, env, prefix, run, sudo, task

# Fill out USER and HOSTS configuration before running
env.user = ''
env.hosts = ['']

env.code_dir = '/home/%s/rtd/checkouts/readthedocs.org' % (env.user)
env.virtualenv = '/home/%s/rtd' % (env.user)


def install_prerequisites():
    """Install prerequisites."""
    sudo("apt-get -y install python-dev python-pip git redis-server texlive "
         "texlive-latex-extra")
    sudo("pip install virtualenv")


def create_virtualenv():
    """Create virtualenv."""
    run("virtualenv --no-site-packages --distribute rtd")


def clone_repository():
    """Clone readthedocs repo"""
    run("mkdir %s/checkouts" % (env.virtualenv))
    with cd("%s/checkouts" % env.virtualenv):
        run("git clone http://github.com/rtfd/readthedocs.org.git")


def pip_requirements():
    """Install pip requirements"""
    with cd(env.code_dir):
        with prefix("source %s/bin/activate" % (env.virtualenv)):
            run("pip install -r pip_requirements.txt")


def build_db():
    """Build database"""
    with prefix("source %s/bin/activate" % (env.virtualenv)):
        run("%s/readthedocs/manage.py syncdb" % (env.code_dir))


def migrate_db():
    """Migrate database"""
    with prefix("source %s/bin/activate" % (env.virtualenv)):
        run("%s/readthedocs/manage.py migrate" % (env.code_dir))


def load_testprojects():
    """Load test data and update repos"""
    with prefix("source %s/bin/activate" % (env.virtualenv)):
        run("%s/readthedocs/manage.py loaddata test_data" % (env.code_dir))
        run("%s/readthedocs/manage.py update_repos" % (env.code_dir))


@task(default=True)
def install():
    """Install readthedocs"""
    install_prerequisites()
    create_virtualenv()
    clone_repository()
    pip_requirements()
    build_db()
    migrate_db()
    load_testprojects()


@task
def clean():
    """Clean up everything to start over"""
    sudo("rm -rf %s" % (env.virtualenv))
    sudo("pip uninstall virtualenv")
    sudo("apt-get -y purge python-dev python-pip git redis-server texlive "
         "texlive-latex-extra")
    sudo("apt-get -y autoremove --purge")
