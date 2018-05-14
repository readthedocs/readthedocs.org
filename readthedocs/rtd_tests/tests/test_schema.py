from os import path
from os import getcwd

from django.test import TestCase
import yamale
import pytest

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

    def test_minimal_config(self):
        file = self.create_yaml('')
        data = yamale.make_data(file)
        yamale.validate(self.schema, data)

    def test_valid_config(self):
        file = self.create_yaml('version: "2"')
        data = yamale.make_data(file)
        yamale.validate(self.schema, data)
