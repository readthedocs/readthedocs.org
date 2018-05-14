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

    def assertInvalidConfig(self, content, exc, msgs=()):
        file = self.create_yaml(content)
        data = yamale.make_data(file)
        with pytest.raises(exc) as excinfo:
            yamale.validate(self.schema, data)
        for msg in msgs:
            self.assertIn(msg, str(excinfo.value))

    def test_minimal_config(self):
        self.assertValidConfig('')

    def test_valid_version(self):
        self.assertValidConfig('version: "2"')

    def test_invalid_versin(self):
        self.assertInvalidConfig(
            'version: "latest"',
            ValueError,
            ['version: \'latest\' not in']
        )
