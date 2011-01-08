import datetime
from fabric.api import *
from fabric.contrib import files, console

env.runtime = 'production'
env.hosts = ['chimera.ericholscher.com']
env.user = 'docs'
env.code_dir = '/home/docs/sites/readthedocs.org/checkouts/readthedocs.org'
env.virtualenv = '/home/docs/sites/readthedocs.org'
env.rundir = '/home/docs/sites/readthedocs.org/run'

def update_requirements():
    "Update requirements in the virtualenv."
    run("%s/bin/pip install -r %s/deploy_requirements.txt" % (env.virtualenv, env.code_dir))

def push():
    "Push new code, but don't restart/reload."
    local('git push origin master')
    with cd(env.code_dir):
        run('git pull origin master')

def pull():
    "Pull new code"
    with cd(env.code_dir):
        run('git pull origin master')

def restart():
    "Restart (or just start) the server"
    env.user = "root"
    run("restart readthedocs-gunicorn")

def migrate(project):
    run('django-admin.py migrate %s' % project)
