from fabric.api import cd, env, lcd, local, hosts, prompt, run
from fabric.decorators import runs_once

import os
import time

env.runtime = 'production'
env.hosts = ['newchimera.readthedocs.com',
             'newbuild.readthedocs.com',
             'bari.readthedocs.com',
             'newasgard.readthedocs.com']
env.user = 'docs'
env.code_dir = '/home/docs/checkouts/readthedocs.org'
env.virtualenv = '/home/docs/'
env.rundir = '/home/docs/run'

fabfile_dir = os.path.dirname(__file__)

@hosts(['newchimera.readthedocs.com', 'newasgard.readthedocs.com'])
def remove_project(project):
    run('rm -rf %s/user_builds/%s' % (env.code_dir, project))

def ntpdate():
    run('ntpdate-debian')

## Logging Awesomeness

@hosts(['newasgard.readthedocs.com', 'newchimera.readthedocs.com'])
def nginx_logs():
    env.user = "root"
    run("tail -F /var/log/nginx/*.log")

@hosts(['newbuild.readthedocs.com', 'bari.readthedocs.com'])
def celery_logs():
    env.user = "docs"
    run("tail -F tail -f ~/log/celery.err")

@hosts(['newasgard.readthedocs.com', 'newchimera.readthedocs.com'])
def logs():
    env.user = "docs"
    run("tail -F %s/logs/*.log" % env.code_dir)

@hosts(['newasgard.readthedocs.com', 'newchimera.readthedocs.com'])
def postcommit_logs():
    env.user = "docs"
    run("tail -F %s/logs/postcommit.log" % env.code_dir)

@hosts(['newasgard.readthedocs.com', 'newchimera.readthedocs.com'])
def cat_postcommit_logs():
    env.user = "docs"
    run("cat %s/logs/postcommit.log" % env.code_dir)

@hosts(['newasgard.readthedocs.com', 'newchimera.readthedocs.com'])
def api_logs():
    env.user = "docs"
    run("tail -F %s/logs/api.log" % env.code_dir)

@hosts(['newasgard.readthedocs.com', 'newchimera.readthedocs.com'])
def web_logs(type):
    """
    Get logs from the web servers::

    fab -P web_logs:middleware
    """
    env.user = "docs"
    run("tail -F %s/logs/%s.log" % (env.code_dir, type))

## Normal bits

@hosts(['localhost'])
def i18n():
    with lcd('readthedocs'):
        local('rm -rf rtd_tests/tests/builds/')
        local('tx pull')
        local('./manage.py makemessages --all')
        local('tx push -s')
        local('./manage.py compilemessages')

@hosts(['localhost'])
def i18n_docs():
    with lcd('docs'):
        # Update our tanslations
        local('tx pull -a')
        local('sphinx-intl build')
        # Push new ones
        local('make gettext')
        local('tx push -s')


def push():
    "Push new code, but don't restart/reload."
    local('git push origin master')
    with cd(env.code_dir):
        run('git fetch')
        run('git reset --hard origin/master')


def update_requirements():
    "Update requirements in the virtualenv."
    run("%s/bin/pip install -r %s/deploy_requirements.txt" % (env.virtualenv, env.code_dir))


@hosts(['newchimera.readthedocs.com'])
def migrate(project=None):
    if project:
        run('django-admin.py migrate %s' % project)
    else:
        run('django-admin.py migrate')

@hosts(['newchimera.readthedocs.com'])
def syncdb(project=None):
    run('django-admin.py syncdb')

@hosts(['newchimera.readthedocs.com', 'newasgard.readthedocs.com'])
def static():
    "Restart (or just start) the server"
    run('django-admin.py collectstatic --noinput')


@hosts(['newchimera.readthedocs.com', 'newasgard.readthedocs.com'])
def restart():
    "Restart (or just start) the server"
    env.user = "docs"
    run("supervisorctl restart web")
    #so it has time to reload
    time.sleep(3)


@hosts(['newchimera.readthedocs.com', 'newasgard.readthedocs.com'])
def reload():
    "Reload (or just start) the server"
    run("supervisorctl update")


@hosts(['newbuild.readthedocs.com', 'bari.readthedocs.com'])
def celery():
    "Restart (or just start) the server"
    run("supervisorctl restart celery")


def pull():
    "Pull new code"
    with cd(env.code_dir):
        run('git fetch')
        run('git reset --hard origin/master')


