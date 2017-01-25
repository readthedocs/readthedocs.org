# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import collections
from functools import wraps

import mock
from django.conf import settings
from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project, Domain
from readthedocs.core.symlink import PublicSymlink, PrivateSymlink


def get_filesystem(path, top_level_path=None):
    """Recurse into path, return dictionary mapping of path and files

    This will return the path `path` as a nested dictionary of path objects.
    Directories are mapped to dictionary objects, file objects will have a
    `type` of `file`, and symlinks will have a `type` of `link`, with a
    parameter `target`, noting the relative path of the symlink target.

    :param path: Path to inspect
    :param top_level_path: Original path for inspection, default is `path`
    :returns: Dictionary of path objects
    :rtype: dict
    """
    fs = {}
    if top_level_path is None:
        top_level_path = path
    for child in os.listdir(path):
        full_path = os.path.join(path, child)
        if os.path.islink(full_path):
            fs[child] = {
                'type': 'link',
                'target': os.path.relpath(os.path.realpath(full_path),
                                          top_level_path)
            }
        elif os.path.isfile(full_path):
            fs[child] = {
                'type': 'file',
            }
        elif os.path.isdir(full_path):
            fs[child] = get_filesystem(full_path, top_level_path)
    return fs


class TempSiterootCase(object):

    """Override SITE_ROOT and patch necessary pieces to inspect symlink structure

    This uses some patches and overidden settings to build out symlinking in a
    temporary path.  Each test is therefore isolated, and cleanup will remove
    these paths after the test case wraps up.

    And subclasses that implement :py:cls:`TestCase` should also make use of
    :py:func:`override_settings`.
    """

    def setUp(self):
        self.maxDiff = None
        self.site_root = os.path.realpath(tempfile.mkdtemp(suffix='siteroot'))
        settings.SITE_ROOT = self.site_root
        settings.DOCROOT = os.path.join(settings.SITE_ROOT, 'user_builds')
        self.mocks = {
            'PublicSymlinkBase.CNAME_ROOT': mock.patch(
                'readthedocs.core.symlink.PublicSymlinkBase.CNAME_ROOT',
                new_callable=mock.PropertyMock
            ),
            'PublicSymlinkBase.WEB_ROOT': mock.patch(
                'readthedocs.core.symlink.PublicSymlinkBase.WEB_ROOT',
                new_callable=mock.PropertyMock
            ),
            'PublicSymlinkBase.PROJECT_CNAME_ROOT': mock.patch(
                'readthedocs.core.symlink.PublicSymlinkBase.PROJECT_CNAME_ROOT',
                new_callable=mock.PropertyMock
            ),
            'PrivateSymlinkBase.CNAME_ROOT': mock.patch(
                'readthedocs.core.symlink.PrivateSymlinkBase.CNAME_ROOT',
                new_callable=mock.PropertyMock
            ),
            'PrivateSymlinkBase.WEB_ROOT': mock.patch(
                'readthedocs.core.symlink.PrivateSymlinkBase.WEB_ROOT',
                new_callable=mock.PropertyMock
            ),
            'PrivateSymlinkBase.PROJECT_CNAME_ROOT': mock.patch(
                'readthedocs.core.symlink.PrivateSymlinkBase.PROJECT_CNAME_ROOT',
                new_callable=mock.PropertyMock
            ),
        }
        self.patches = dict((key, mock.start()) for (key, mock) in self.mocks.items())
        self.patches['PublicSymlinkBase.CNAME_ROOT'].return_value = os.path.join(
            settings.SITE_ROOT, 'public_cname_root'
        )
        self.patches['PublicSymlinkBase.WEB_ROOT'].return_value = os.path.join(
            settings.SITE_ROOT, 'public_web_root'
        )
        self.patches['PublicSymlinkBase.PROJECT_CNAME_ROOT'].return_value = os.path.join(
            settings.SITE_ROOT, 'public_cname_project'
        )
        self.patches['PrivateSymlinkBase.CNAME_ROOT'].return_value = os.path.join(
            settings.SITE_ROOT, 'private_cname_root'
        )
        self.patches['PrivateSymlinkBase.WEB_ROOT'].return_value = os.path.join(
            settings.SITE_ROOT, 'private_web_root'
        )
        self.patches['PrivateSymlinkBase.PROJECT_CNAME_ROOT'].return_value = os.path.join(
            settings.SITE_ROOT, 'private_cname_project'
        )

    def tearDown(self):
        shutil.rmtree(self.site_root)

    def assertFilesystem(self, filesystem):
        """
        Creates a nested dictionary that represents the folder structure of rootdir
        """
        self.assertEqual(filesystem, get_filesystem(self.site_root))


