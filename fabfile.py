import datetime
from fabric.api import *
from fabric.contrib import files, console

env.runtime = 'production'
env.hosts = ['readthedocs.org']
env.user = 'docs'
env.code_dir = '/home/docs/sites/readthedocs.com/checkouts/tweezers'
env.virtualenv = '/home/docs/sites/readthedocs.com'
env.rundir = '/home/docs/sites/readthedocs.com/run'

def update_requirements():
    "Update requirements in the virtualenv."
    run("%s/bin/pip install -r %s/pip_requirements.txt" % (env.virtualenv, env.code_dir))

def push():
    "Push new code, but don't restart/reload."
    local('git push origin master')
    with cd(env.code_dir):
        run('git pull origin master')

def reload():
    "Reload the server."
    with cd(env.code_dir):
        run("kill -HUP `cat %s/gunicorn.pid`" % env.rundir)

def restart():
    "Restart (or just start) the server"
    run("~/run_gunicorn.sh")
