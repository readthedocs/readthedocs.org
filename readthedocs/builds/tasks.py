
from __future__ import absolute_import

import datetime
import hashlib
import json
import logging
import os
import shutil
import socket
from collections import defaultdict

import requests
from builtins import str
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from readthedocs_build.config import ConfigError
from slumber.exceptions import HttpClientError

from readthedocs.builds.constants import (LATEST,
                                          BUILD_STATE_CLONING,
                                          BUILD_STATE_INSTALLING,
                                          BUILD_STATE_BUILDING,
                                          BUILD_STATE_FINISHED)
from readthedocs.builds.models import Build, Version, APIVersion
from readthedocs.builds.signals import build_complete
from readthedocs.builds.syncers import Syncer
from readthedocs.cdn.purge import purge
from readthedocs.core.resolver import resolve_path
from readthedocs.core.symlink import PublicSymlink, PrivateSymlink
from readthedocs.core.utils import send_email, broadcast
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.constants import DOCKER_LIMITS
from readthedocs.doc_builder.environments import (LocalBuildEnvironment,
                                                  DockerBuildEnvironment)
from readthedocs.doc_builder.exceptions import BuildEnvironmentError
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.doc_builder.python_environments import Virtualenv, Conda
from readthedocs.projects.models import APIProject
from readthedocs.restapi.client import api as api_v2
from readthedocs.restapi.utils import index_search_request
from readthedocs.search.parse_json import process_all_json_files
from readthedocs.vcs_support import utils as vcs_support_utils
from readthedocs.worker import app


log = logging.getLogger(__name__)

HTML_ONLY = getattr(settings, 'HTML_ONLY_PROJECTS', ())


@app.task(queue='web')
def fileify(version_pk, commit):
    """
    Create ImportedFile objects for all of a version's files.

    This is so we have an idea of what files we have in the database.
    """
    version = Version.objects.get(pk=version_pk)
    project = version.project

    if not commit:
        log.info(LOG_TEMPLATE
                 .format(project=project.slug, version=version.slug,
                         msg=('Imported File not being built because no commit '
                              'information')))
        return

    path = project.rtd_build_path(version.slug)
    if path:
        log.info(LOG_TEMPLATE
                 .format(project=version.project.slug, version=version.slug,
                         msg='Creating ImportedFiles'))
        _manage_imported_files(version, path, commit)
    else:
        log.info(LOG_TEMPLATE
                 .format(project=project.slug, version=version.slug,
                         msg='No ImportedFile files'))


