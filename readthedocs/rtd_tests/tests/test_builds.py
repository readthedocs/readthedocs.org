import subprocess

from django.test import TestCase
import mock

from projects.tasks import build_docs
from rtd_tests.factories.projects_factories import ProjectFactory


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

        with mock.patch('codecs.open', mock.mock_open(), create=True):
            built_docs = build_docs(version,
                                    False,
                                    False,
                                    False,
                                    False,
                                    False,
                                    False,
                                    False,
                                    )

        builder = project.doc_builder()(version)
        self.assertIn(builder.sphinx_builder,
                      str(mock_Popen.call_args_list[1])
                      )

        # We are using the comment builder

    def test_builder_comments(self):

        # Normal build
        project = ProjectFactory(allow_comments=True)
        version = project.versions.all()[0]
        builder = project.doc_builder()(version)
        self.assertEqual(builder.sphinx_builder, 'readthedocs-comments')

    def test_builder_no_comments(self):

        # Normal build
        project = ProjectFactory(allow_comments=False)
        version = project.versions.all()[0]
        builder = project.doc_builder()(version)
        self.assertEqual(builder.sphinx_builder, 'readthedocs')