@override_settings()
class TestSymlinkCnames(TempSiterootCase, TestCase):

    def setUp(self):
        super(TestSymlinkCnames, self).setUp()
        self.project = get(Project, slug='kong', privacy_level='public',
                           main_language_project=None)
        self.symlink = PublicSymlink(self.project)

    def test_symlink_cname(self):
        self.domain = get(Domain, project=self.project, domain='woot.com',
                          url='http://woot.com', cname=True)
        self.symlink.symlink_cnames()
        self.assertFilesystem({
            'private_cname_project': {
                'woot.com': {'type': 'link', 'target': 'user_builds/kong'}
            },
            'private_cname_root': {
                'woot.com': {'type': 'link', 'target': 'private_web_root/kong'},
            },
            'private_web_root': {'kong': {'en': {}}},
            'public_cname_project': {
                'woot.com': {'type': 'link', 'target': 'user_builds/kong'}
            },
            'public_cname_root': {
                'woot.com': {'type': 'link', 'target': 'public_web_root/kong'},
            },
            'public_web_root': {
                'kong': {'en': {'latest': {
                    'type': 'link',
                    'target': 'user_builds/kong/rtd-builds/latest',
                }}}
            }
        })

    def test_symlink_cname_dont_link_missing_domains(self):
        """Domains should be relinked after deletion"""
        self.domain = get(Domain, project=self.project, domain='woot.com',
                          url='http://woot.com', cname=True)
        self.symlink.symlink_cnames()
        filesystem = {
            'private_cname_project': {
                'woot.com': {'type': 'link', 'target': 'user_builds/kong'}
            },
            'private_cname_root': {
                'woot.com': {'type': 'link', 'target': 'private_web_root/kong'},
            },
            'private_web_root': {'kong': {'en': {}}},
            'public_cname_project': {
                'woot.com': {'type': 'link', 'target': 'user_builds/kong'}
            },
            'public_cname_root': {
                'woot.com': {'type': 'link', 'target': 'public_web_root/kong'},
            },
            'public_web_root': {
                'kong': {'en': {'latest': {
                    'type': 'link',
                    'target': 'user_builds/kong/rtd-builds/latest',
                }}}
            }
        }
        self.assertFilesystem(filesystem)
        self.domain.delete()
        filesystem['public_cname_root'] = {}
        filesystem['private_cname_root'] = {}
        # TODO full removal is not handled by the symlink operation, and is
        # instead a celery task. This won't reflect those changes
        self.symlink.symlink_cnames()
        self.assertFilesystem(filesystem)


