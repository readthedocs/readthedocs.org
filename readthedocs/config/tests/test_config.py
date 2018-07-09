from __future__ import division, print_function, unicode_literals

import os

import pytest
from mock import DEFAULT, patch
from pytest import raises

from readthedocs.config import (
    BuildConfig, ConfigError, ConfigOptionNotSupportedError, InvalidConfig,
    ProjectConfig, load)
from readthedocs.config.config import (
    CONFIG_NOT_SUPPORTED, NAME_INVALID, NAME_REQUIRED, PYTHON_INVALID,
    TYPE_REQUIRED)
from readthedocs.config.validation import (
    INVALID_BOOL, INVALID_CHOICE, INVALID_LIST, INVALID_PATH, INVALID_STRING)

from .utils import apply_fs

env_config = {
    'output_base': '/tmp'
}


minimal_config = {
    'name': 'docs',
    'type': 'sphinx',
}


config_with_explicit_empty_list = {
    'readthedocs.yml': '''
name: docs
type: sphinx
formats: []
'''
}


minimal_config_dir = {
    'readthedocs.yml': '''\
name: docs
type: sphinx
'''
}


multiple_config_dir = {
    'readthedocs.yml': '''
name: first
type: sphinx
---
name: second
type: sphinx
    ''',
    'nested': minimal_config_dir,
}


def get_build_config(config, env_config=None, source_file='readthedocs.yml',
                     source_position=0):
    return BuildConfig(
        env_config or {},
        config,
        source_file=source_file,
        source_position=source_position)


def get_env_config(extra=None):
    """Get the minimal env_config for the configuration object."""
    defaults = {
        'output_base': '',
        'name': 'name',
        'type': 'sphinx',
    }
    if extra is None:
        extra = {}
    defaults.update(extra)
    return defaults


def test_load_no_config_file(tmpdir):
    base = str(tmpdir)
    with raises(ConfigError):
        load(base, env_config)


def test_load_empty_config_file(tmpdir):
    apply_fs(tmpdir, {
        'readthedocs.yml': ''
    })
    base = str(tmpdir)
    with raises(ConfigError):
        load(base, env_config)


def test_minimal_config(tmpdir):
    apply_fs(tmpdir, minimal_config_dir)
    base = str(tmpdir)
    config = load(base, env_config)
    assert isinstance(config, ProjectConfig)
    assert len(config) == 1
    build = config[0]
    assert isinstance(build, BuildConfig)


def test_build_config_has_source_file(tmpdir):
    base = str(apply_fs(tmpdir, minimal_config_dir))
    build = load(base, env_config)[0]
    assert build.source_file == os.path.join(base, 'readthedocs.yml')
    assert build.source_position == 0


def test_build_config_has_source_position(tmpdir):
    base = str(apply_fs(tmpdir, multiple_config_dir))
    builds = load(base, env_config)
    assert len(builds) == 2
    first, second = filter(
        lambda b: not b.source_file.endswith('nested/readthedocs.yml'),
        builds)
    assert first.source_position == 0
    assert second.source_position == 1


def test_build_config_has_list_with_single_empty_value(tmpdir):
    base = str(apply_fs(tmpdir, config_with_explicit_empty_list))
    build = load(base, env_config)[0]
    assert isinstance(build, BuildConfig)
    assert build.formats == []


def test_config_requires_name():
    build = BuildConfig(
        {'output_base': ''}, {},
        source_file='readthedocs.yml',
        source_position=0
    )
    with raises(InvalidConfig) as excinfo:
        build.validate()
    assert excinfo.value.key == 'name'
    assert excinfo.value.code == NAME_REQUIRED


def test_build_requires_valid_name():
    build = BuildConfig(
        {'output_base': ''},
        {'name': 'with/slashes'},
        source_file='readthedocs.yml',
        source_position=0
    )
    with raises(InvalidConfig) as excinfo:
        build.validate()
    assert excinfo.value.key == 'name'
    assert excinfo.value.code == NAME_INVALID


def test_config_requires_type():
    build = BuildConfig(
        {'output_base': ''}, {'name': 'docs'},
        source_file='readthedocs.yml',
        source_position=0
    )
    with raises(InvalidConfig) as excinfo:
        build.validate()
    assert excinfo.value.key == 'type'
    assert excinfo.value.code == TYPE_REQUIRED


