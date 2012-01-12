from fabric.api import *
from fabric.decorators import runs_once

env.runtime = 'production'
env.hosts = ['chimera.ericholscher.com', 'ladon.ericholscher.com', 'build.ericholscher.com']
env.user = 'docs'
env.code_dir = '/home/docs/sites/readthedocs.org/checkouts/readthedocs.org'
env.virtualenv = '/home/docs/sites/readthedocs.org'
env.rundir = '/home/docs/sites/readthedocs.org/run'

def push():
    "Push new code, but don't restart/reload."
    local('git push origin master')
    with cd(env.code_dir):
        run('git fetch')
        run('git reset --hard origin/master')

def update_requirements():
    "Update requirements in the virtualenv."
    run("%s/bin/pip install -r %s/deploy_requirements.txt" % (env.virtualenv, env.code_dir))

@hosts(['chimera.ericholscher.com'])
def migrate(project=None):
    if project:
        run('django-admin.py migrate %s' % project)
    else:
        run('django-admin.py migrate')

@hosts(['chimera.ericholscher.com', 'ladon.ericholscher.com'])
def restart():
    "Restart (or just start) the server"
    env.user = "root"
    run("restart readthedocs-gunicorn")

@hosts(['build.ericholscher.com'])
#@hosts(['kirin.ericholscher.com'])
def celery():
    "Restart (or just start) the server"
    env.user = "root"
    run("restart readthedocs-celery")

def pull():
    "Pull new code"
    with cd(env.code_dir):
        run('git pull origin master')

@runs_once
def spider():
    local('patu.py -d1 readthedocs.org')

def _aws_wrapper(f, *args, **kwargs):
    "get AWS credentials if not defined"
    #these are normally defined in ~/.fabricrc
    @hosts('run_once') #so fab doesn't go crazy
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
        if not distro.enabled and distro.status=="Deployed":
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

@hosts(['chimera.ericholscher.com'])
def uptime():
    run('uptime')

@hosts(['chimera.ericholscher.com'])
def update_index():
    run('django-admin.py update_index')
