from __future__ import division, print_function, unicode_literals

from io import StringIO

from pytest import raises

from readthedocs.config.parser import ParseError, parse


def test_parse_empty_config_file():
    buf = StringIO(u'')
    with raises(ParseError):
        parse(buf)


def test_parse_invalid_yaml():
    buf = StringIO(u'- - !asdf')
    with raises(ParseError):
        parse(buf)


def test_parse_bad_type():
    buf = StringIO(u'Hello')
    with raises(ParseError):
        parse(buf)


def test_parse_single_config():
    buf = StringIO(u'base: path')
    config = parse(buf)
    assert isinstance(config, list)
    assert len(config) == 1
    assert config[0]['base'] == 'path'


def test_parse_null_value():
    buf = StringIO(u'base: null')
    config = parse(buf)
    assert config[0]['base'] is None


def test_parse_empty_value():
    buf = StringIO(u'base:')
    config = parse(buf)
    assert config[0]['base'] is None


def test_parse_empty_string_value():
    buf = StringIO(u'base: ""')
    config = parse(buf)
    assert config[0]['base'] == ''


def test_parse_empty_list():
    buf = StringIO(u'base: []')
    config = parse(buf)
    assert config[0]['base'] == []


def test_parse_multiple_configs_in_one_file():
    buf = StringIO(
        u'''
base: path
---
base: other_path
name: second
nested:
    works: true
        ''')
    configs = parse(buf)
    assert isinstance(configs, list)
    assert len(configs) == 2
    assert configs[0]['base'] == 'path'
    assert configs[1]['nested'] == {'works': True}