def test_build_requires_valid_type():
    build = BuildConfig(
        {'output_base': ''},
        {'name': 'docs', 'type': 'unknown'},
        source_file='readthedocs.yml',
        source_position=0
    )
    with raises(InvalidConfig) as excinfo:
        build.validate()
    assert excinfo.value.key == 'type'
    assert excinfo.value.code == INVALID_CHOICE


def test_version():
    build = get_build_config({}, get_env_config())
    assert build.version == '1'


def test_empty_python_section_is_valid():
    build = get_build_config({'python': {}}, get_env_config())
    build.validate()
    assert build.python


def test_python_section_must_be_dict():
    build = get_build_config({'python': 123}, get_env_config())
    with raises(InvalidConfig) as excinfo:
        build.validate()
    assert excinfo.value.key == 'python'
    assert excinfo.value.code == PYTHON_INVALID


def test_use_system_site_packages_defaults_to_false():
    build = get_build_config({'python': {}}, get_env_config())
    build.validate()
    # Default is False.
    assert not build.use_system_site_packages


@pytest.mark.parametrize('value', [True, False])
def test_use_system_site_packages_repects_default_value(value):
    defaults = {
        'use_system_packages': value,
    }
    build = get_build_config({}, get_env_config({'defaults': defaults}))
    build.validate()
    assert build.use_system_site_packages is value


def test_python_pip_install_default():
    build = get_build_config({'python': {}}, get_env_config())
    build.validate()
    # Default is False.
    assert build.pip_install is False


