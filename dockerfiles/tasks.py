from invoke import task

DOCKER_COMPOSE = 'docker-compose.yml'
DOCKER_COMPOSE_SEARCH = 'docker-compose-search.yml'
DOCKER_COMPOSE_COMMAND = f'docker-compose -f {DOCKER_COMPOSE} -f {DOCKER_COMPOSE_SEARCH}'

@task
def build(c):
    """Build docker image for servers."""
    c.run(f'{DOCKER_COMPOSE_COMMAND} build --no-cache', pty=True)

@task
def down(c, volumes=False):
    """Stop and remove all the docker containers."""
    if volumes:
        c.run(f'{DOCKER_COMPOSE_COMMAND} down -v', pty=True)
    else:
        c.run(f'{DOCKER_COMPOSE_COMMAND} down', pty=True)


@task
def up(c, no_search=False, init=False, no_reload=False):
    """Start all the docker containers for a Read the Docs instance"""
    INIT = 'INIT='
    DOCKER_NO_RELOAD = 'DOCKER_NO_RELOAD='
    if init:
        INIT = 'INIT=t'
    if no_reload:
        DOCKER_NO_RELOAD = 'DOCKER_NO_RELOAD=t'

    if no_search:
        c.run(f'{INIT} {DOCKER_NO_RELOAD} docker-compose -f {DOCKER_COMPOSE} up', pty=True)
    else:
        c.run(f'{INIT} {DOCKER_NO_RELOAD} {DOCKER_COMPOSE_COMMAND} up', pty=True)


@task
def start(c, no_search=False, no_reload=False):
    """Start all containers for a Read the Docs instance"""
    DOCKER_NO_RELOAD = 'DOCKER_NO_RELOAD='
    if no_reload:
        DOCKER_NO_RELOAD = 'DOCKER_NO_RELOAD=t'

    if no_search:
        c.run(f'{DOCKER_NO_RELOAD} docker-compose -f {DOCKER_COMPOSE} start', pty=True)
    else:
        c.run(f'{DOCKER_NO_RELOAD} {DOCKER_COMPOSE_COMMAND} start', pty=True)


@task
def stop(c):
    """Stop all running containers."""
    c.run(f'{DOCKER_COMPOSE_COMMAND} stop', pty=True)


@task
def shell(c, running=False, container='web'):
    """Run a shell inside a container."""
    if running:
        c.run(f'{DOCKER_COMPOSE_COMMAND} exec {container} /bin/bash', pty=True)
    else:
        c.run(f'{DOCKER_COMPOSE_COMMAND} run --rm {container} /bin/bash', pty=True)

@task
def manage(c, command):
    """Run manage.py with a specific command."""
    c.run(f'{DOCKER_COMPOSE_COMMAND} run --rm web python3 manage.py {command}', pty=True)

@task
def attach(c, container):
    """Attach a tty to a running container (useful for pdb)."""
    c.run(f'docker attach readthedocsorg_{container}_1', pty=True)

@task
def restart(c, containers):
    """Restart one or more containers."""
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

@task
def pull(c):
    """Pull all docker images required for build servers."""
    images = [
        ('4.0', 'stable'),
        ('5.0', 'latest'),
    ]
    for image, tag in images:
        c.run(f'docker pull readthedocs/build:{image}', pty=True)
        c.run(f'docker tag readthedocs/build:{image} readthedocs/build:{tag}', pty=True)

@task
def test(c, arguments=''):
    """Run all test suite."""
    c.run(f'{DOCKER_COMPOSE_COMMAND} run --rm --no-deps web tox {arguments}', pty=True)
