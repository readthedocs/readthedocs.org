# -*- coding: utf-8 -*-
from io import StringIO

from pytest import raises

from readthedocs.config.parser import ParseError, parse


def test_parse_empty_config_file():
    buf = StringIO('')
    with raises(ParseError):
        parse(buf)


def test_parse_invalid_yaml():
    buf = StringIO('- - !asdf')
    with raises(ParseError):
        parse(buf)


def test_parse_bad_type():
    buf = StringIO('Hello')
    with raises(ParseError):
        parse(buf)


def test_parse_single_config():
    buf = StringIO('base: path')
    config = parse(buf)
    assert isinstance(config, dict)
    assert config['base'] == 'path'


def test_parse_null_value():
    buf = StringIO('base: null')
    config = parse(buf)
    assert config['base'] is None


def test_parse_empty_value():
    buf = StringIO('base:')
    config = parse(buf)
    assert config['base'] is None


def test_parse_empty_string_value():
    buf = StringIO('base: ""')
    config = parse(buf)
    assert config['base'] == ''


def test_parse_empty_list():
    buf = StringIO('base: []')
    config = parse(buf)
    assert config['base'] == []


def test_do_not_parse_multiple_configs_in_one_file():
    buf = StringIO(
        '''
base: path
---
base: other_path
name: second
nested:
    works: true
        '''
    )
    with raises(ParseError):
        parse(buf)
