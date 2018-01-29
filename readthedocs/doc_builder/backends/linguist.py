from __future__ import absolute_import
import json
import logging
import os
import re

from readthedocs.projects.utils import safe_write
from ..base import BaseBuilder
from ..environments import BuildCommand

log = logging.getLogger(__name__)


class LinguistBuilder(BaseBuilder):

    """Linguist builder which generates a programming language breakdown."""

    type = 'linguist'
    builder = 'build'
    build_dir = '_build/linguist'

    LINGUIST_COMMAND_LOCAL = 'linguist'
    LINGUIST_COMMAND_DOCKER = 'github-linguist'

    LINGUIST_OUTPUT_REGEX = re.compile(
        r'^(?P<percentage>\d+\.\d+)\%\s+(?P<language>.+)$',
        re.MULTILINE,
    )

    def __init__(self, *args, **kwargs):
        super(LinguistBuilder, self).__init__(*args, **kwargs)
        self.root_path = self.version.project.checkout_path(self.version.slug)
        self.old_artifact_path = os.path.join(self.root_path, self.build_dir)
        self.output_dir = self.old_artifact_path

        # Outputs
        self.linguist_txt_path = os.path.join(self.output_dir, 'linguist.txt')
        self.linguist_json_path = os.path.join(self.output_dir, 'linguist.json')
        self.linguist_error_path = os.path.join(self.output_dir, 'linguist-error.txt')

    def _parse_linguist_output(self, output):
        data = self.LINGUIST_OUTPUT_REGEX.findall(output)
        return [(float(perc), lang) for perc, lang in data]

    def _save_linguist_output(self, output):
        safe_write(self.linguist_txt_path, output)

        # Parse the language breakdown for easier consumption
        safe_write(self.linguist_json_path, json.dumps(
            self._parse_linguist_output(output)
        ))

    def _save_linguist_error(self, output):
        safe_write(self.linguist_error_path, output)

    def build(self):
        if self.build_env.command_class == BuildCommand:
            command = self.LINGUIST_COMMAND_LOCAL
        else:
            command = self.LINGUIST_COMMAND_DOCKER

        cmd_ret = self.run(
            command,
            cwd=self.root_path,
            warn_only=True,
        )

        if cmd_ret.successful and cmd_ret.output:
            self._save_linguist_output(cmd_ret.output)
        else:
            # Override command failure - do not fail the build
            cmd_ret.exit_code = 0
            log.warning('Linguist did not run successfully. This does not fail the build.')
            self._save_linguist_error(cmd_ret.output)

        # We never want to fail a build because Linguist failed or isn't installed
        return True
