# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
import json
import gc
import logging

from django.db import models, migrations

log = logging.getLogger(__name__)


def chunks(queryset, chunksize=1000):
    pk = 0
    queryset = queryset.order_by('pk')
    last_instance = queryset.last()
    if last_instance is not None:
        last_pk = last_instance.pk
        while pk < last_pk:
            for row in queryset.filter(pk__gt=pk)[:chunksize]:
                pk = row.pk
                yield row
            gc.collect()


def forwards_move_repos(apps, schema_editor):
    """Moves OAuth repos"""
    db = schema_editor.connection.alias

    # Organizations
    GithubOrganization = apps.get_model('oauth', 'GithubOrganization')
    BitbucketTeam = apps.get_model('oauth', 'BitbucketTeam')
    RemoteOrganization = apps.get_model('oauth', 'RemoteOrganization')
    for org in chunks(GithubOrganization.objects.all()):
        new_org = RemoteOrganization.objects.using(db).create(
            pub_date=org.pub_date,
            modified_date=org.modified_date,
            active=org.active,
            slug=org.login,
            name=org.name,
            email=org.email,
            url=org.html_url,
            source='github',
        )
        for user in org.users.iterator():
            new_org.users.add(user)
        try:
            data = eval(org.json)
            new_org.avatar_url = data['avatar_url']
            new_org.json = json.dumps(data)
        except:
            pass
        new_org.save()
        log.info('Migrated organization: %s', org.name)

    for org in chunks(BitbucketTeam.objects.all()):
        new_org = RemoteOrganization.objects.using(db).create(
            pub_date=org.pub_date,
            modified_date=org.modified_date,
            active=org.active,
            slug=org.login,
            name=org.name,
            email=org.email,
            url=org.html_url,
            source='bitbucket',
        )
        for user in org.users.iterator():
            new_org.users.add(user)
        try:
            new_org.json = json.dumps(eval(org.json))
        except:
            pass
        new_org.save()
        log.info('Migrated organization: %s', org.name)

    # Now repositories
    GithubProject = apps.get_model('oauth', 'GithubProject')
    BitbucketProject = apps.get_model('oauth', 'BitbucketProject')
    RemoteRepository = apps.get_model('oauth', 'RemoteRepository')

    for project in chunks(GithubProject.objects.all()):
        new_repo = RemoteRepository.objects.using(db).create(
            pub_date=project.pub_date,
            modified_date=project.modified_date,
            active=project.active,
            name=project.name,
            full_name=project.full_name,
            description=project.description,
            ssh_url=project.ssh_url,
            html_url=project.html_url,
            vcs='git',
            source='github',
        )
        for user in project.users.iterator():
            new_repo.users.add(user)
        if project.organization is not None:
            new_repo.organization = (RemoteOrganization
                                    .objects
                                    .using(db)
                                    .get(slug=project.organization.login))
        try:
            data = eval(project.json)
            new_repo.avatar_url = data.get('owner', {}).get('avatar_url', None)
            new_repo.admin = data.get('permissions', {}).get('admin', False)
            new_repo.private = data.get('private', False)
            if new_repo.private:
                new_repo.clone_url = data.get('ssh_url')
            else:
                new_repo.clone_url = data.get('clone_url')
            new_repo.json = json.dumps(data)
        except (SyntaxError, ValueError) as e:
            pass
        new_repo.save()
        log.info('Migrated project: %s', project.name)

    for project in chunks(BitbucketProject.objects.all()):
        new_repo = RemoteRepository.objects.using(db).create(
            pub_date=project.pub_date,
            modified_date=project.modified_date,
            active=project.active,
            name=project.name,
            full_name=project.full_name,
            description=project.description,
            ssh_url=project.ssh_url,
            html_url=project.html_url,
            admin=False,
            vcs=project.vcs,
            source='bitbucket',
        )
        for user in project.users.iterator():
            new_repo.users.add(user)
        if project.organization is not None:
            new_repo.organization = (RemoteOrganization
                                    .objects
                                    .using(db)
                                    .get(slug=project.organization.login))
        try:
            data = eval(project.json)
            new_repo.avatar_url = (data.get('links', {})
                                   .get('avatar', {})
                                   .get('href', None))
            new_repo.private = data.get('is_private', False)
            new_repo.json = json.dumps(data)

            clone_urls = dict((location['name'], location['href'])
                              for location
                              in data.get('links', {}).get('clone', {}))
            if new_repo.private:
                new_repo.clone_url = clone_urls.get('ssh', project.git_url)
            else:
                new_repo.clone_url = clone_urls.get('https', project.html_url)
        except (SyntaxError, ValueError) as e:
            pass
        new_repo.save()
        log.info('Migrated project: %s', project.name)


def reverse_move_repos(apps, schema_editor):
    """Drop OAuth repos"""
    db = schema_editor.connection.alias
    RemoteRepository = apps.get_model('oauth', 'RemoteRepository')
    RemoteOrganization = apps.get_model('oauth', 'RemoteOrganization')
    RemoteRepository.objects.using(db).delete()
    RemoteOrganization.objects.using(db).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0002_combine_services'),
    ]

    operations = [
        migrations.RunPython(forwards_move_repos, reverse_move_repos),
    ]
