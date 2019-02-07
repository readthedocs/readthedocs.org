# -*- coding: utf-8 -*-
import os

from readthedocs.config.find import find_one

from .utils import apply_fs


def test_find_no_files(tmpdir):
    with tmpdir.as_cwd():
        path = find_one(os.getcwd(), r'readthedocs.yml')
    assert path == ''


def test_find_at_root(tmpdir):
    apply_fs(tmpdir, {'readthedocs.yml': '', 'otherfile.txt': ''})
    base = str(tmpdir)
    path = find_one(base, r'readthedocs\.yml')
    assert path == os.path.abspath(os.path.join(base, 'readthedocs.yml'))
