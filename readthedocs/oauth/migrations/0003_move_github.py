# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db import models, migrations


def forwards_move_repos(apps, schema_editor):
    """Moves OAuth repos"""
    db = schema_editor.connection.alias

    # Organizations
    GithubOrganization = apps.get_model('oauth', 'GithubOrganization')
    BitbucketTeam = apps.get_model('oauth', 'BitbucketTeam')
    OAuthOrganization = apps.get_model('oauth', 'OAuthOrganization')
    for org in GithubOrganization.objects.all():
        new_org = OAuthOrganization.objects.using(db).create(
            pub_date=org.pub_date,
            modified_date=org.modified_date,
            active=org.active,
            slug=org.login,
            name=org.name,
            email=org.email,
            url=org.html_url,
            source='github',
        )
        for user in org.users.all():
            new_org.users.add(user)
        try:
            data = eval(org.json)
            new_org.avatar_url = data['avatar_url']
            new_org.json = json.dumps(data)
        except:
            pass
        new_org.save()

    for org in BitbucketTeam.objects.all():
        new_org = OAuthOrganization.objects.using(db).create(
            pub_date=org.pub_date,
            modified_date=org.modified_date,
            active=org.active,
            slug=org.login,
            name=org.name,
            email=org.email,
            url=org.html_url,
            source='bitbucket',
        )
        for user in org.users.all():
            new_org.users.add(user)
        try:
            new_org.json = json.dumps(eval(org.json))
        except:
            pass
        new_org.save()

    # Now repositories
    GithubProject = apps.get_model('oauth', 'GithubProject')
    BitbucketProject = apps.get_model('oauth', 'BitbucketProject')
    OAuthRepository = apps.get_model('oauth', 'OAuthRepository')

    for project in GithubProject.objects.all():
        new_repo = OAuthRepository.objects.using(db).create(
            pub_date=project.pub_date,
            modified_date=project.modified_date,
            active=project.active,
            name=project.name,
            full_name=project.full_name,
            description=project.description,
            ssh_url=project.ssh_url,
            clone_url=project.git_url,
            html_url=project.html_url,
            vcs='git',
            source='github',
        )
        for user in project.users.all():
            new_repo.users.add(user)
        if project.organization is not None:
            new_repo.organization = (OAuthOrganization
                                    .objects
                                    .using(db)
                                    .get(slug=project.organization.login))
        try:
            data = eval(project.json)
            new_repo.avatar_url = data.get('owner', {}).get('avatar_url', None)
            new_repo.admin = data.get('permissions', {}).get('admin', False)
            new_repo.private = data.get('private', False)
            new_repo.json = json.dumps(data)
        except:
            pass
        new_repo.save()

    for project in BitbucketProject.objects.all():
        new_repo = OAuthRepository.objects.using(db).create(
            pub_date=project.pub_date,
            modified_date=project.modified_date,
            active=project.active,
            name=project.name,
            full_name=project.full_name,
            description=project.description,
            ssh_url=project.ssh_url,
            clone_url=project.git_url,
            html_url=project.html_url,
            admin=False,
            vcs=project.vcs,
            source='bitbucket',
        )
        for user in project.users.all():
            new_repo.users.add(user)
        if project.organization is not None:
            new_repo.organization = (OAuthOrganization
                                    .objects
                                    .using(db)
                                    .get(slug=project.organization.login))
        try:
            data = eval(project.json)
            new_repo.avatar_url = data.get('avatar', {}).get('href', None)
            new_repo.private = data.get('is_private', False)
            new_repo.json = json.dumps(data)
        except:
            pass
        new_repo.save()


def reverse_move_repos(apps, schema_editor):
    """Drop OAuth repos"""
    db = schema_editor.connection.alias
    OAuthRepository = apps.get_model('oauth', 'OAuthRepository')
    OAuthOrganization = apps.get_model('oauth', 'OAuthOrganization')
    OAuthRepository.objects.using(db).delete()
    OAuthOrganization.objects.using(db).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0002_combine_services'),
    ]

    operations = [
        migrations.RunPython(forwards_move_repos, reverse_move_repos),
    ]
