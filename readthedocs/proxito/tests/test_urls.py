# Copied from .com codebase

"""Test URL config."""

import pytest
from django.test import TestCase
from django.urls import resolve


@pytest.mark.proxito
class TestSingleVersionURLs(TestCase):

    def test_root(self):
        match = resolve('/')
        self.assertEqual(match.url_name, 'docs_detail_singleversion_subproject')
        self.assertEqual(match.args, ())
        self.assertEqual(
            match.kwargs, {
                'subproject_slug': None,
                'subproject_slash': None,
                'filename': '',
            },
        )

    def test_normal_root(self):
        match = resolve('/en/latest/')
        self.assertEqual(match.url_name, 'docs_detail')
        self.assertEqual(match.args, ())
        self.assertEqual(
            match.kwargs, {
                'subproject_slug': None,
                'lang_slug': 'en',
                'version_slug': 'latest',
                'filename': '',
            },
        )

    def test_normal_root_with_file(self):
        match = resolve('/en/latest/foo.html')
        self.assertEqual(match.url_name, 'docs_detail')
        self.assertEqual(match.args, ())
        self.assertEqual(
            match.kwargs, {
                'subproject_slug': None,
                'lang_slug': 'en',
                'version_slug': 'latest',
                'filename': 'foo.html',
            },
        )

    def test_subproject_with_lang_and_version(self):
        match = resolve('/projects/bar/en/latest/')
        self.assertEqual(match.url_name, 'docs_detail')
        self.assertEqual(match.args, ())
        self.assertEqual(
            match.kwargs, {
                'subproject_slug': 'bar',
                'lang_slug': 'en',
                'version_slug': 'latest',
                'filename': '',
            },
        )

    def test_subproject_with_lang_and_version_and_filename(self):
        match = resolve('/projects/bar/en/latest/index.html')
        self.assertEqual(match.url_name, 'docs_detail')
        self.assertEqual(match.args, ())
        self.assertEqual(
            match.kwargs, {
                'subproject_slug': 'bar',
                'lang_slug': 'en',
                'version_slug': 'latest',
                'filename': 'index.html',
            },
        )

    def test_subproject_single_version(self):
        match = resolve('/projects/bar/index.html')
        self.assertEqual(match.url_name, 'docs_detail_singleversion_subproject')
        self.assertEqual(match.args, ())
        self.assertEqual(
            match.kwargs, {
                'subproject_slug': 'bar',
                'subproject_slash': '/',
                'filename': 'index.html',
            },
        )

    def test_subproject_root(self):
        match = resolve('/projects/bar/')
        self.assertEqual(match.url_name, 'docs_detail_singleversion_subproject')
        self.assertEqual(match.args, ())
        self.assertEqual(
            match.kwargs, {
                'subproject_slug': 'bar',
                'subproject_slash': '/',
                'filename': '',
            },
        )

    def test_single_version(self):
        match = resolve('/some/path/index.html')
        self.assertEqual(match.url_name, 'docs_detail_singleversion_subproject')
        self.assertEqual(match.args, ())
        self.assertEqual(
            match.kwargs, {
                'subproject_slash': None,
                'subproject_slug': None,
                'filename': 'some/path/index.html',
            },
        )
