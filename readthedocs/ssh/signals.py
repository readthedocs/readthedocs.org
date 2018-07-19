# -*- coding: utf-8 -*-

"""Signals to use private/public keys before/after events."""

from __future__ import division, print_function, unicode_literals

import logging
import glob
import os
import re
import signal
import subprocess

from django.dispatch import receiver

from readthedocs.doc_builder.base import restoring_chdir
from readthedocs.projects.signals import after_vcs, before_vcs
from readthedocs.restapi.client import api

log = logging.getLogger(__name__)


@receiver(before_vcs)
@restoring_chdir
def setup_ssh_agent(sender, **kwargs):
    """
    Start SSH Agent for this process.

    Hit the API endpoint to retrieve all the SSH keys for this project and load
    them temporarily into the SSH agent using ``ssh-add`` command.
    """
    log.info('Setting up SSH Agent')
    version = sender
    key_path = os.path.join(version.project.doc_path, 'checkouts')
    if not os.path.exists(key_path):
        os.makedirs(key_path)
    os.chdir(key_path)

    log.info('Retrieving all SSH keys: project=%s', version.project.slug)
    keys = api.project(version.project.pk).keys.get()
    key_file_names = []
    for i, key in enumerate(keys):
        key_file_name = '{slug}-key-{number}'.format(slug=version.slug, number=i)
        key_file_names.append(key_file_name)

        # Set 600 as mod to be able to rewrite it in case it already exists
        if os.path.exists(key_file_name):
            os.system('chmod 600 {}'.format(key_file_name))

        with open(key_file_name, '+w') as fd:
            fd.write(key['private_key'])
        os.system('chmod 400 {}'.format(key_file_name))

    sh_cmds = subprocess.check_output(['ssh-agent', '-s']).decode('utf-8')
    for sh_line in sh_cmds.split('\n'):
        matches = re.search('(\S+)\=(\S+)\;', sh_line)
        if matches:
            os.environ[matches.group(1)] = matches.group(2)
    log.info('Adding %d keys to the agent', len(key_file_names))
    for key_file_name in key_file_names:
        os.system('ssh-add -t 30 {}'.format(key_file_name))


@receiver(after_vcs)
@restoring_chdir
def remove_ssh_agent(sender, **kwargs):
    """
    Delete SSH agent after checkout.

    Remove the SSH agent and delete from disk the key file saved in the setup.
    """
    version = sender
    key_path = os.path.join(version.project.doc_path, 'checkouts')
    os.chdir(key_path)
    key_file_name = '{slug}-key-*'.format(slug=version.slug)
    key_file_names = glob.glob(key_file_name)

    log.info('Removing %d keys from the agent', len(key_file_names))
    for key_file_name in key_file_names:
        os.remove(os.path.join(key_path, key_file_name))

    os.system('ssh-agent -k')
    try:
        pid = int(os.environ['SSH_AGENT_PID'])
        os.kill(pid, signal.SIGTERM)
    except (ValueError, KeyError, OSError):
        pass
    log.info(
        'Removing SSH Agent (pid=%s)',
        os.environ.get(
            'SSH_AGENT_PID',
            'unknown',
        ),
    )
    for key in ['SSH_AUTH_SOCK', 'SSH_AGENT_PID']:
        try:
            del os.environ[key]
        except KeyError:
            pass
