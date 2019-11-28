from invoke import task

DOCKER_COMPOSE = 'docker-compose.yml'
DOCKER_COMPOSE_SEARCH = 'docker-compose-search.yml'
DOCKER_COMPOSE_COMMAND = f'docker-compose -f {DOCKER_COMPOSE} -f {DOCKER_COMPOSE_SEARCH}'

@task
def build(c):
    c.run(f'{DOCKER_COMPOSE_COMMAND} build --no-cache', pty=True)

@task
def down(c):
    c.run(f'{DOCKER_COMPOSE_COMMAND} down', pty=True)

@task
def up(c, no_search=False):
    if no_search:
        c.run(f'docker-compose -f {DOCKER_COMPOSE} up', pty=True)
    else:
        c.run(f'{DOCKER_COMPOSE_COMMAND} up', pty=True)

@task
def shell(c, running=False, container='web'):
    if running:
        c.run(f'{DOCKER_COMPOSE_COMMAND} exec {container} /bin/bash', pty=True)
    else:
        c.run(f'{DOCKER_COMPOSE_COMMAND} run --rm {container} /bin/bash', pty=True)

@task
def manage(c, command):
    c.run(f'{DOCKER_COMPOSE_COMMAND} run --rm web python3 manage.py {command}', pty=True)

@task
def attach(c, container):
    c.run(f'docker attach readthedocsorg_{container}_1', pty=True)

@task
def restart(c, containers):
    c.run(f'{DOCKER_COMPOSE_COMMAND} restart {containers}', pty=True)

    # When restarting a container that nginx is connected to, we need to restart
    # nginx as well because it has the IP cached
    need_nginx_restart = [
        'web',
        'proxito'
        'storage',
    ]
    for extra in need_nginx_restart:
        if extra in containers:
            c.run(f'{DOCKER_COMPOSE_COMMAND} restart nginx', pty=True)
            break