@runs_once
def spider():
    local('patu.py -d1 readthedocs.org')


def _aws_wrapper(f, *args, **kwargs):
    "get AWS credentials if not defined"
    #these are normally defined in ~/.fabricrc
    @hosts('run_once')  # so fab doesn't go crazy
    def wrapped(*args, **kwargs):
        from boto.cloudfront.exception import CloudFrontServerError
        from boto.cloudfront import CloudFrontConnection
        c = CloudFrontConnection(env.aws_access_key_id,
                                 env.aws_secret_access_key)
        if not hasattr(env, 'aws_access_key_id'):
            prompt('AWS Access Key ID: ', key='aws_access_key_id')
        if not hasattr(env, 'aws_secret_access_key'):
            prompt('AWS Secret Access Key: ', key='aws_secret_access_key')
        try:
            return f(c, *args, **kwargs)
        except CloudFrontServerError as e:
            print "Error: \n", e.error_message
    return wrapped


@_aws_wrapper
def to_cdn(c, slug):
    "Create a new Distribution object on CloudFront"
    from boto.cloudfront import CloudFrontConnection
    from boto.cloudfront.origin import CustomOrigin

    c = CloudFrontConnection(env.aws_access_key_id,
                             env.aws_secret_access_key)
    d = c.create_distribution(
        origin=CustomOrigin(slug + '.cdn.readthedocs.org',
                            origin_protocol_policy='http-only'),
        enabled=True,
        comment='Slug: ' + slug,
        cnames=[slug + '.readthedocs.org']
    )
    print "Created: " + d.domain_name + " for " + slug
    list_cdn()


@_aws_wrapper
def list_cdn(c):
    "List Distributions on CloudFront"
    distributions = c.get_all_distributions()
    for d in distributions:
        print "%3s %4s %40s %30s" % ('Ena' if d.enabled else 'Dis',
                                     d.status[:4], d.origin.dns_name,
                                     d.domain_name)


@_aws_wrapper
def disable_cdn(c, *args):
    "Sets a Distribution entry to disabled. Required before deletion."
    distributions = c.get_all_distributions()
    for distro in distributions:
        dist_slug = distro.origin.dns_name.split('.')[0]
        if dist_slug in args:
            print "Disabling:", dist_slug
            #this is broken as of boto 2.0b4.
            #fix is to comment out lines 347-352 in cloudfront/distribution.py
            distro.get_distribution().disable()


@_aws_wrapper
def delete_cdn(c):
    "Deletes all Distributions in the 'Disabled' state."
    distributions = c.get_all_distributions()
    for distro in distributions:
        if not distro.enabled and distro.status == "Deployed":
            print "Deleting", distro.origin.dns_name
            distro.get_distribution().delete()


def full_deploy():
    #HACK
    #Call this again at the top-level so the hosts decorator
    #effects the hosts it runs against for each command.
    run('fab push update_requirements migrate restart celery')
    #push()
    #update_requirements()
    #migrate()
    #restart()
    #celery()


@hosts(['newchimera.readthedocs.com'])
def uptime():
    run('uptime')


@hosts(['newchimera.readthedocs.com'])
def update_index():
    run('django-admin.py update_index')

@hosts('None')
def update_theme():
    theme_dir = os.path.join(fabfile_dir, 'readthedocs', 'templates', 'sphinx')
    if not os.path.exists('/tmp/sphinx_rtd_theme'):
        local('git clone https://github.com/snide/sphinx_rtd_theme.git /tmp/sphinx_rtd_theme')
    with lcd('/tmp/sphinx_rtd_theme'):
        local('git remote update')
        local('git reset --hard origin/master ')
        local('cp -r /tmp/sphinx_rtd_theme/sphinx_rtd_theme %s' % theme_dir)
        local('cp -r /tmp/sphinx_rtd_theme/sphinx_rtd_theme/static/fonts/ %s' % os.path.join(fabfile_dir, 'media', 'font'))
        local('cp /tmp/sphinx_rtd_theme/sphinx_rtd_theme/static/css/badge_only.css %s' % os.path.join(fabfile_dir, 'media', 'css'))
        local('cp /tmp/sphinx_rtd_theme/sphinx_rtd_theme/static/css/theme.css %s' % os.path.join(fabfile_dir, 'media', 'css', 'sphinx_rtd_theme.css'))