class BaseSubprojects(TempSiterootCase):

    def test_subproject_normal(self):
        """Symlink pass adds symlink for subproject"""
        self.project.add_subproject(self.subproject)
        self.symlink.symlink_subprojects()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'en': {}},
                'sub': {'en': {}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {
                    'en': {'latest': {
                        'type': 'link',
                        'target': 'user_builds/kong/rtd-builds/latest',
                    }},
                    'projects': {
                        'sub': {
                            'type': 'link',
                            'target': 'public_web_root/sub',
                        }
                    }
                },
                'sub': {
                    'en': {'latest': {
                        'type': 'link',
                        'target': 'user_builds/sub/rtd-builds/latest',
                    }}
                }
            }
        }
        if self.privacy == 'private':
            sub_projects = filesystem['public_web_root']['kong']['projects']
            sub_projects['sub']['target'] = 'private_web_root/sub'
            filesystem['private_web_root']['kong']['projects'] = sub_projects
            del filesystem['public_web_root']['kong']['projects']
        self.assertFilesystem(filesystem)

    def test_subproject_alias(self):
        """Symlink pass adds symlink for subproject alias"""
        self.project.add_subproject(self.subproject, alias='sweet-alias')
        self.symlink.symlink_subprojects()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'en': {}},
                'sub': {'en': {}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {
                    'en': {'latest': {
                        'type': 'link',
                        'target': 'user_builds/kong/rtd-builds/latest',
                    }},
                    'projects': {
                        'sub': {
                            'type': 'link',
                            'target': 'public_web_root/sub',
                        },
                        'sweet-alias': {
                            'type': 'link',
                            'target': 'public_web_root/sub',
                        },
                    }
                },
                'sub': {
                    'en': {'latest': {
                        'type': 'link',
                        'target': 'user_builds/sub/rtd-builds/latest',
                    }}
                }
            }
        }
        if self.privacy == 'private':
            sub_projects = filesystem['public_web_root']['kong']['projects']
            sub_projects['sub']['target'] = 'private_web_root/sub'
            sub_projects['sweet-alias']['target'] = 'private_web_root/sub'
            filesystem['private_web_root']['kong']['projects'] = sub_projects
            del filesystem['public_web_root']['kong']['projects']
        self.assertFilesystem(filesystem)

    def test_remove_subprojects(self):
        """Nonexistant subprojects are unlinked"""
        self.project.add_subproject(self.subproject)
        self.symlink.symlink_subprojects()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'en': {}},
                'sub': {'en': {}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {
                    'en': {'latest': {
                        'type': 'link',
                        'target': 'user_builds/kong/rtd-builds/latest',
                    }},
                    'projects': {
                        'sub': {
                            'type': 'link',
                            'target': 'public_web_root/sub',
                        }
                    }
                },
                'sub': {
                    'en': {'latest': {
                        'type': 'link',
                        'target': 'user_builds/sub/rtd-builds/latest',
                    }}
                }
            }
        }
        if self.privacy == 'private':
            sub_projects = filesystem['public_web_root']['kong']['projects']
            sub_projects['sub']['target'] = 'private_web_root/sub'
            filesystem['private_web_root']['kong']['projects'] = sub_projects
            del filesystem['public_web_root']['kong']['projects']
        self.assertFilesystem(filesystem)

        self.project.remove_subproject(self.subproject)
        self.symlink.symlink_subprojects()
        if self.privacy == 'public':
            filesystem['public_web_root']['kong']['projects'] = {}
        if self.privacy == 'private':
            filesystem['private_web_root']['kong']['projects'] = {}
        self.assertFilesystem(filesystem)


@override_settings()
class TestPublicSubprojects(BaseSubprojects, TestCase):

    def setUp(self):
        super(TestPublicSubprojects, self).setUp()
        self.project = get(Project, slug='kong', privacy_level='public',
                           main_language_project=None)
        self.subproject = get(Project, slug='sub', privacy_level='public',
                              main_language_project=None)
        self.symlink = PublicSymlink(self.project)
        self.privacy = 'public'


@override_settings()
class TestPrivateSubprojects(BaseSubprojects, TestCase):

    def setUp(self):
        super(TestPrivateSubprojects, self).setUp()
        self.project = get(Project, slug='kong', privacy_level='private',
                           main_language_project=None)
        self.subproject = get(Project, slug='sub', privacy_level='private',
                              main_language_project=None)
        self.symlink = PrivateSymlink(self.project)
        self.privacy = 'private'


