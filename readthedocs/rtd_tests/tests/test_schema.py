from os import getcwd, path

import pytest
import yamale
from django.test import TestCase
from readthedocs.rtd_tests.utils import apply_fs


class TestSchemaV2(TestCase):

    def setUp(self):
        base_path = path.join(getcwd(), 'rtd_tests/fixtures/spec/v2')
        self.schema = yamale.make_schema(
            path.join(base_path, 'schema.yml')
        )

    @pytest.fixture(autouse=True)
    def tmpdir(self, tmpdir):
        self.tmpdir = tmpdir

    def create_yaml(self, content):
        file = {
            'rtd.yml': content,
        }
        apply_fs(self.tmpdir, file)
        return path.join(self.tmpdir.strpath, 'rtd.yml')

    def assertValidConfig(self, content):
        file = self.create_yaml(content)
        data = yamale.make_data(file)
        yamale.validate(self.schema, data)

    def assertInvalidConfig(self, content, msgs=()):
        file = self.create_yaml(content)
        data = yamale.make_data(file)
        with pytest.raises(ValueError) as excinfo:
            yamale.validate(self.schema, data)
        for msg in msgs:
            self.assertIn(msg, str(excinfo.value))

    def test_minimal_config(self):
        self.assertValidConfig('version: "2"')

    def test_invalid_version(self):
        self.assertInvalidConfig(
            'version: "latest"',
            ['version: \'latest\' not in']
        )

    def test_invalid_version_1(self):
        self.assertInvalidConfig(
            'version: "1"',
            ['version: \'1\' not in']
        )

    def test_valid_formats(self):
        content = '''
version: "2"
formats:
  - pdf
  - singlehtmllocalmedia
        '''
        self.assertValidConfig(content)

    def test_invalid_formats(self):
        content = '''
version: "2"
formats:
  - invalidformat
  - singlehtmllocalmedia
        '''
        self.assertInvalidConfig(
            content,
            ['formats', '\'invalidformat\' not in']
        )

    def tets_empty_formats(self):
        content = '''
version: "2"
formats: []
        '''
        self.assertValidConfig(content)
