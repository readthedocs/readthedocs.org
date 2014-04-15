import mock
from nose.tools import ok_
import os
import shutil
import unittest

from django.conf import settings

from vcs_support import utils

TEST_STATICS = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_statics')


class TestNonBlockingLock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            os.mkdir(TEST_STATICS)
        except OSError:
            pass

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_STATICS, ignore_errors=True)

    def setUp(self):
        self.project_mock = mock.Mock()
        self.project_mock.slug = 'test-project-slug'
        self.project_mock.doc_path = TEST_STATICS
        self.version_mock = mock.Mock()
        self.version_mock.slug = 'test-version-slug'

    def test_simplelock(self):
        with utils.NonBlockingLock(project=self.project_mock,
                                   version=self.version_mock) as f_lock:
            ok_(os.path.exists(f_lock.fpath))

    def test_simplelock_cleanup(self):
        lock_path = None
        with utils.NonBlockingLock(project=self.project_mock,
                                   version=self.version_mock) as f_lock:
            lock_path = f_lock.fpath
        ok_(lock_path is not None and not os.path.exists(lock_path))

    def test_nonreentrant(self):
        with utils.NonBlockingLock(project=self.project_mock,
                                   version=self.version_mock) as f_lock:
            try:
                with utils.NonBlockingLock(project=self.project_mock,
                                           version=self.version_mock) as f_lock:
                    pass
            except utils.LockTimeout:
                pass
            else:
                raise AssertionError('Should have thrown LockTimeout')

    def test_forceacquire(self):
        with utils.NonBlockingLock(project=self.project_mock,
                                   version=self.version_mock) as f_lock:
            try:
                with utils.NonBlockingLock(project=self.project_mock,
                                           version=self.version_mock, max_lock_age=0) as f_lock:
                    pass
            except utils.LockTimeout:
                raise AssertionError('Should have thrown LockTimeout')


