from StringIO import StringIO

from django.test import TestCase
from mock import patch

from core.management.commands import run_docker
from projects.models import Project
from builds.models import Version


class TestRunDocker(TestCase):
    '''Test run_docker command with good input and output'''

    fixtures = ['test_data']

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = Version(slug='foo', verbose_name='foobar')
        self.project.versions.add(self.version)

    def _get_input(self, files=None):
        return ('{"project": {"id": 6, "name": "Pip", "slug": "pip"},'
                '"id": 71, "type": "tag", "identifier": "437fb316fbbdba1acdd22e07dbe7c4809ffd97e6",'
                '"verbose_name": "stable", "slug": "stable"}')

    def _docker_build(data):
        if isinstance(data, Version):
            return {'html': (0, 'DOCKER PASS', '')}
        else:
            return {'html': (1, '', 'DOCKER FAIL')}

    def test_stdin(self):
        '''Test docker build command'''

        def _input(_, files=None):
            return '{"test": "foobar"}'

        with patch.object(run_docker.Command, '_get_input', _input):
            cmd = run_docker.Command()
            assert cmd._get_input() == '{"test": "foobar"}'

    @patch.object(run_docker.Command, '_get_input', _get_input)
    @patch('projects.tasks.docker_build', _docker_build)
    @patch('sys.stdout', new_callable=StringIO)
    def test_good_input(self, mock_output):
        '''Test docker build command'''
        cmd = run_docker.Command()
        self.assertEqual(cmd._get_input(), self._get_input())
        cmd.handle()
        self.assertEqual(
            mock_output.getvalue(),
            '{"html": [0, "DOCKER PASS", ""]}\n'
        )

    @patch('projects.tasks.docker_build', _docker_build)
    def test_bad_input(self):
        '''Test docker build command'''
        with patch.object(run_docker.Command, '_get_input') as mock_input:
            with patch('sys.stdout', new_callable=StringIO) as mock_output:
                mock_input.return_value = 'BAD JSON'
                cmd = run_docker.Command()
                cmd.handle()
                self.assertEqual(
                    mock_output.getvalue(),
                    ('{"doc_builder": '
                     '[-1, "", "ValueError: No JSON object could be decoded"]}'
                     '\n')
                )