class BaseSymlinkTranslations(TempSiterootCase):

    def test_symlink_basic(self):
        """Test basic scenario, language english, translation german"""
        self.symlink.symlink_translations()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'en': {}},
                'pip': {'de': {}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {
                    'en': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/kong/rtd-builds/latest',
                        },
                        'master': {
                            'type': 'link',
                            'target': 'user_builds/kong/rtd-builds/master',
                        },
                    },
                    'de': {
                        'type': 'link',
                        'target': 'public_web_root/pip/de',
                    },
                },
                'pip': {
                    'de': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/pip/rtd-builds/latest',
                        },
                        'master': {
                            'type': 'link',
                            'target': 'user_builds/pip/rtd-builds/master',
                        },
                    }
                }
            }
        }
        if self.privacy == 'private':
            lang = filesystem['public_web_root']['kong']['de']
            lang['target'] = 'private_web_root/pip/de'
            filesystem['private_web_root']['kong']['de'] = lang
            del filesystem['public_web_root']['kong']['de']
        self.assertFilesystem(filesystem)

    def test_symlink_non_english(self):
        """Test language german, translation english"""
        self.project.language = 'de'
        self.translation.language = 'en'
        self.project.save()
        self.translation.save()
        self.symlink.symlink_translations()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'de': {}},
                'pip': {'en': {}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {
                    'en': {
                        'type': 'link',
                        'target': 'public_web_root/pip/en',
                    },
                    'de': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/kong/rtd-builds/latest',
                        },
                        'master': {
                            'type': 'link',
                            'target': 'user_builds/kong/rtd-builds/master',
                        },
                    },
                },
                'pip': {
                    'en': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/pip/rtd-builds/latest',
                        },
                        'master': {
                            'type': 'link',
                            'target': 'user_builds/pip/rtd-builds/master',
                        },
                    }
                }
            }
        }
        if self.privacy == 'private':
            lang = filesystem['public_web_root']['kong']['en']
            lang['target'] = 'private_web_root/pip/en'
            filesystem['private_web_root']['kong']['en'] = lang
            del filesystem['public_web_root']['kong']['en']
        self.assertFilesystem(filesystem)

    def test_symlink_no_english(self):
        """Test language german, no english

        This should symlink the translation to 'en' even though there is no 'en'
        language in translations or project language
        """
        self.project.language = 'de'
        trans = self.project.translations.first()
        self.project.translations.remove(trans)
        self.project.save()
        self.assertNotIn(trans, self.project.translations.all())
        self.symlink.symlink_translations()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'de': {}},
                'pip': {'de': {}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {
                    'de': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/kong/rtd-builds/latest',
                        },
                        'master': {
                            'type': 'link',
                            'target': 'user_builds/kong/rtd-builds/master',
                        },
                    },
                },
                'pip': {
                    'de': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/pip/rtd-builds/latest',
                        },
                        'master': {
                            'type': 'link',
                            'target': 'user_builds/pip/rtd-builds/master',
                        },
                    }
                }
            }
        }
        self.assertFilesystem(filesystem)

    def test_remove_language(self):
        self.symlink.symlink_translations()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'en': {}},
                'pip': {'de': {}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {
                    'de': {
                        'type': 'link',
                        'target': 'public_web_root/pip/de',
                    },
                    'en': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/kong/rtd-builds/latest',
                        },
                        'master': {
                            'type': 'link',
                            'target': 'user_builds/kong/rtd-builds/master',
                        },
                    },
                },
                'pip': {
                    'de': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/pip/rtd-builds/latest',
                        },
                        'master': {
                            'type': 'link',
                            'target': 'user_builds/pip/rtd-builds/master',
                        },
                    }
                }
            }
        }
        if self.privacy == 'private':
            lang = filesystem['public_web_root']['kong']['de']
            lang['target'] = 'private_web_root/pip/de'
            filesystem['private_web_root']['kong']['de'] = lang
            del filesystem['public_web_root']['kong']['de']
        self.assertFilesystem(filesystem)

        trans = self.project.translations.first()
        self.project.translations.remove(trans)
        self.symlink.symlink_translations()
        if self.privacy == 'public':
            del filesystem['public_web_root']['kong']['de']
        elif self.privacy == 'private':
            del filesystem['private_web_root']['kong']['de']
        self.assertFilesystem(filesystem)


@override_settings()
class TestPublicSymlinkTranslations(BaseSymlinkTranslations, TestCase):

    def setUp(self):
        super(TestPublicSymlinkTranslations, self).setUp()
        self.project = get(Project, slug='kong', privacy_level='public',
                           main_language_project=None)
        self.translation = get(Project, slug='pip', language='de',
                               privacy_level='public',
                               main_language_project=None)
        self.project.translations.add(self.translation)
        self.symlink = PublicSymlink(self.project)
        get(Version, slug='master', verbose_name='master', active=True,
            project=self.project)
        get(Version, slug='master', verbose_name='master', active=True,
            project=self.translation)
        self.assertIn(self.translation, self.project.translations.all())
        self.privacy = 'public'


@override_settings()
class TestPrivateSymlinkTranslations(BaseSymlinkTranslations, TestCase):

    def setUp(self):
        super(TestPrivateSymlinkTranslations, self).setUp()
        self.project = get(Project, slug='kong', privacy_level='private',
                           main_language_project=None)
        self.translation = get(Project, slug='pip', language='de',
                               privacy_level='private',
                               main_language_project=None)
        self.project.translations.add(self.translation)
        self.symlink = PrivateSymlink(self.project)
        get(Version, slug='master', verbose_name='master', active=True,
            project=self.project)
        get(Version, slug='master', verbose_name='master', active=True,
            project=self.translation)
        self.assertIn(self.translation, self.project.translations.all())
        self.privacy = 'private'