def describe_validate_python_extra_requirements():

    def it_defaults_to_list():
        build = get_build_config({'python': {}}, get_env_config())
        build.validate()
        # Default is an empty list.
        assert build.extra_requirements == []

    def it_validates_is_a_list():
        build = get_build_config(
            {'python': {'extra_requirements': 'invalid'}},
            get_env_config()
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.extra_requirements'
        assert excinfo.value.code == PYTHON_INVALID

    @patch('readthedocs.config.config.validate_string')
    def it_uses_validate_string(validate_string):
        validate_string.return_value = True
        build = get_build_config(
            {'python': {'extra_requirements': ['tests']}},
            get_env_config()
        )
        build.validate()
        validate_string.assert_any_call('tests')


def describe_validate_use_system_site_packages():
    def it_defaults_to_false():
        build = get_build_config({'python': {}}, get_env_config())
        build.validate()
        assert build.use_system_site_packages is False

    def it_validates_value():
        build = get_build_config(
            {'python': {'use_system_site_packages': 'invalid'}},
            get_env_config()
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        excinfo.value.key = 'python.use_system_site_packages'
        excinfo.value.code = INVALID_BOOL

    @patch('readthedocs.config.config.validate_bool')
    def it_uses_validate_bool(validate_bool):
        validate_bool.return_value = True
        build = get_build_config(
            {'python': {'use_system_site_packages': 'to-validate'}},
            get_env_config()
        )
        build.validate()
        validate_bool.assert_any_call('to-validate')


def describe_validate_setup_py_install():

    def it_defaults_to_false():
        build = get_build_config({'python': {}}, get_env_config())
        build.validate()
        assert build.python['setup_py_install'] is False

    def it_validates_value():
        build = get_build_config(
            {'python': {'setup_py_install': 'this-is-string'}},
            get_env_config()
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.setup_py_install'
        assert excinfo.value.code == INVALID_BOOL

    @patch('readthedocs.config.config.validate_bool')
    def it_uses_validate_bool(validate_bool):
        validate_bool.return_value = True
        build = get_build_config(
            {'python': {'setup_py_install': 'to-validate'}},
            get_env_config()
        )
        build.validate()
        validate_bool.assert_any_call('to-validate')


def describe_validate_python_version():

    def it_defaults_to_a_valid_version():
        build = get_build_config({'python': {}}, get_env_config())
        build.validate()
        assert build.python_version == 2
        assert build.python_interpreter == 'python2.7'
        assert build.python_full_version == 2.7

    def it_supports_other_versions():
        build = get_build_config(
            {'python': {'version': 3.5}},
            get_env_config()
        )
        build.validate()
        assert build.python_version == 3.5
        assert build.python_interpreter == 'python3.5'
        assert build.python_full_version == 3.5

    def it_validates_versions_out_of_range():
        build = get_build_config(
            {'python': {'version': 1.0}},
            get_env_config()
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.version'
        assert excinfo.value.code == INVALID_CHOICE

    def it_validates_wrong_type():
        build = get_build_config(
            {'python': {'version': 'this-is-string'}},
            get_env_config()
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.version'
        assert excinfo.value.code == INVALID_CHOICE

    def it_validates_wrong_type_right_value():
        build = get_build_config(
            {'python': {'version': '3.5'}},
            get_env_config()
        )
        build.validate()
        assert build.python_version == 3.5
        assert build.python_interpreter == 'python3.5'
        assert build.python_full_version == 3.5

        build = get_build_config(
            {'python': {'version': '3'}},
            get_env_config()
        )
        build.validate()
        assert build.python_version == 3
        assert build.python_interpreter == 'python3.5'
        assert build.python_full_version == 3.5

    def it_validates_env_supported_versions():
        build = get_build_config(
            {'python': {'version': 3.6}},
            env_config=get_env_config(
                {
                    'python': {'supported_versions': [3.5]},
                    'build': {'image': 'custom'},
                }
            )
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'python.version'
        assert excinfo.value.code == INVALID_CHOICE

        build = get_build_config(
            {'python': {'version': 3.6}},
            env_config=get_env_config(
                {
                    'python': {'supported_versions': [3.5, 3.6]},
                    'build': {'image': 'custom'},
                }
            )
        )
        build.validate()
        assert build.python_version == 3.6
        assert build.python_interpreter == 'python3.6'
        assert build.python_full_version == 3.6

    @pytest.mark.parametrize('value', [2, 3])
    def it_respects_default_value(value):
        defaults = {
            'python_version': value
        }
        build = get_build_config(
            {},
            get_env_config({'defaults': defaults})
        )
        build.validate()
        assert build.python_version == value


def describe_validate_formats():

    def it_defaults_to_empty():
        build = get_build_config({}, get_env_config())
        build.validate()
        assert build.formats == []

    def it_gets_set_correctly():
        build = get_build_config({'formats': ['pdf']}, get_env_config())
        build.validate()
        assert build.formats == ['pdf']

    def formats_can_be_null():
        build = get_build_config({'formats': None}, get_env_config())
        build.validate()
        assert build.formats == []

    def formats_with_previous_none():
        build = get_build_config({'formats': ['none']}, get_env_config())
        build.validate()
        assert build.formats == []

    def formats_can_be_empty():
        build = get_build_config({'formats': []}, get_env_config())
        build.validate()
        assert build.formats == []

    def all_valid_formats():
        build = get_build_config(
            {'formats': ['pdf', 'htmlzip', 'epub']},
            get_env_config()
        )
        build.validate()
        assert build.formats == ['pdf', 'htmlzip', 'epub']

    def cant_have_none_as_format():
        build = get_build_config(
            {'formats': ['htmlzip', None]},
            get_env_config()
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'format'
        assert excinfo.value.code == INVALID_CHOICE

    def formats_have_only_allowed_values():
        build = get_build_config(
            {'formats': ['htmlzip', 'csv']},
            get_env_config()
        )
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'format'
        assert excinfo.value.code == INVALID_CHOICE

    def only_list_type():
        build = get_build_config({'formats': 'no-list'}, get_env_config())
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'format'
        assert excinfo.value.code == INVALID_LIST


def describe_validate_setup_py_path():

    def it_defaults_to_source_file_directory(tmpdir):
        apply_fs(
            tmpdir,
            {
                'subdir': {
                    'readthedocs.yml': '',
                    'setup.py': '',
                },
            }
        )
        with tmpdir.as_cwd():
            source_file = tmpdir.join('subdir', 'readthedocs.yml')
            setup_py = tmpdir.join('subdir', 'setup.py')
            build = get_build_config(
                {},
                env_config=get_env_config(),
                source_file=str(source_file))
            build.validate()
            assert build.python['setup_py_path'] == str(setup_py)

    def it_validates_value(tmpdir):
        with tmpdir.as_cwd():
            build = get_build_config({'python': {'setup_py_path': 'this-is-string'}})
            with raises(InvalidConfig) as excinfo:
                build.validate_python()
            assert excinfo.value.key == 'python.setup_py_path'
            assert excinfo.value.code == INVALID_PATH

    def it_uses_validate_file(tmpdir):
        path = tmpdir.join('setup.py')
        path.write('content')
        path = str(path)
        patcher = patch('readthedocs.config.config.validate_file')
        with patcher as validate_file:
            validate_file.return_value = path
            build = get_build_config(
                {'python': {'setup_py_path': 'setup.py'}})
            build.validate_python()
            args, kwargs = validate_file.call_args
            assert args[0] == 'setup.py'


def test_valid_build_config():
    build = BuildConfig(env_config,
                        minimal_config,
                        source_file='readthedocs.yml',
                        source_position=0)
    build.validate()
    assert build.name == 'docs'
    assert build.type == 'sphinx'
    assert build.base
    assert build.python
    assert 'setup_py_install' in build.python
    assert 'use_system_site_packages' in build.python
    assert build.output_base


def describe_validate_base():

    def it_validates_to_abspath(tmpdir):
        apply_fs(tmpdir, {'configs': minimal_config, 'docs': {}})
        with tmpdir.as_cwd():
            source_file = str(tmpdir.join('configs', 'readthedocs.yml'))
            build = BuildConfig(
                get_env_config(),
                {'base': '../docs'},
                source_file=source_file,
                source_position=0)
            build.validate()
            assert build.base == str(tmpdir.join('docs'))

    @patch('readthedocs.config.config.validate_directory')
    def it_uses_validate_directory(validate_directory):
        validate_directory.return_value = 'path'
        build = get_build_config({'base': '../my-path'}, get_env_config())
        build.validate()
        # Test for first argument to validate_directory
        args, kwargs = validate_directory.call_args
        assert args[0] == '../my-path'

    def it_fails_if_base_is_not_a_string(tmpdir):
        apply_fs(tmpdir, minimal_config)
        with tmpdir.as_cwd():
            build = BuildConfig(
                get_env_config(),
                {'base': 1},
                source_file=str(tmpdir.join('readthedocs.yml')),
                source_position=0)
            with raises(InvalidConfig) as excinfo:
                build.validate()
            assert excinfo.value.key == 'base'
            assert excinfo.value.code == INVALID_STRING

    def it_fails_if_base_does_not_exist(tmpdir):
        apply_fs(tmpdir, minimal_config)
        build = BuildConfig(
            get_env_config(),
            {'base': 'docs'},
            source_file=str(tmpdir.join('readthedocs.yml')),
            source_position=0)
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'base'
        assert excinfo.value.code == INVALID_PATH


def describe_validate_build():

    def it_fails_if_build_is_invalid_option(tmpdir):
        apply_fs(tmpdir, minimal_config)
        build = BuildConfig(
            get_env_config(),
            {'build': {'image': 3.0}},
            source_file=str(tmpdir.join('readthedocs.yml')),
            source_position=0)
        with raises(InvalidConfig) as excinfo:
            build.validate()
        assert excinfo.value.key == 'build'
        assert excinfo.value.code == INVALID_CHOICE

    def it_fails_on_python_validation(tmpdir):
        apply_fs(tmpdir, minimal_config)
        build = BuildConfig(
            {},
            {
                'build': {'image': 1.0},
                'python': {'version': '3.3'},
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
            source_position=0)
        build.validate_build()
        with raises(InvalidConfig) as excinfo:
            build.validate_python()
        assert excinfo.value.key == 'python.version'
        assert excinfo.value.code == INVALID_CHOICE

    def it_works_on_python_validation(tmpdir):
        apply_fs(tmpdir, minimal_config)
        build = BuildConfig(
            {},
            {
                'build': {'image': 'latest'},
                'python': {'version': '3.3'},
            },
            source_file=str(tmpdir.join('readthedocs.yml')),
            source_position=0)
        build.validate_build()
        build.validate_python()

    def it_works(tmpdir):
        apply_fs(tmpdir, minimal_config)
        build = BuildConfig(
            get_env_config(),
            {'build': {'image': 'latest'}},
            source_file=str(tmpdir.join('readthedocs.yml')),
            source_position=0)
        build.validate()
        assert build.build_image == 'readthedocs/build:latest'

    def default(tmpdir):
        apply_fs(tmpdir, minimal_config)
        build = BuildConfig(
            get_env_config(),
            {},
            source_file=str(tmpdir.join('readthedocs.yml')),
            source_position=0)
        build.validate()
        assert build.build_image == 'readthedocs/build:2.0'

    @pytest.mark.parametrize(
        'image', ['latest', 'readthedocs/build:3.0', 'rtd/build:latest'])
    def it_priorities_image_from_env_config(tmpdir, image):
        apply_fs(tmpdir, minimal_config)
        defaults = {
            'build_image': image,
        }
        build = BuildConfig(
            get_env_config({'defaults': defaults}),
            {'build': {'image': 'latest'}},
            source_file=str(tmpdir.join('readthedocs.yml')),
            source_position=0
        )
        build.validate()
        assert build.build_image == image


def test_use_conda_default_false():
    build = get_build_config({}, get_env_config())
    build.validate()
    assert build.use_conda is False


def test_use_conda_respects_config():
    build = get_build_config(
        {'conda': {}},
        get_env_config()
    )
    build.validate()
    assert build.use_conda is True


def test_validates_conda_file(tmpdir):
    apply_fs(tmpdir, {'environment.yml': ''})
    build = get_build_config(
        {'conda': {'file': 'environment.yml'}},
        get_env_config(),
        source_file=str(tmpdir.join('readthedocs.yml'))
    )
    build.validate()
    assert build.use_conda is True
    assert build.conda_file == str(tmpdir.join('environment.yml'))


def test_requirements_file_empty():
    build = get_build_config({}, get_env_config())
    build.validate()
    assert build.requirements_file is None


def test_requirements_file_repects_default_value(tmpdir):
    apply_fs(tmpdir, {'myrequirements.txt': ''})
    defaults = {
        'requirements_file': 'myrequirements.txt'
    }
    build = get_build_config(
        {},
        get_env_config({'defaults': defaults}),
        source_file=str(tmpdir.join('readthedocs.yml'))
    )
    build.validate()
    assert build.requirements_file == 'myrequirements.txt'


def test_requirements_file_respects_configuration(tmpdir):
    apply_fs(tmpdir, {'requirements.txt': ''})
    build = get_build_config(
        {'requirements_file': 'requirements.txt'},
        get_env_config(),
        source_file=str(tmpdir.join('readthedocs.yml'))
    )
    build.validate()
    assert build.requirements_file == 'requirements.txt'



def test_build_validate_calls_all_subvalidators(tmpdir):
    apply_fs(tmpdir, minimal_config)
    build = BuildConfig(
        {},
        {},
        source_file=str(tmpdir.join('readthedocs.yml')),
        source_position=0)
    with patch.multiple(BuildConfig,
                        validate_base=DEFAULT,
                        validate_name=DEFAULT,
                        validate_type=DEFAULT,
                        validate_python=DEFAULT,
                        validate_output_base=DEFAULT):
        build.validate()
        BuildConfig.validate_base.assert_called_with()
        BuildConfig.validate_name.assert_called_with()
        BuildConfig.validate_type.assert_called_with()
        BuildConfig.validate_python.assert_called_with()
        BuildConfig.validate_output_base.assert_called_with()


def test_validate_project_config():
    with patch.object(BuildConfig, 'validate') as build_validate:
        project = ProjectConfig([
            BuildConfig(
                env_config,
                minimal_config,
                source_file='readthedocs.yml',
                source_position=0)
        ])
        project.validate()
        assert build_validate.call_count == 1


def test_load_calls_validate(tmpdir):
    apply_fs(tmpdir, minimal_config_dir)
    base = str(tmpdir)
    with patch.object(BuildConfig, 'validate') as build_validate:
        load(base, env_config)
        assert build_validate.call_count == 1


def test_raise_config_not_supported():
    build = get_build_config({}, get_env_config())
    build.validate()
    with raises(ConfigOptionNotSupportedError) as excinfo:
        build.redirects
    assert excinfo.value.configuration == 'redirects'
    assert excinfo.value.code == CONFIG_NOT_SUPPORTED
