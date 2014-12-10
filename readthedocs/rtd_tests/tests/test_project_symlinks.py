import os
from functools import wraps

from mock import patch
from django.test import TestCase

from builds.models import Version
from projects.models import Project
from projects.symlinks import symlink_translations


def patched(fn):
    '''Patches calls to run_on_app_servers on instance methods'''

    @wraps(fn)
    def wrapper(self):

        def _collect_commands(cmd):
            self.commands.append(cmd)

        with patch('projects.symlinks.run_on_app_servers', _collect_commands):
            with patch('readthedocs.projects.symlinks.run_on_app_servers', _collect_commands):
                return fn(self)
    return wrapper


class TestSymlinkTranslations(TestCase):

    fixtures = ['eric', 'test_data']
    commands = []

    def setUp(self):
        self.project = Project.objects.get(slug='kong')
        self.translation = Project.objects.get(slug='pip')
        self.translation.language = 'de'
        self.translation.main_lanuage_project = self.project
        self.project.translations.add(self.translation)
        self.translation.save()
        self.project.save()
        Version.objects.create(verbose_name='master', slug='master',
                               active=True, project=self.project)
        Version.objects.create(verbose_name='master', slug='master',
                               active=True, project=self.translation)
        self.args = {
            'project': self.project.doc_path,
            'translation': self.translation.doc_path,
            'builds': os.path.join(self.project.doc_path, 'rtd-builds'),
        }
        self.assertIn(self.translation, self.project.translations.all())
        self.commands = []

    @patched
    def test_symlink_basic(self):
        '''Test basic scenario, language english, translation german'''
        symlink_translations(self.project.versions.first())
        commands = [
            'mkdir -p {project}/translations',
            'ln -nsf {translation}/rtd-builds {project}/translations/de',
            'ln -nsf {builds} {project}/translations/en',
        ]
        for (i, command) in enumerate(commands):
            self.assertEqual(self.commands[i], command.format(**self.args),
                             msg=('Command {0} mismatch, expecting {1}'
                                  .format(i, self.commands[i])))

    @patched
    def test_symlink_non_english(self):
        '''Test language german, translation english'''
        # Change the languages, and then clear commands, as project.save calls
        # the symlinking
        self.project.language = 'de'
        self.translation.language = 'en'
        self.project.save()
        self.translation.save()
        self.commands = []

        symlink_translations(self.project.versions.first())
        commands = [
            'mkdir -p {project}/translations',
            'ln -nsf {project}/rtd-builds {project}/translations/de',
            'ln -nsf {translation}/rtd-builds {project}/translations/en',
        ]
        for (i, command) in enumerate(commands):
            self.assertEqual(self.commands[i], command.format(**self.args),
                             msg=('Command {0} mismatch, expecting {1}'
                                  .format(i, self.commands[i])))

    @patched
    def test_symlink_no_english(self):
        '''Test language german, no english

        This should symlink the translation to 'en' even though there is no 'en'
        language in translations or project language
        '''
        # Change the languages, and then clear commands, as project.save calls
        # the symlinking
        self.project.language = 'de'
        version = self.project.translations.first()
        self.project.translations.remove(version)
        self.project.save()
        self.assertNotIn(version, self.project.translations.all())
        self.commands = []

        symlink_translations(self.project.versions.first())
        commands = [
            'mkdir -p {project}/translations',
            'ln -nsf {project}/rtd-builds {project}/translations/de',
            'ln -nsf {project}/rtd-builds {project}/translations/en',
        ]
        for (i, command) in enumerate(commands):
            self.assertEqual(self.commands[i], command.format(**self.args),
                             msg=('Command {0} mismatch, expecting {1}'
                                  .format(i, self.commands[i])))
