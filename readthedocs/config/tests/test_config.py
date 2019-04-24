import os
import re
import textwrap
from collections import OrderedDict

import pytest
from mock import DEFAULT, patch
from pytest import raises

from readthedocs.config import (
    ALL,
    PIP,
    SETUPTOOLS,
    BuildConfigV1,
    BuildConfigV2,
    ConfigError,
    ConfigFileNotFound,
    ConfigOptionNotSupportedError,
    InvalidConfig,
    load,
)
from readthedocs.config.config import (
    CONFIG_FILE_REQUIRED,
    CONFIG_FILENAME_REGEX,
    CONFIG_NOT_SUPPORTED,
    CONFIG_REQUIRED,
    CONFIG_SYNTAX_INVALID,
    INVALID_KEY,
    PYTHON_INVALID,
    VERSION_INVALID,
)
from readthedocs.config.models import (
    Conda,
    PythonInstall,
    PythonInstallRequirements,
)
from readthedocs.config.validation import (
    INVALID_BOOL,
    INVALID_CHOICE,
    INVALID_LIST,
    VALUE_NOT_FOUND,
    ValidationError,
)

from .utils import apply_fs


yaml_config_dir = {
    'readthedocs.yml': textwrap.dedent(
        '''
        formats:
          - pdf
        '''
    ),
}


def get_build_config(config, env_config=None, source_file='readthedocs.yml'):
    return BuildConfigV1(
        env_config or {},
        config,
        source_file=source_file,
    )


@pytest.mark.parametrize(
    'files', [
        {'readthedocs.ymlmore': ''}, {'first': {'readthedocs.yml': ''}},
        {'startreadthedocs.yml': ''}, {'second': {'confuser.txt': 'content'}},
        {'noroot': {'readthedocs.ymlmore': ''}}, {'third': {'readthedocs.yml': 'content', 'Makefile': ''}},
        {'noroot': {'startreadthedocs.yml': ''}}, {'fourth': {'samplefile.yaml': 'content'}},
        {'readthebots.yaml': ''}, {'fifth': {'confuser.txt': '', 'readthedocs.yml': 'content'}},
    ],
)
def test_load_no_config_file(tmpdir, files):
    apply_fs(tmpdir, files)
    base = str(tmpdir)
    with raises(ConfigFileNotFound) as e:
        load(base, {})
    assert e.value.code == CONFIG_FILE_REQUIRED


def test_load_empty_config_file(tmpdir):
    apply_fs(
        tmpdir, {
            'readthedocs.yml': '',
        },
    )
    base = str(tmpdir)
    with raises(ConfigError):
        load(base, {})


def test_minimal_config(tmpdir):
    apply_fs(tmpdir, yaml_config_dir)
    base = str(tmpdir)
    build = load(base, {})
    assert isinstance(build, BuildConfigV1)


def test_load_version1(tmpdir):
    apply_fs(
        tmpdir, {
            'readthedocs.yml': textwrap.dedent('''
            version: 1
        '''),
        },
    )
    base = str(tmpdir)
    build = load(base, {})
    assert isinstance(build, BuildConfigV1)


def test_load_version2(tmpdir):
    apply_fs(
        tmpdir, {
            'readthedocs.yml': textwrap.dedent('''
            version: 2
        '''),
        },
    )
    base = str(tmpdir)
    build = load(base, {})
    assert isinstance(build, BuildConfigV2)


def test_load_unknow_version(tmpdir):
    apply_fs(
        tmpdir, {
            'readthedocs.yml': textwrap.dedent('''
            version: 9
        '''),
        },
    )
    base = str(tmpdir)
    with raises(ConfigError) as excinfo:
        load(base, {})
    assert excinfo.value.code == VERSION_INVALID


def test_load_raise_exception_invalid_syntax(tmpdir):
    apply_fs(
        tmpdir, {
            'readthedocs.yml': textwrap.dedent('''
                version: 2
                python:
                  install:
                    - method: pip
                      path: .
                        # bad indentation here
                        extra_requirements:
                          - build
            '''),
        },
    )
    base = str(tmpdir)
    with raises(ConfigError) as excinfo:
        load(base, {})
    assert excinfo.value.code == CONFIG_SYNTAX_INVALID


def test_yaml_extension(tmpdir):
    """Make sure loading the 'readthedocs' file with a 'yaml' extension."""
    apply_fs(
        tmpdir, {
            'readthedocs.yaml': textwrap.dedent(
                '''
            python:
              version: 3
            '''
            ),
        },
    )
    base = str(tmpdir)
    config = load(base, {})
    assert isinstance(config, BuildConfigV1)


def test_build_config_has_source_file(tmpdir):
    base = str(apply_fs(tmpdir, yaml_config_dir))
    build = load(base, {})
    assert build.source_file == os.path.join(base, 'readthedocs.yml')


def test_build_config_has_list_with_single_empty_value(tmpdir):
    base = str(apply_fs(
        tmpdir, {
            'readthedocs.yml': textwrap.dedent(
                '''
            formats: []
            '''
            ),
        },
    ))
    build = load(base, {})
    assert isinstance(build, BuildConfigV1)
    assert build.formats == []


def test_version():
    build = get_build_config({})
    assert build.version == '1'


def test_doc_type():
    build = get_build_config(
        {},
        {
            'defaults': {
                'doctype': 'sphinx',
            },
        },
    )
    build.validate()
    assert build.doctype == 'sphinx'


def test_empty_python_section_is_valid():
    build = get_build_config({'python': {}})
    build.validate()
    assert build.python


def test_python_section_must_be_dict():
    build = get_build_config({'python': 123})
    with raises(InvalidConfig) as excinfo:
        build.validate()
    assert excinfo.value.key == 'python'
    assert excinfo.value.code == PYTHON_INVALID


def test_use_system_site_packages_defaults_to_false():
    build = get_build_config({'python': {}})
    build.validate()
    # Default is False.
    assert not build.python.use_system_site_packages


