import os
from functools import wraps

from mock import patch
from django.conf import settings
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project, Domain
from readthedocs.projects.symlinks import symlink_translations, symlink_cnames


def patched(fn):
    '''Patches calls to run_on_app_servers on instance methods'''

    @wraps(fn)
    def wrapper(self):

        def _collect_commands(cmd):
            self.commands.append(cmd)

        with patch('readthedocs.projects.symlinks.run_on_app_servers', _collect_commands):
            with patch('readthedocs.projects.symlinks.run_on_app_servers', _collect_commands):
                return fn(self)
    return wrapper


class TestSymlinkCnames(TestCase):

    def setUp(self):
        self.project = get(Project, slug='kong')
        self.version = get(Version, verbose_name='latest', active=True, project=self.project)
        self.args = {
            'project': self.project.doc_path,
            'cnames_root': settings.CNAME_ROOT,
            'new_cnames_root': os.path.join(getattr(settings, 'SITE_ROOT'), 'cnametoproject'),
            'build_path': self.project.doc_path,
        }
        self.commands = []

    @patched
    def test_symlink_cname(self):
        self.cname = get(Domain, project=self.project, url='http://woot.com', cname=True)
        symlink_cnames(self.project)
        self.args['cname'] = self.cname.clean_host
        commands = [
            'mkdir -p {cnames_root}',
            'ln -nsf {build_path}/rtd-builds {cnames_root}/{cname}',
            'mkdir -p {new_cnames_root}',
            'ln -nsf {build_path} {new_cnames_root}/{cname}'
        ]

        for index, command in enumerate(commands):
            self.assertEqual(self.commands[index], command.format(**self.args))


class TestSymlinkTranslations(TestCase):

    commands = []

    def setUp(self):
        self.project = get(Project, slug='kong')
        self.translation = get(Project, slug='pip')
        self.translation.language = 'de'
        self.translation.main_lanuage_project = self.project
        self.project.translations.add(self.translation)
        self.translation.save()
        self.project.save()
        get(Version, verbose_name='master', active=True, project=self.project)
        get(Version, verbose_name='master', active=True, project=self.translation)
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
        symlink_translations(self.project)
        commands = [
            'mkdir -p {project}/translations',
            'ln -nsf {translation}/rtd-builds {project}/translations/de',
            'ln -nsf {builds} {project}/translations/en',
        ]

        for command in commands:
            self.assertIsNotNone(
                self.commands.pop(
                    self.commands.index(command.format(**self.args))
                ))

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

        symlink_translations(self.project)
        commands = [
            'mkdir -p {project}/translations',
            'ln -nsf {project}/rtd-builds {project}/translations/de',
            'ln -nsf {translation}/rtd-builds {project}/translations/en',
        ]

        for command in commands:
            self.assertIsNotNone(
                self.commands.pop(
                    self.commands.index(command.format(**self.args))
                ))

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

        symlink_translations(self.project)
        commands = [
            'mkdir -p {project}/translations',
            'ln -nsf {project}/rtd-builds {project}/translations/de',
            'ln -nsf {project}/rtd-builds {project}/translations/en',
        ]

        for command in commands:
            self.assertIsNotNone(
                self.commands.pop(
                    self.commands.index(command.format(**self.args))
                ))