@override_settings()
class TestPublicSymlinkSingleVersion(TempSiterootCase, TestCase):

    def setUp(self):
        super(TestPublicSymlinkSingleVersion, self).setUp()
        self.project = get(Project, slug='kong', privacy_level='public',
                           main_language_project=None)
        self.version = self.project.versions.get(slug='latest')
        self.version.privacy_level = 'public'
        self.version.save()
        self.symlink = PublicSymlink(self.project)

    def test_symlink_single_version(self):
        self.symlink.symlink_single_version()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'en': {}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {
                    'type': 'link',
                    'target': 'user_builds/kong/rtd-builds/latest',
                },
            }
        }
        self.assertFilesystem(filesystem)

    def test_symlink_single_version_missing(self):
        self.project.versions = []
        self.project.save()
        self.symlink = PublicSymlink(self.project)
        self.symlink.symlink_single_version()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'en': {}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {
                    'type': 'link',
                    'target': 'user_builds/kong/rtd-builds/latest',
                }
            }
        }
        self.assertFilesystem(filesystem)


class BaseSymlinkVersions(TempSiterootCase):

    def test_symlink_versions(self):
        self.symlink.symlink_versions()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'en': {}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {
                    'en': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/kong/rtd-builds/latest',
                        },
                        'stable': {
                            'type': 'link',
                            'target': 'user_builds/kong/rtd-builds/stable',
                        },
                    },
                },
            }
        }
        if self.privacy == 'private':
            versions = filesystem['public_web_root']['kong']['en']
            filesystem['private_web_root']['kong']['en'] = versions.copy()
            del filesystem['public_web_root']['kong']['en']['stable']
        self.assertFilesystem(filesystem)


@override_settings()
class TestPublicSymlinkVersions(BaseSymlinkVersions, TestCase):

    def setUp(self):
        super(TestPublicSymlinkVersions, self).setUp()
        self.project = get(Project, slug='kong', privacy_level='public',
                           main_language_project=None)
        self.stable = get(Version, slug='stable', verbose_name='stable',
                          active=True, project=self.project,
                          privacy_level='public')
        self.symlink = PublicSymlink(self.project)
        self.privacy = 'public'

    def test_symlink_private_versions(self):
        self.stable.privacy_level = 'private'
        self.stable.save()
        self.symlink.symlink_versions()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'en': {'stable': {
                    'type': 'link',
                    'target': 'user_builds/kong/rtd-builds/stable',
                }}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {'en': {'latest': {
                    'type': 'link',
                    'target': 'user_builds/kong/rtd-builds/latest',
                }}},
            }
        }
        self.assertFilesystem(filesystem)

    def test_removed_versions(self):
        self.symlink.symlink_versions()
        self.stable.delete()
        self.symlink.symlink_versions()
        filesystem = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'kong': {'en': {}},
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'kong': {'en': {'latest': {
                    'type': 'link',
                    'target': 'user_builds/kong/rtd-builds/latest',
                }}},
            }
        }
        self.assertFilesystem(filesystem)


@override_settings()
class TestPrivateSymlinkVersions(BaseSymlinkVersions, TestCase):

    def setUp(self):
        super(TestPrivateSymlinkVersions, self).setUp()
        self.project = get(Project, slug='kong', privacy_level='private',
                           main_language_project=None)
        self.stable = get(Version, slug='stable', verbose_name='stable',
                          active=True, project=self.project,
                          privacy_level='private')
        self.project.versions.update(privacy_level='private')
        self.symlink = PrivateSymlink(self.project)
        self.privacy = 'private'


@override_settings()
class TestPublicSymlinkUnicode(TempSiterootCase, TestCase):

    def setUp(self):
        super(TestPublicSymlinkUnicode, self).setUp()
        self.project = get(Project, slug='kong', name=u'foo-∫',
                           main_language_project=None)
        self.stable = get(Version, slug='foo-a', verbose_name=u'foo-∂',
                          active=True, project=self.project)
        self.symlink = PublicSymlink(self.project)

    def test_symlink_no_error(self):
        try:
            self.symlink.run()
        except:
            self.fail('Symlink run raised an exception on unicode slug')