@pytest.mark.parametrize('value', [True, False])
def test_use_system_site_packages_repects_default_value(value):
    defaults = {
        'use_system_packages': value,
    }
    build = get_build_config({}, {'defaults': defaults})
    build.validate()
    assert build.python.use_system_site_packages is value



class TestValidatePythonExtraRequirements:

    def test_it_defaults_to_install_requirements_as_none(self):
        build = get_build_config({'python': {}})
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert isinstance(install[0], PythonInstallRequirements)
        assert install[0].requirements is None

    def test_it_validates_is_a_list(self):
        build = get_build_config(
            {'python': {'extra_requirements': 'invalid'}},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.extra_requirements'
        assert excinfo.value.code == PYTHON_INVALID

    @patch('readthedocs.config.config.validate_string')
    def test_it_uses_validate_string(self, validate_string):
        validate_string.return_value = True
        build = get_build_config(
            {
                'python': {
                    'pip_install': True,
                    'extra_requirements': ['tests'],
                },
            },
        )
        build.validate()
        validate_string.assert_any_call('tests')


class TestValidateUseSystemSitePackages:

    def test_it_defaults_to_false(self):
        build = get_build_config({'python': {}})
        build.validate()
        assert build.python.use_system_site_packages is False

    def test_it_validates_value(self):
        build = get_build_config(
            {'python': {'use_system_site_packages': 'invalid'}},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        excinfo.value.key = 'python.use_system_site_packages'
        excinfo.value.code = INVALID_BOOL

    @patch('readthedocs.config.config.validate_bool')
    def test_it_uses_validate_bool(self, validate_bool):
        validate_bool.return_value = True
        build = get_build_config(
            {'python': {'use_system_site_packages': 'to-validate'}},
        )
        build.validate()
        validate_bool.assert_any_call('to-validate')


class TestValidateSetupPyInstall:

    def test_it_defaults_to_false(self):
        build = get_build_config({'python': {}})
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert isinstance(install[0], PythonInstallRequirements)
        assert install[0].requirements is None

    def test_it_validates_value(self):
        build = get_build_config(
            {'python': {'setup_py_install': 'this-is-string'}},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.setup_py_install'
        assert excinfo.value.code == INVALID_BOOL

    @patch('readthedocs.config.config.validate_bool')
    def test_it_uses_validate_bool(self, validate_bool):
        validate_bool.return_value = True
        build = get_build_config(
            {'python': {'setup_py_install': 'to-validate'}},
        )
        build.validate()
        validate_bool.assert_any_call('to-validate')


class TestValidatePythonVersion:

    def test_it_defaults_to_a_valid_version(self):
        build = get_build_config({'python': {}})
        build.validate()
        assert build.python.version == 2
        assert build.python_interpreter == 'python2.7'
        assert build.python_full_version == 2.7

    def test_it_supports_other_versions(self):
        build = get_build_config(
            {'python': {'version': 3.5}},
        )
        build.validate()
        assert build.python.version == 3.5
        assert build.python_interpreter == 'python3.5'
        assert build.python_full_version == 3.5

    def test_it_validates_versions_out_of_range(self):
        build = get_build_config(
            {'python': {'version': 1.0}},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.version'
        assert excinfo.value.code == INVALID_CHOICE

    def test_it_validates_wrong_type(self):
        build = get_build_config(
            {'python': {'version': 'this-is-string'}},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.version'
        assert excinfo.value.code == INVALID_CHOICE

    def test_it_validates_wrong_type_right_value(self):
        build = get_build_config(
            {'python': {'version': '3.5'}},
        )
        build.validate()
        assert build.python.version == 3.5
        assert build.python_interpreter == 'python3.5'
        assert build.python_full_version == 3.5

        build = get_build_config(
            {'python': {'version': '3'}},
        )
        build.validate()
        assert build.python.version == 3
        assert build.python_interpreter == 'python3.7'
        assert build.python_full_version == 3.7

    def test_it_validates_env_supported_versions(self):
        build = get_build_config(
            {'python': {'version': 3.6}},
            env_config={
                'python': {'supported_versions': [3.5]},
                'build': {'image': 'custom'},
            },
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.version'
        assert excinfo.value.code == INVALID_CHOICE

        build = get_build_config(
            {'python': {'version': 3.6}},
            env_config={
                'python': {'supported_versions': [3.5, 3.6]},
                'build': {'image': 'custom'},
            },
        )
        build.validate()
        assert build.python.version == 3.6
        assert build.python_interpreter == 'python3.6'
        assert build.python_full_version == 3.6

    @pytest.mark.parametrize('value', [2, 3])
    def test_it_respects_default_value(self, value):
        defaults = {
            'python_version': value,
        }
        build = get_build_config(
            {},
            {'defaults': defaults},
        )
        build.validate()
        assert build.python.version == value


class TestValidateFormats:

    def test_it_defaults_to_empty(self):
        build = get_build_config({})
        build.validate()
        assert build.formats == []

    def test_it_gets_set_correctly(self):
        build = get_build_config({'formats': ['pdf']})
        build.validate()
        assert build.formats == ['pdf']

    def test_formats_can_be_null(self):
        build = get_build_config({'formats': None})
        build.validate()
        assert build.formats == []

    def test_formats_with_previous_none(self):
        build = get_build_config({'formats': ['none']})
        build.validate()
        assert build.formats == []

    def test_formats_can_be_empty(self):
        build = get_build_config({'formats': []})
        build.validate()
        assert build.formats == []

    def test_all_valid_formats(self):
        build = get_build_config(
            {'formats': ['pdf', 'htmlzip', 'epub']},
        )
        build.validate()
        assert build.formats == ['pdf', 'htmlzip', 'epub']

    def test_cant_have_none_as_format(self):
        build = get_build_config(
            {'formats': ['htmlzip', None]},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'format'
        assert excinfo.value.code == INVALID_CHOICE

    def test_formats_have_only_allowed_values(self):
        build = get_build_config(
            {'formats': ['htmlzip', 'csv']},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'format'
        assert excinfo.value.code == INVALID_CHOICE

    def test_only_list_type(self):
        build = get_build_config({'formats': 'no-list'})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'format'
        assert excinfo.value.code == INVALID_LIST


def test_valid_build_config():
    build = BuildConfigV1(
        {},
        {},
        source_file='readthedocs.yml',
    )
    build.validate()
    assert build.python
    assert len(build.python.install) == 1
    assert isinstance(build.python.install[0], PythonInstallRequirements)
    assert build.python.install[0].requirements is None


class TestValidateBuild:

    def test_it_fails_if_build_is_invalid_option(self, tmpdir):
        apply_fs(tmpdir, yaml_config_dir)
        build = BuildConfigV1(
            {},
            {'build': {'image': 3.2}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'build'
        assert excinfo.value.code == INVALID_CHOICE

    def test_it_fails_on_python_validation(self, tmpdir):
        apply_fs(tmpdir, yaml_config_dir)
        build = BuildConfigV1(
            {},
            {
                'build': {'image': 1.0},
                'python': {'version': '3.3'},
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate_build()
        with raises(InvalidConfig) as excinfo:
            build.validate_python()
        assert excinfo.value.key == 'python.version'
        assert excinfo.value.code == INVALID_CHOICE

    def test_it_works_on_python_validation(self, tmpdir):
        apply_fs(tmpdir, yaml_config_dir)
        build = BuildConfigV1(
            {},
            {
                'build': {'image': 'latest'},
                'python': {'version': '3.6'},
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate_build()
        build.validate_python()

    def test_it_works(self, tmpdir):
        apply_fs(tmpdir, yaml_config_dir)
        build = BuildConfigV1(
            {},
            {'build': {'image': 'latest'}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        assert build.build.image == 'readthedocs/build:latest'

    def test_default(self, tmpdir):
        apply_fs(tmpdir, yaml_config_dir)
        build = BuildConfigV1(
            {},
            {},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        assert build.build.image == 'readthedocs/build:latest'

    @pytest.mark.parametrize(
        'image', ['latest', 'readthedocs/build:3.0', 'rtd/build:latest'],
    )
    def test_it_priorities_image_from_env_config(self, tmpdir, image):
        apply_fs(tmpdir, yaml_config_dir)
        defaults = {
            'build_image': image,
        }
        build = BuildConfigV1(
            {'defaults': defaults},
            {'build': {'image': 'latest'}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        assert build.build.image == image


def test_use_conda_default_none():
    build = get_build_config({})
    build.validate()
    assert build.conda is None


def test_validates_conda_file(tmpdir):
    apply_fs(tmpdir, {'environment.yml': ''})
    build = get_build_config(
        {'conda': {'file': 'environment.yml'}},
        source_file=str(tmpdir.join('readthedocs.yml')),
    )
    build.validate()
    assert isinstance(build.conda, Conda)
    assert build.conda.environment == str(tmpdir.join('environment.yml'))


def test_file_is_required_when_using_conda(tmpdir):
    apply_fs(tmpdir, {'environment.yml': ''})
    build = get_build_config(
        {'conda': {'foo': 'environment.yml'}},
        source_file=str(tmpdir.join('readthedocs.yml')),
    )
    with raises(InvalidConfig) as excinfo:
        build.validate()
    assert excinfo.value.key == 'conda.file'
    assert excinfo.value.code == VALUE_NOT_FOUND


def test_requirements_file_empty():
    build = get_build_config({})
    build.validate()
    install = build.python.install
    assert len(install) == 1
    assert install[0].requirements is None


def test_requirements_file_repects_default_value(tmpdir):
    apply_fs(tmpdir, {'myrequirements.txt': ''})
    defaults = {
        'requirements_file': 'myrequirements.txt',
    }
    build = get_build_config(
        {},
        {'defaults': defaults},
        source_file=str(tmpdir.join('readthedocs.yml')),
    )
    build.validate()
    install = build.python.install
    assert len(install) == 1
    assert install[0].requirements == str(tmpdir.join('myrequirements.txt'))


def test_requirements_file_respects_configuration(tmpdir):
    apply_fs(tmpdir, {'requirements.txt': ''})
    build = get_build_config(
        {'requirements_file': 'requirements.txt'},
        source_file=str(tmpdir.join('readthedocs.yml')),
    )
    build.validate()
    install = build.python.install
    assert len(install) == 1
    assert install[0].requirements == str(tmpdir.join('requirements.txt'))


def test_requirements_file_is_null(tmpdir):
    build = get_build_config(
        {'requirements_file': None},
        source_file=str(tmpdir.join('readthedocs.yml')),
    )
    build.validate()
    install = build.python.install
    assert len(install) == 1
    assert install[0].requirements is None


def test_requirements_file_is_blank(tmpdir):
    build = get_build_config(
        {'requirements_file': ''},
        source_file=str(tmpdir.join('readthedocs.yml')),
    )
    build.validate()
    install = build.python.install
    assert len(install) == 1
    assert install[0].requirements is None


def test_build_validate_calls_all_subvalidators(tmpdir):
    apply_fs(tmpdir, {})
    build = BuildConfigV1(
        {},
        {},
        source_file=str(tmpdir.join('readthedocs.yml')),
    )
    with patch.multiple(
            BuildConfigV1,
            validate_python=DEFAULT,
    ):
        build.validate()
        BuildConfigV1.validate_python.assert_called_with()


def test_load_calls_validate(tmpdir):
    apply_fs(tmpdir, yaml_config_dir)
    base = str(tmpdir)
    with patch.object(BuildConfigV1, 'validate') as build_validate:
        load(base, {})
        assert build_validate.call_count == 1


def test_raise_config_not_supported():
    build = get_build_config({})
    build.validate()
    with raises(ConfigOptionNotSupportedError) as excinfo:
        build.redirects
    assert excinfo.value.configuration == 'redirects'
    assert excinfo.value.code == CONFIG_NOT_SUPPORTED


@pytest.mark.parametrize(
    'correct_config_filename',
    [prefix + 'readthedocs.' + extension for prefix in {'', '.'}
     for extension in {'yml', 'yaml'}],
)
def test_config_filenames_regex(correct_config_filename):
    assert re.match(CONFIG_FILENAME_REGEX, correct_config_filename)


def test_as_dict(tmpdir):
    apply_fs(tmpdir, {'requirements.txt': ''})
    build = get_build_config(
        {
            'version': 1,
            'formats': ['pdf'],
            'python': {
                'version': 3.5,
            },
            'requirements_file': 'requirements.txt',
        },
        {
            'defaults': {
                'doctype': 'sphinx',
                'sphinx_configuration': None,
            },
        },
        source_file=str(tmpdir.join('readthedocs.yml')),
    )
    build.validate()
    expected_dict = {
        'version': '1',
        'formats': ['pdf'],
        'python': {
            'version': 3.5,
            'install': [{
                'requirements': str(tmpdir.join('requirements.txt')),
            }],
            'use_system_site_packages': False,
        },
        'build': {
            'image': 'readthedocs/build:latest',
        },
        'conda': None,
        'sphinx': {
            'builder': 'sphinx',
            'configuration': None,
            'fail_on_warning': False,
        },
        'mkdocs': {
            'configuration': None,
            'fail_on_warning': False,
        },
        'doctype': 'sphinx',
        'submodules': {
            'include': ALL,
            'exclude': [],
            'recursive': True,
        },
    }
    assert build.as_dict() == expected_dict


class TestBuildConfigV2:

    def get_build_config(
            self, config, env_config=None, source_file='readthedocs.yml',
    ):
        return BuildConfigV2(
            env_config or {},
            config,
            source_file=source_file,
        )

    def test_version(self):
        build = self.get_build_config({})
        assert build.version == '2'

    def test_correct_error_when_source_is_dir(self, tmpdir):
        build = self.get_build_config({}, source_file=str(tmpdir))
        with raises(InvalidConfig) as excinfo:
            build.error(key='key', message='Message', code='code')
        # We don't have any extra information about
        # the source_file.
        assert str(excinfo.value) == 'Invalid "key": Message'

    def test_formats_check_valid(self):
        build = self.get_build_config({'formats': ['htmlzip', 'pdf', 'epub']})
        build.validate()
        assert build.formats == ['htmlzip', 'pdf', 'epub']

    @pytest.mark.parametrize('value', [3, 'invalid', {'other': 'value'}])
    def test_formats_check_invalid_value(self, value):
        build = self.get_build_config({'formats': value})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'formats'

    def test_formats_check_invalid_type(self):
        build = self.get_build_config(
            {'formats': ['htmlzip', 'invalid', 'epub']},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'formats'

    def test_formats_default_value(self):
        build = self.get_build_config({})
        build.validate()
        assert build.formats == []

    def test_formats_overrides_default_values(self):
        build = self.get_build_config(
            {},
            {'defaults': {'formats': ['htmlzip']}},
        )
        build.validate()
        assert build.formats == []

    def test_formats_priority_over_defaults(self):
        build = self.get_build_config(
            {'formats': []},
            {'defaults': {'formats': ['htmlzip']}},
        )
        build.validate()
        assert build.formats == []

        build = self.get_build_config(
            {'formats': ['pdf']},
            {'defaults': {'formats': ['htmlzip']}},
        )
        build.validate()
        assert build.formats == ['pdf']

    def test_formats_allow_empty(self):
        build = self.get_build_config({'formats': []})
        build.validate()
        assert build.formats == []

    def test_formats_allow_all_keyword(self):
        build = self.get_build_config({'formats': 'all'})
        build.validate()
        assert build.formats == ['htmlzip', 'pdf', 'epub']

    def test_conda_check_valid(self, tmpdir):
        apply_fs(tmpdir, {'environment.yml': ''})
        build = self.get_build_config(
            {'conda': {'environment': 'environment.yml'}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        assert build.conda.environment == str(tmpdir.join('environment.yml'))

    @pytest.mark.parametrize('value', [3, [], 'invalid'])
    def test_conda_check_invalid_value(self, value):
        build = self.get_build_config({'conda': value})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'conda'

    @pytest.mark.parametrize('value', [3, [], {}])
    def test_conda_check_invalid_file_value(self, value):
        build = self.get_build_config({'conda': {'file': value}})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'conda.environment'

    def test_conda_check_file_required(self):
        build = self.get_build_config({'conda': {'no-file': 'other'}})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'conda.environment'

    @pytest.mark.parametrize('value', ['stable', 'latest'])
    def test_build_image_check_valid(self, value):
        build = self.get_build_config({'build': {'image': value}})
        build.validate()
        assert build.build.image == 'readthedocs/build:{}'.format(value)

    @pytest.mark.parametrize('value', ['readthedocs/build:latest', 'one'])
    def test_build_image_check_invalid(self, value):
        build = self.get_build_config({'build': {'image': value}})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'build.image'

    @pytest.mark.parametrize(
        'image', ['latest', 'readthedocs/build:3.0', 'rtd/build:latest'],
    )
    def test_build_image_priorities_default(self, image):
        build = self.get_build_config(
            {'build': {'image': 'latest'}},
            {'defaults': {'build_image': image}},
        )
        build.validate()
        assert build.build.image == image

    @pytest.mark.parametrize('image', ['', None])
    def test_build_image_over_empty_default(self, image):
        build = self.get_build_config(
            {'build': {'image': 'latest'}},
            {'defaults': {'build_image': image}},
        )
        build.validate()
        assert build.build.image == 'readthedocs/build:latest'

    def test_build_image_default_value(self):
        build = self.get_build_config({})
        build.validate()
        assert build.build.image == 'readthedocs/build:latest'

    @pytest.mark.parametrize('value', [3, [], 'invalid'])
    def test_build_check_invalid_type(self, value):
        build = self.get_build_config({'build': value})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'build'

    @pytest.mark.parametrize('value', [3, [], {}])
    def test_build_image_check_invalid_type(self, value):
        build = self.get_build_config({'build': {'image': value}})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'build.image'

    @pytest.mark.parametrize('value', [3, [], 'invalid'])
    def test_python_check_invalid_types(self, value):
        build = self.get_build_config({'python': value})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python'

    @pytest.mark.parametrize(
        'image,versions',
        [
            ('latest', [2, 2.7, 3, 3.5, 3.6]),
            ('stable', [2, 2.7, 3, 3.5, 3.6]),
        ],
    )
    def test_python_version(self, image, versions):
        for version in versions:
            build = self.get_build_config({
                'build': {
                    'image': image,
                },
                'python': {
                    'version': version,
                },
            })
            build.validate()
            assert build.python.version == version

    def test_python_version_accepts_string(self):
        build = self.get_build_config({
            'build': {
                'image': 'latest',
            },
            'python': {
                'version': '3.6',
            },
        })
        build.validate()
        assert build.python.version == 3.6

    @pytest.mark.parametrize(
        'image,versions',
        [
            ('latest', [1, 2.8, 4, 3.8]),
            ('stable', [1, 2.8, 4, 3.8]),
        ],
    )
    def test_python_version_invalid(self, image, versions):
        for version in versions:
            build = self.get_build_config({
                'build': {
                    'image': image,
                },
                'python': {
                    'version': version,
                },
            })
            with raises(InvalidConfig) as excinfo:
                build.validate()
            assert excinfo.value.key == 'python.version'

    def test_python_version_default(self):
        build = self.get_build_config({})
        build.validate()
        assert build.python.version == 3

    @pytest.mark.parametrize('value', [2, 3])
    def test_python_version_overrides_default(self, value):
        build = self.get_build_config(
            {},
            {'defaults': {'python_version': value}},
        )
        build.validate()
        assert build.python.version == 3

    @pytest.mark.parametrize('value', [2, 3, 3.6])
    def test_python_version_priority_over_default(self, value):
        build = self.get_build_config(
            {'python': {'version': value}},
            {'defaults': {'python_version': 3}},
        )
        build.validate()
        assert build.python.version == value

    @pytest.mark.parametrize('value', [[], {}])
    def test_python_version_check_invalid_types(self, value):
        build = self.get_build_config({'python': {'version': value}})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.version'

    def test_python_install_default_value(self):
        build = self.get_build_config({})
        build.validate()
        install = build.python.install
        assert len(install) == 0

    def test_python_install_check_default(self, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert isinstance(install[0], PythonInstall)
        assert install[0].path == str(tmpdir)
        assert install[0].method == PIP
        assert install[0].extra_requirements == []

    @pytest.mark.parametrize('value', ['invalid', 'apt'])
    def test_python_install_method_check_invalid(self, value, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'method': value,
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.install.0.method'

    def test_python_install_requirements_check_valid(self, tmpdir):
        apply_fs(tmpdir, {'requirements.txt': ''})
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'requirements': 'requirements.txt'
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert isinstance(install[0], PythonInstallRequirements)
        assert install[0].requirements == str(tmpdir.join('requirements.txt'))

    def test_python_install_requirements_does_not_allow_null(self, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'requirements': None,
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.install.0.requirements'

    def test_python_install_requirements_does_not_allow_empty_string(self, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'requirements': '',
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.install.0.requirements'

    def test_python_install_requirements_ignores_default(self, tmpdir):
        apply_fs(tmpdir, {'requirements.txt': ''})
        build = self.get_build_config(
            {},
            {'defaults': {'requirements_file': 'requirements.txt'}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        assert build.python.install == []

    def test_python_install_requirements_priority_over_default(self, tmpdir):
        apply_fs(tmpdir, {'requirements.txt': ''})
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'requirements': 'requirements.txt'
                    }],
                },
            },
            {'defaults': {'requirements_file': 'requirements-default.txt'}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert install[0].requirements == str(tmpdir.join('requirements.txt'))

    @pytest.mark.parametrize('value', [3, [], {}])
    def test_python_install_requirements_check_invalid_types(self, value, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'requirements': value,
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.install.0.requirements'

    def test_python_install_path_is_required(self, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'method': 'pip',
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.install.0'
        assert excinfo.value.code == CONFIG_REQUIRED

    def test_python_install_pip_check_valid(self, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'method': 'pip',
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert install[0].path == str(tmpdir)
        assert install[0].method == PIP

    def test_python_install_pip_have_priority_over_default(self, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'method': 'pip',
                    }],
                },
            },
            {'defaults': {'install_project': True}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert install[0].path == str(tmpdir)
        assert install[0].method == PIP

    def test_python_install_setuptools_check_valid(self, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'method': 'setuptools',
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert install[0].path == str(tmpdir)
        assert install[0].method == SETUPTOOLS

    def test_python_install_setuptools_ignores_default(self):
        build = self.get_build_config(
            {},
            {'defaults': {'install_project': True}},
        )
        build.validate()
        assert build.python.install == []

    def test_python_install_setuptools_priority_over_default(self, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'method': 'setuptools',
                    }],
                },
            },
            {'defaults': {'install_project': False}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert install[0].path == str(tmpdir)
        assert install[0].method == SETUPTOOLS

    def test_python_install_allow_empty_list(self):
        build = self.get_build_config({'python': {'install': []}},)
        build.validate()
        assert build.python.install == []

    def test_python_install_default(self):
        build = self.get_build_config({'python': {}})
        build.validate()
        assert build.python.install == []

    @pytest.mark.parametrize('value', [2, 'string', {}])
    def test_python_install_check_invalid_type(self, value):
        build = self.get_build_config({'python': {'install': value}},)
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.install'

    def test_python_install_extra_requirements_and_pip(self, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'method': 'pip',
                        'extra_requirements': ['docs', 'tests'],
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert install[0].extra_requirements == ['docs', 'tests']

    def test_python_install_extra_requirements_and_setuptools(self, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'method': 'setuptools',
                        'extra_requirements': ['docs', 'tests'],
                    }],
                }
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.install.0.extra_requirements'

    @pytest.mark.parametrize('value', [2, 'invalid', {}, '', None])
    def test_python_install_extra_requirements_check_type(self, value, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'method': 'pip',
                        'extra_requirements': value,
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.install.0.extra_requirements'

    def test_python_install_extra_requirements_allow_empty(self, tmpdir):
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': '.',
                        'method': 'pip',
                        'extra_requirements': [],
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 1
        assert install[0].extra_requirements == []

    def test_python_install_several_respects_order(self, tmpdir):
        apply_fs(tmpdir, {
            'one': {},
            'two': {},
            'three.txt': '',
        })
        build = self.get_build_config(
            {
                'python': {
                    'install': [{
                        'path': 'one',
                        'method': 'pip',
                        'extra_requirements': [],
                    }, {
                        'path': 'two',
                        'method': 'setuptools',
                    }, {
                        'requirements': 'three.txt',
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        install = build.python.install
        assert len(install) == 3

        assert install[0].path == str(tmpdir.join('one'))
        assert install[0].method == PIP
        assert install[0].extra_requirements == []

        assert install[1].path == str(tmpdir.join('two'))
        assert install[1].method == SETUPTOOLS

        assert install[2].requirements == str(tmpdir.join('three.txt'))

    @pytest.mark.parametrize('value', [True, False])
    def test_python_system_packages_check_valid(self, value):
        build = self.get_build_config({
            'python': {
                'system_packages': value,
            },
        })
        build.validate()
        assert build.python.use_system_site_packages is value

    @pytest.mark.parametrize('value', [[], 'invalid', 5])
    def test_python_system_packages_check_invalid(self, value):
        build = self.get_build_config({
            'python': {
                'system_packages': value,
            },
        })
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.system_packages'

    def test_python_system_packages_check_default(self):
        build = self.get_build_config({})
        build.validate()
        assert build.python.use_system_site_packages is False

    def test_python_system_packages_respects_default(self):
        build = self.get_build_config(
            {},
            {'defaults': {'use_system_packages': True}},
        )
        build.validate()
        assert build.python.use_system_site_packages is True

    def test_python_system_packages_priority_over_default(self):
        build = self.get_build_config(
            {'python': {'system_packages': False}},
            {'defaults': {'use_system_packages': True}},
        )
        build.validate()
        assert build.python.use_system_site_packages is False

        build = self.get_build_config(
            {'python': {'system_packages': True}},
            {'defaults': {'use_system_packages': False}},
        )
        build.validate()
        assert build.python.use_system_site_packages is True

    @pytest.mark.parametrize('value', [[], True, 0, 'invalid'])
    def test_sphinx_validate_type(self, value):
        build = self.get_build_config({'sphinx': value})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'sphinx'

    def test_sphinx_is_default_doc_type(self):
        build = self.get_build_config({})
        build.validate()
        assert build.sphinx is not None
        assert build.mkdocs is None
        assert build.doctype == 'sphinx'

    @pytest.mark.parametrize(
        'value,expected',
        [
            ('html', 'sphinx'),
            ('htmldir', 'sphinx_htmldir'),
            ('singlehtml', 'sphinx_singlehtml'),
        ],
    )
    def test_sphinx_builder_check_valid(self, value, expected):
        build = self.get_build_config(
            {'sphinx': {'builder': value}},
            {'defaults': {'doctype': expected}},
        )
        build.validate()
        assert build.sphinx.builder == expected
        assert build.doctype == expected

    @pytest.mark.parametrize('value', [[], True, 0, 'invalid'])
    def test_sphinx_builder_check_invalid(self, value):
        build = self.get_build_config({'sphinx': {'builder': value}})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'sphinx.builder'

    def test_sphinx_builder_default(self):
        build = self.get_build_config({})
        build.validate()
        build.sphinx.builder == 'sphinx'

    @pytest.mark.skip(
        'This test is not compatible with the new validation around doctype.',
    )
    def test_sphinx_builder_ignores_default(self):
        build = self.get_build_config(
            {},
            {'defaults': {'doctype': 'sphinx_singlehtml'}},
        )
        build.validate()
        build.sphinx.builder == 'sphinx'

    def test_sphinx_configuration_check_valid(self, tmpdir):
        apply_fs(tmpdir, {'conf.py': ''})
        build = self.get_build_config(
            {'sphinx': {'configuration': 'conf.py'}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        assert build.sphinx.configuration == str(tmpdir.join('conf.py'))

    def test_sphinx_cant_be_used_with_mkdocs(self, tmpdir):
        apply_fs(tmpdir, {'conf.py': ''})
        build = self.get_build_config(
            {
                'sphinx': {'configuration': 'conf.py'},
                'mkdocs': {},
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == '.'

    def test_sphinx_configuration_allow_null(self):
        build = self.get_build_config({'sphinx': {'configuration': None}},)
        build.validate()
        assert build.sphinx.configuration is None

    def test_sphinx_configuration_check_default(self):
        build = self.get_build_config({})
        build.validate()
        assert build.sphinx.configuration is None

    def test_sphinx_configuration_respects_default(self, tmpdir):
        apply_fs(tmpdir, {'conf.py': ''})
        build = self.get_build_config(
            {},
            {'defaults': {'sphinx_configuration': 'conf.py'}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        assert build.sphinx.configuration == str(tmpdir.join('conf.py'))

    def test_sphinx_configuration_default_can_be_none(self, tmpdir):
        apply_fs(tmpdir, {'conf.py': ''})
        build = self.get_build_config(
            {},
            {'defaults': {'sphinx_configuration': None}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        assert build.sphinx.configuration is None

    def test_sphinx_configuration_priorities_over_default(self, tmpdir):
        apply_fs(tmpdir, {'conf.py': '', 'conf-default.py': ''})
        build = self.get_build_config(
            {'sphinx': {'configuration': 'conf.py'}},
            {'defaults': {'sphinx_configuration': 'conf-default.py'}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        assert build.sphinx.configuration == str(tmpdir.join('conf.py'))

    @pytest.mark.parametrize('value', [[], True, 0, {}])
    def test_sphinx_configuration_validate_type(self, value):
        build = self.get_build_config({'sphinx': {'configuration': value}},)
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'sphinx.configuration'

    @pytest.mark.parametrize('value', [True, False])
    def test_sphinx_fail_on_warning_check_valid(self, value):
        build = self.get_build_config({'sphinx': {'fail_on_warning': value}})
        build.validate()
        assert build.sphinx.fail_on_warning is value

    @pytest.mark.parametrize('value', [[], 'invalid', 5])
    def test_sphinx_fail_on_warning_check_invalid(self, value):
        build = self.get_build_config({'sphinx': {'fail_on_warning': value}})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'sphinx.fail_on_warning'

    def test_sphinx_fail_on_warning_check_default(self):
        build = self.get_build_config({})
        build.validate()
        assert build.sphinx.fail_on_warning is False

    @pytest.mark.parametrize('value', [[], True, 0, 'invalid'])
    def test_mkdocs_validate_type(self, value):
        build = self.get_build_config({'mkdocs': value})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'mkdocs'

    def test_mkdocs_default(self):
        build = self.get_build_config({})
        build.validate()
        assert build.mkdocs is None

    def test_mkdocs_configuration_check_valid(self, tmpdir):
        apply_fs(tmpdir, {'mkdocs.yml': ''})
        build = self.get_build_config(
            {'mkdocs': {'configuration': 'mkdocs.yml'}},
            {'defaults': {'doctype': 'mkdocs'}},
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        assert build.mkdocs.configuration == str(tmpdir.join('mkdocs.yml'))
        assert build.doctype == 'mkdocs'
        assert build.sphinx is None

    def test_mkdocs_configuration_allow_null(self):
        build = self.get_build_config(
            {'mkdocs': {'configuration': None}},
            {'defaults': {'doctype': 'mkdocs'}},
        )
        build.validate()
        assert build.mkdocs.configuration is None

    def test_mkdocs_configuration_check_default(self):
        build = self.get_build_config(
            {'mkdocs': {}},
            {'defaults': {'doctype': 'mkdocs'}},
        )
        build.validate()
        assert build.mkdocs.configuration is None

    @pytest.mark.parametrize('value', [[], True, 0, {}])
    def test_mkdocs_configuration_validate_type(self, value):
        build = self.get_build_config(
            {'mkdocs': {'configuration': value}},
            {'defaults': {'doctype': 'mkdocs'}},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'mkdocs.configuration'

    @pytest.mark.parametrize('value', [True, False])
    def test_mkdocs_fail_on_warning_check_valid(self, value):
        build = self.get_build_config(
            {'mkdocs': {'fail_on_warning': value}},
            {'defaults': {'doctype': 'mkdocs'}},
        )
        build.validate()
        assert build.mkdocs.fail_on_warning is value

    @pytest.mark.parametrize('value', [[], 'invalid', 5])
    def test_mkdocs_fail_on_warning_check_invalid(self, value):
        build = self.get_build_config(
            {'mkdocs': {'fail_on_warning': value}},
            {'defaults': {'doctype': 'mkdocs'}},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'mkdocs.fail_on_warning'

    def test_mkdocs_fail_on_warning_check_default(self):
        build = self.get_build_config(
            {'mkdocs': {}},
            {'defaults': {'doctype': 'mkdocs'}},
        )
        build.validate()
        assert build.mkdocs.fail_on_warning is False

    def test_validates_different_filetype_mkdocs(self):
        build = self.get_build_config(
            {'mkdocs': {}},
            {'defaults': {'doctype': 'sphinx'}},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'mkdocs'
        assert 'configured as "Sphinx Html"' in str(excinfo.value)
        assert 'there is no "sphinx" key' in str(excinfo.value)

    def test_validates_different_filetype_sphinx(self):
        build = self.get_build_config(
            {'sphinx': {}},
            {'defaults': {'doctype': 'sphinx_htmldir'}},
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'sphinx.builder'
        assert 'configured as "Sphinx HtmlDir"' in str(excinfo.value)
        assert 'your "sphinx.builder" key does not match' in str(excinfo.value)

    def test_submodule_defaults(self):
        build = self.get_build_config({})
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == ALL
        assert build.submodules.recursive is False

    @pytest.mark.parametrize('value', [[], 'invalid', 0])
    def test_submodules_check_invalid_type(self, value):
        build = self.get_build_config({'submodules': value})
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'submodules'

    def test_submodules_include_check_valid(self):
        build = self.get_build_config({
            'submodules': {
                'include': ['one', 'two'],
            },
        })
        build.validate()
        assert build.submodules.include == ['one', 'two']
        assert build.submodules.exclude == []
        assert build.submodules.recursive is False

    @pytest.mark.parametrize('value', ['invalid', True, 0, {}])
    def test_submodules_include_check_invalid(self, value):
        build = self.get_build_config({
            'submodules': {
                'include': value,
            },
        })
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'submodules.include'

    def test_submodules_include_allows_all_keyword(self):
        build = self.get_build_config({
            'submodules': {
                'include': 'all',
            },
        })
        build.validate()
        assert build.submodules.include == ALL
        assert build.submodules.exclude == []
        assert build.submodules.recursive is False

    def test_submodules_exclude_check_valid(self):
        build = self.get_build_config({
            'submodules': {
                'exclude': ['one', 'two'],
            },
        })
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == ['one', 'two']
        assert build.submodules.recursive is False

    @pytest.mark.parametrize('value', ['invalid', True, 0, {}])
    def test_submodules_exclude_check_invalid(self, value):
        build = self.get_build_config({
            'submodules': {
                'exclude': value,
            },
        })
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'submodules.exclude'

    def test_submodules_exclude_allows_all_keyword(self):
        build = self.get_build_config({
            'submodules': {
                'exclude': 'all',
            },
        })
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == ALL
        assert build.submodules.recursive is False

    def test_submodules_cant_exclude_and_include(self):
        build = self.get_build_config({
            'submodules': {
                'include': ['two'],
                'exclude': ['one'],
            },
        })
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'submodules'

    def test_submodules_can_exclude_include_be_empty(self):
        build = self.get_build_config({
            'submodules': {
                'exclude': 'all',
                'include': [],
            },
        })
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == ALL
        assert build.submodules.recursive is False

    @pytest.mark.parametrize('value', [True, False])
    def test_submodules_recursive_check_valid(self, value):
        build = self.get_build_config({
            'submodules': {
                'include': ['one', 'two'],
                'recursive': value,
            },
        })
        build.validate()
        assert build.submodules.include == ['one', 'two']
        assert build.submodules.exclude == []
        assert build.submodules.recursive is value

    @pytest.mark.parametrize('value', [[], 'invalid', 5])
    def test_submodules_recursive_check_invalid(self, value):
        build = self.get_build_config({
            'submodules': {
                'include': ['one', 'two'],
                'recursive': value,
            },
        })
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'submodules.recursive'

    def test_submodules_recursive_explict_default(self):
        build = self.get_build_config({
            'submodules': {
                'include': [],
                'recursive': False,
            },
        })
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == ALL
        assert build.submodules.recursive is False

        build = self.get_build_config({
            'submodules': {
                'exclude': [],
                'recursive': False,
            },
        })
        build.validate()
        assert build.submodules.include == []
        assert build.submodules.exclude == []
        assert build.submodules.recursive is False

    @pytest.mark.parametrize('value,key', [
        ({'typo': 'something'}, 'typo'),
        (
            {
                'pyton': {
                    'version': 'another typo',
                }
            },
            'pyton.version'
        ),
        (
            {
                'build': {
                    'image': 'latest',
                    'extra': 'key',
                }
            },
            'build.extra'
        ),
        (
            {
                'python': {
                    'install': [{
                        'path': '.',
                    }, {
                        'path': '.',
                        'method': 'pip',
                        'invalid': 'key',
                    }]
                }
            },
            'python.install.1.invalid'
        )
    ])
    def test_strict_validation(self, value, key):
        build = self.get_build_config(value)
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == key
        assert excinfo.value.code == INVALID_KEY

    def test_strict_validation_pops_all_keys(self):
        build = self.get_build_config({
            'version': 2,
            'python': {
                'version': 3,
            },
        })
        build.validate()
        assert build.raw_config == {}

    @pytest.mark.parametrize(
        'value,expected', [
            ({}, []),
            ({'one': 1}, ['one']),
            ({'one': {'two': 3}}, ['one', 'two']),
            (OrderedDict([('one', 1), ('two', 2)]), ['one']),
            (OrderedDict([('one', {'two': 2}), ('three', 3)]), ['one', 'two']),
        ],
    )
    def test_get_extra_key(self, value, expected):
        build = self.get_build_config({})
        assert build._get_extra_key(value) == expected

    def test_pop_config_single(self):
        build = self.get_build_config({'one': 1})
        build.pop_config('one')
        assert build.raw_config == {}

    def test_pop_config_nested(self):
        build = self.get_build_config({'one': {'two': 2}})
        build.pop_config('one.two')
        assert build.raw_config == {}

    def test_pop_config_nested_with_residue(self):
        build = self.get_build_config({'one': {'two': 2, 'three': 3}})
        build.pop_config('one.two')
        assert build.raw_config == {'one': {'three': 3}}

    def test_pop_config_default_none(self):
        build = self.get_build_config({'one': {'two': 2, 'three': 3}})
        assert build.pop_config('one.four') is None
        assert build.raw_config == {'one': {'two': 2, 'three': 3}}

    def test_pop_config_default(self):
        build = self.get_build_config({'one': {'two': 2, 'three': 3}})
        assert build.pop_config('one.four', 4) == 4
        assert build.raw_config == {'one': {'two': 2, 'three': 3}}

    def test_pop_config_raise_exception(self):
        build = self.get_build_config({'one': {'two': 2, 'three': 3}})
        with raises(ValidationError) as excinfo:
            build.pop_config('one.four', raise_ex=True)
        assert excinfo.value.value == 'four'
        assert excinfo.value.code == VALUE_NOT_FOUND

    def test_as_dict(self, tmpdir):
        apply_fs(tmpdir, {'requirements.txt': ''})
        build = self.get_build_config(
            {
                'version': 2,
                'formats': ['pdf'],
                'python': {
                    'version': 3.6,
                    'install': [{
                        'requirements': 'requirements.txt',
                    }],
                },
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
        )
        build.validate()
        expected_dict = {
            'version': '2',
            'formats': ['pdf'],
            'python': {
                'version': 3.6,
                'install': [{
                    'requirements': str(tmpdir.join('requirements.txt')),
                }],
                'use_system_site_packages': False,
            },
            'build': {
                'image': 'readthedocs/build:latest',
            },
            'conda': None,
            'sphinx': {
                'builder': 'sphinx',
                'configuration': None,
                'fail_on_warning': False,
            },
            'mkdocs': None,
            'doctype': 'sphinx',
            'submodules': {
                'include': [],
                'exclude': ALL,
                'recursive': False,
            },
        }
        assert build.as_dict() == expected_dict
