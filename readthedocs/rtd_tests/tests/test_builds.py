import os
import subprocess

from django.test import TestCase
import mock

from readthedocs.projects.tasks import build_docs
from readthedocs.rtd_tests.factories.projects_factories import ProjectFactory
from readthedocs.rtd_tests.mocks.paths import fake_paths_lookup
from readthedocs.doc_builder.loader import get_builder_class


class MockProcess(object):
    returncode = 0
    communicate_result = None

    def __init__(self, communicate_result):
        self.communicate_result = communicate_result

    def communicate(self):
        return self.communicate_result


def build_subprocess_side_effect(*args, **kwargs):
    if args == (('git', 'rev-parse', 'HEAD'),):
        return MockProcess(('SOMEGITHASH', ''))
    elif 'sphinx-build' in args[0]:
        return MockProcess(("Here's where our build report goes.", "Here's our error message."))
    else:
        return subprocess.Popen(*args, **kwargs)


class BuildTests(TestCase):

    @mock.patch('slumber.Resource')
    @mock.patch('os.chdir')
    @mock.patch('projects.models.Project.api_versions')
    @mock.patch('subprocess.Popen')
    def test_build(self, mock_Popen, mock_api_versions, mock_chdir, mock_apiv2_downloads):

        # subprocess mock logic

        mock_process = mock.Mock()
        process_return_dict = {'communicate.return_value': ('SOMEGITHASH', '')}
        mock_process.configure_mock(**process_return_dict)
        mock_Popen.return_value = mock_process
        mock_Popen.side_effect = build_subprocess_side_effect

        project = ProjectFactory(allow_comments=True)

        version = project.versions.all()[0]
        mock_api_versions.return_value = [version]

        mock_apiv2_downloads.get.return_value = {'downloads': "no_url_here"}

        conf_path = os.path.join(
            project.checkout_path(version.slug),
            project.conf_py_file)

        # Mock open to simulate existing conf.py file
        with mock.patch('codecs.open', mock.mock_open(), create=True):
            with fake_paths_lookup({conf_path: True}):
                built_docs = build_docs(version,
                                        False,
                                        False,
                                        False,
                                        )

        builder_class = get_builder_class(project.documentation_type)
        builder = builder_class(version)
        self.assertIn(builder.sphinx_builder,
                      str(mock_Popen.call_args_list[1])
                      )

        # We are using the comment builder

    def test_builder_comments(self):

        # Normal build
        project = ProjectFactory(allow_comments=True)
        version = project.versions.all()[0]
        builder_class = get_builder_class(project.documentation_type)
        builder = builder_class(version)
        self.assertEqual(builder.sphinx_builder, 'readthedocs-comments')

    def test_builder_no_comments(self):

        # Normal build
        project = ProjectFactory(allow_comments=False)
        version = project.versions.all()[0]
        builder_class = get_builder_class(project.documentation_type)
        builder = builder_class(version)
        self.assertEqual(builder.sphinx_builder, 'readthedocs')

    @mock.patch('slumber.Resource')
    @mock.patch('os.chdir')
    @mock.patch('subprocess.Popen')
    @mock.patch('doc_builder.backends.sphinx.HtmlBuilder.build')
    @mock.patch('doc_builder.backends.sphinx.PdfBuilder.build')
    @mock.patch('doc_builder.backends.sphinx.EpubBuilder.build')
    def test_build_respects_pdf_flag(self,
                                     EpubBuilder_build,
                                     PdfBuilder_build,
                                     HtmlBuilder_build,
                                     mock_Popen,
                                     mock_chdir,
                                     mock_apiv2_downloads):

        # subprocess mock logic

        mock_process = mock.Mock()
        process_return_dict = {'communicate.return_value': ('SOMEGITHASH', '')}
        mock_process.configure_mock(**process_return_dict)
        mock_Popen.return_value = mock_process
        mock_Popen.side_effect = build_subprocess_side_effect

        project = ProjectFactory(
            enable_pdf_build=True,
            enable_epub_build=False)
        version = project.versions.all()[0]

        conf_path = os.path.join(project.checkout_path(version.slug), project.conf_py_file)

        # Mock open to simulate existing conf.py file
        with mock.patch('codecs.open', mock.mock_open(), create=True):
            with fake_paths_lookup({conf_path: True}):
                built_docs = build_docs(version,
                                        False,
                                        False,
                                        False,
                                        )

        # The HTML and the PDF format were built.
        self.assertEqual(HtmlBuilder_build.call_count, 1)
        self.assertEqual(PdfBuilder_build.call_count, 1)
        # Epub however was disabled and therefore not built.
        self.assertEqual(EpubBuilder_build.call_count, 0)

    @mock.patch('slumber.Resource')
    @mock.patch('os.chdir')
    @mock.patch('subprocess.Popen')
    @mock.patch('doc_builder.backends.sphinx.HtmlBuilder.build')
    @mock.patch('doc_builder.backends.sphinx.PdfBuilder.build')
    @mock.patch('doc_builder.backends.sphinx.EpubBuilder.build')
    def test_build_respects_epub_flag(self,
                                      EpubBuilder_build,
                                      PdfBuilder_build,
                                      HtmlBuilder_build,
                                      mock_Popen,
                                      mock_chdir,
                                      mock_apiv2_downloads):

        # subprocess mock logic

        mock_process = mock.Mock()
        process_return_dict = {'communicate.return_value': ('SOMEGITHASH', '')}
        mock_process.configure_mock(**process_return_dict)
        mock_Popen.return_value = mock_process
        mock_Popen.side_effect = build_subprocess_side_effect

        project = ProjectFactory(
            enable_pdf_build=False,
            enable_epub_build=True)
        version = project.versions.all()[0]

        conf_path = os.path.join(project.checkout_path(version.slug), project.conf_py_file)

        # Mock open to simulate existing conf.py file
        with mock.patch('codecs.open', mock.mock_open(), create=True):
            with fake_paths_lookup({conf_path: True}):
                built_docs = build_docs(version,
                                        False,
                                        False,
                                        False,
                                        )

        # The HTML and the Epub format were built.
        self.assertEqual(HtmlBuilder_build.call_count, 1)
        self.assertEqual(EpubBuilder_build.call_count, 1)
        # PDF however was disabled and therefore not built.
        self.assertEqual(PdfBuilder_build.call_count, 0)
