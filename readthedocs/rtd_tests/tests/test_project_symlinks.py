# -*- coding: utf-8 -*-

from __future__ import absolute_import
from builtins import object
import os
import shutil
import tempfile

import mock
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project, Domain
from readthedocs.projects.tasks import broadcast_remove_orphan_symlinks, remove_orphan_symlinks, symlink_project
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


TEMP_SITE_ROOT = os.path.realpath(tempfile.mkdtemp(suffix='siteroot'))
TEMP_DOCROOT = os.path.join(TEMP_SITE_ROOT, 'user_builds')


@override_settings(
    SITE_ROOT=TEMP_SITE_ROOT,
    DOCROOT=TEMP_DOCROOT,
)
class TempSiteRootTestCase(TestCase):

    """
    Override SITE_ROOT and patch necessary pieces to inspect symlink structure.

    This uses some patches and overridden settings to build out symlinking in a
    temporary path.  Each test is therefore isolated, and cleanup will remove
    these paths after the test case wraps up.
    """

    def setUp(self):
        self.maxDiff = None
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
        self.patches = dict((key, mock.start()) for (key, mock) in list(self.mocks.items()))
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
        shutil.rmtree(settings.SITE_ROOT)

    def assertFilesystem(self, filesystem):
        """
        Creates a nested dictionary that represents the folder structure of rootdir
        """
        self.assertEqual(filesystem, get_filesystem(settings.SITE_ROOT))


class BaseSymlinkCnames(object):

    def setUp(self):
        super(BaseSymlinkCnames, self).setUp()
        self.project = get(Project, slug='kong', privacy_level=self.privacy,
                           main_language_project=None)
        self.project.versions.update(privacy_level=self.privacy)
        self.project.save()
        self.symlink = self.symlink_class(self.project)

    def test_symlink_cname(self):
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
        if self.privacy == 'private':
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)

    def test_symlink_remove_orphan_symlinks(self):
        self.domain = get(Domain, project=self.project, domain='woot.com',
                          url='http://woot.com', cname=True)
        self.symlink.symlink_cnames()

        # Editing the Domain and calling save will symlink the new domain and
        # leave the old one as orphan.
        self.domain.domain = 'foobar.com'
        self.domain.save()

        filesystem = {
            'private_cname_project': {
                'foobar.com': {'type': 'link', 'target': 'user_builds/kong'},
                'woot.com': {'type': 'link', 'target': 'user_builds/kong'},
            },
            'private_cname_root': {
                'foobar.com': {'type': 'link', 'target': 'private_web_root/kong'},
                'woot.com': {'type': 'link', 'target': 'private_web_root/kong'},
            },
            'private_web_root': {'kong': {'en': {}}},
            'public_cname_project': {
                'foobar.com': {'type': 'link', 'target': 'user_builds/kong'},
                'woot.com': {'type': 'link', 'target': 'user_builds/kong'},
            },
            'public_cname_root': {
                'foobar.com': {'type': 'link', 'target': 'public_web_root/kong'},
                'woot.com': {'type': 'link', 'target': 'public_web_root/kong'},
            },
            'public_web_root': {
                'kong': {'en': {'latest': {
                    'type': 'link',
                    'target': 'user_builds/kong/rtd-builds/latest',
                }}}
            }
        }
        if self.privacy == 'private':
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)

        remove_orphan_symlinks()
        filesystem = {
            'private_cname_project': {
                'foobar.com': {'type': 'link', 'target': 'user_builds/kong'},
            },
            'private_cname_root': {
                'foobar.com': {'type': 'link', 'target': 'private_web_root/kong'},
            },
            'private_web_root': {'kong': {'en': {}}},
            'public_cname_project': {
                'foobar.com': {'type': 'link', 'target': 'user_builds/kong'},
            },
            'public_cname_root': {
                'foobar.com': {'type': 'link', 'target': 'public_web_root/kong'},
            },
            'public_web_root': {
                'kong': {'en': {'latest': {
                    'type': 'link',
                    'target': 'user_builds/kong/rtd-builds/latest',
                }}},
            },
        }
        if self.privacy == 'private':
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root

        self.assertFilesystem(filesystem)

    def test_broadcast_remove_orphan_symlinks(self):
        """Broadcast orphan symlinks is called with the proper attributes."""
        with mock.patch('readthedocs.projects.tasks.broadcast') as broadcast:
            broadcast_remove_orphan_symlinks()

        broadcast.assert_called_with(
            type='web',
            task=remove_orphan_symlinks,
            args=[],
        )

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
        if self.privacy == 'private':
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)
        self.domain.delete()
        filesystem['private_cname_root'] = {}
        filesystem['public_cname_root'] = {}
        # TODO full removal is not handled by the symlink operation, and is
        # instead a celery task. This won't reflect those changes
        self.symlink.symlink_cnames()
        self.assertFilesystem(filesystem)


class TestPublicSymlinkCnames(BaseSymlinkCnames, TempSiteRootTestCase):
    privacy = 'public'
    symlink_class = PublicSymlink


class TestPrivateSymlinkCnames(BaseSymlinkCnames, TempSiteRootTestCase):
    privacy = 'private'
    symlink_class = PrivateSymlink


class BaseSubprojects(object):

    def setUp(self):
        super(BaseSubprojects, self).setUp()
        self.project = get(Project, slug='kong', privacy_level=self.privacy,
                           main_language_project=None)
        self.project.versions.update(privacy_level=self.privacy)
        self.project.save()
        self.subproject = get(Project, slug='sub', privacy_level=self.privacy,
                              main_language_project=None)
        self.subproject.versions.update(privacy_level=self.privacy)
        self.subproject.save()
        self.symlink = self.symlink_class(self.project)

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
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            public_root['kong']['projects']['sub']['target'] = 'private_web_root/sub'
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
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
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            public_root['kong']['projects']['sub']['target'] = 'private_web_root/sub'
            public_root['kong']['projects']['sweet-alias']['target'] = 'private_web_root/sub'
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)

    def test_subproject_alias_with_spaces(self):
        """Symlink pass adds symlink for subproject alias"""
        self.project.add_subproject(self.subproject, alias='Sweet Alias')
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
                        'Sweet Alias': {
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
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            public_root['kong']['projects']['sub']['target'] = 'private_web_root/sub'
            public_root['kong']['projects']['Sweet Alias']['target'] = 'private_web_root/sub'
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)

    def test_remove_subprojects(self):
        """Nonexistent subprojects are unlinked"""
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
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            public_root['kong']['projects']['sub']['target'] = 'private_web_root/sub'
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)

        self.project.remove_subproject(self.subproject)
        self.symlink.symlink_subprojects()
        if self.privacy == 'public':
            filesystem['public_web_root']['kong']['projects'] = {}
        if self.privacy == 'private':
            filesystem['private_web_root']['kong']['projects'] = {}
        self.assertFilesystem(filesystem)


class TestPublicSubprojects(BaseSubprojects, TempSiteRootTestCase):
    privacy = 'public'
    symlink_class = PublicSymlink


class TestPrivateSubprojects(BaseSubprojects, TempSiteRootTestCase):
    privacy = 'private'
    symlink_class = PrivateSymlink


class BaseSymlinkTranslations(object):

    def setUp(self):
        super(BaseSymlinkTranslations, self).setUp()
        self.project = get(Project, slug='kong', privacy_level=self.privacy,
                           main_language_project=None)
        self.project.versions.update(privacy_level=self.privacy)
        self.project.save()
        self.translation = get(Project, slug='pip', language='de',
                               privacy_level=self.privacy,
                               main_language_project=None)
        self.translation.versions.update(privacy_level=self.privacy)
        self.translation.save()
        self.project.translations.add(self.translation)
        self.symlink = self.symlink_class(self.project)
        get(Version, slug='master', verbose_name='master', active=True,
            project=self.project, privacy_level=self.privacy)
        get(Version, slug='master', verbose_name='master', active=True,
            project=self.translation, privacy_level=self.privacy)
        self.assertIn(self.translation, self.project.translations.all())

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
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            public_root['kong']['de']['target'] = 'private_web_root/pip/de'
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
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
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            public_root['kong']['en']['target'] = 'private_web_root/pip/en'
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
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
        if self.privacy == 'private':
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
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
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            public_root['kong']['de']['target'] = 'private_web_root/pip/de'
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)

        trans = self.project.translations.first()
        self.project.translations.remove(trans)
        self.symlink.symlink_translations()
        if self.privacy == 'public':
            del filesystem['public_web_root']['kong']['de']
        elif self.privacy == 'private':
            del filesystem['private_web_root']['kong']['de']
        self.assertFilesystem(filesystem)


class TestPublicSymlinkTranslations(BaseSymlinkTranslations, TempSiteRootTestCase):
    privacy = 'public'
    symlink_class = PublicSymlink


class TestPrivateSymlinkTranslations(BaseSymlinkTranslations, TempSiteRootTestCase):
    privacy = 'private'
    symlink_class = PrivateSymlink


class BaseSymlinkSingleVersion(object):

    def setUp(self):
        super(BaseSymlinkSingleVersion, self).setUp()
        self.project = get(Project, slug='kong', privacy_level=self.privacy,
                           main_language_project=None)
        self.project.versions.update(privacy_level=self.privacy)
        self.project.save()
        self.version = self.project.versions.get(slug='latest')
        self.version.privacy_level = self.privacy
        self.version.save()
        self.symlink = self.symlink_class(self.project)

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
        if self.privacy == 'private':
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)

    def test_symlink_single_version_missing(self):
        self.project.versions = []
        self.project.save()
        self.symlink = self.symlink_class(self.project)
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
        if self.privacy == 'private':
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)


class TestPublicSymlinkSingleVersion(BaseSymlinkSingleVersion, TempSiteRootTestCase):
    privacy = 'public'
    symlink_class = PublicSymlink


class TestPublicSymlinkSingleVersion(BaseSymlinkSingleVersion, TempSiteRootTestCase):
    privacy = 'private'
    symlink_class = PrivateSymlink


class BaseSymlinkVersions(object):

    def setUp(self):
        super(BaseSymlinkVersions, self).setUp()
        self.project = get(Project, slug='kong', privacy_level=self.privacy,
                           main_language_project=None)
        self.project.versions.update(privacy_level=self.privacy)
        self.project.save()
        self.stable = get(Version, slug='stable', verbose_name='stable',
                          active=True, project=self.project,
                          privacy_level=self.privacy)
        self.project.versions.update(privacy_level=self.privacy)
        self.symlink = self.symlink_class(self.project)

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
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)

    def test_removed_versions(self):
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
                'kong': {'en': {
                    'latest': {
                        'type': 'link',
                        'target': 'user_builds/kong/rtd-builds/latest',
                    },
                    'stable': {
                        'type': 'link',
                        'target': 'user_builds/kong/rtd-builds/stable',
                    },
                }},
            }
        }
        if self.privacy == 'private':
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)

        self.project.versions.filter(slug='stable').delete()
        self.project.save()
        self.symlink.symlink_versions()
        if self.privacy == 'public':
            del filesystem['public_web_root']['kong']['en']['stable']
        elif self.privacy == 'private':
            del filesystem['private_web_root']['kong']['en']['stable']
        self.assertFilesystem(filesystem)

    def test_symlink_other_versions(self):
        self.stable.privacy_level = 'private' if self.privacy == 'public' else 'public'
        self.stable.save()
        self.project.save()
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
        if self.privacy == 'private':
            public_root = filesystem['public_web_root'].copy()
            private_root = filesystem['private_web_root'].copy()
            filesystem['public_web_root'] = private_root
            filesystem['private_web_root'] = public_root
        self.assertFilesystem(filesystem)


class TestPublicSymlinkVersions(BaseSymlinkVersions, TempSiteRootTestCase):
    privacy = 'public'
    symlink_class = PublicSymlink


class TestPrivateSymlinkVersions(BaseSymlinkVersions, TempSiteRootTestCase):
    privacy = 'private'
    symlink_class = PrivateSymlink


class TestPublicSymlinkUnicode(TempSiteRootTestCase):

    def setUp(self):
        super(TestPublicSymlinkUnicode, self).setUp()
        self.project = get(Project, slug='kong', name=u'foo-∫',
                           main_language_project=None)
        self.project.save()
        self.stable = get(Version, slug='foo-a', verbose_name=u'foo-∂',
                          active=True, project=self.project)
        self.symlink = PublicSymlink(self.project)

    def test_symlink_no_error(self):
        try:
            self.symlink.run()
        except:
            self.fail('Symlink run raised an exception on unicode slug')

    def test_symlink_broadcast_calls_on_project_save(self):
        """
        Test calls to ``readthedocs.core.utils.broadcast`` on Project.save().

        When a Project is saved, we need to check that we are calling
        ``broadcast`` utility with the proper task and arguments to re-symlink
        them.
        """
        with mock.patch('readthedocs.projects.models.broadcast') as broadcast:
            project = get(Project)
            # skipped on first save
            broadcast.assert_not_called()

            broadcast.reset_mock()
            project.description = 'New description'
            project.save()
            # called once for this project itself
            broadcast.assert_any_call(
                type='app',
                task=symlink_project,
                args=[project.pk],
            )

            broadcast.reset_mock()
            subproject = get(Project)
            # skipped on first save
            broadcast.assert_not_called()

            project.add_subproject(subproject)
            # subproject.save() is not called
            broadcast.assert_not_called()

            subproject.description = 'New subproject description'
            subproject.save()
            # subproject symlinks
            broadcast.assert_any_call(
                type='app',
                task=symlink_project,
                args=[subproject.pk],
            )
            # superproject symlinks
            broadcast.assert_any_call(
                type='app',
                task=symlink_project,
                args=[project.pk],
            )


class TestPublicPrivateSymlink(TempSiteRootTestCase):

    def setUp(self):
        super(TestPublicPrivateSymlink, self).setUp()
        from django.contrib.auth.models import User

        self.user = get(User)
        self.project = get(
            Project, name='project', slug='project', privacy_level='public',
            users=[self.user], main_language_project=None)
        self.project.versions.update(privacy_level='public')
        self.project.save()

        self.subproject = get(
            Project, name='subproject', slug='subproject', privacy_level='public',
            users=[self.user], main_language_project=None)
        self.subproject.versions.update(privacy_level='public')
        self.subproject.save()

    def test_change_subproject_privacy(self):
        """
        Change subproject's ``privacy_level`` creates proper symlinks.

        When the ``privacy_level`` changes in the subprojects, we need to
        re-symlink the superproject also to keep in sync its symlink under the
        private/public roots.
        """
        filesystem_before = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'project': {
                    'en': {},
                },
                'subproject': {
                    'en': {},
                },
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'project': {
                    'en': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/project/rtd-builds/latest',
                        },
                    },
                    'projects': {
                        'subproject': {
                            'type': 'link',
                            'target': 'public_web_root/subproject',
                        },
                    },
                },
                'subproject': {
                    'en': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/subproject/rtd-builds/latest',
                        },
                    },
                },
            },
        }

        filesystem_after = {
            'private_cname_project': {},
            'private_cname_root': {},
            'private_web_root': {
                'project': {
                    'en': {},
                    'projects': {
                        'subproject': {
                            'type': 'link',
                            'target': 'private_web_root/subproject',
                        },
                    },
                },
                'subproject': {
                    'en': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/subproject/rtd-builds/latest',
                        },
                    },
                },
            },
            'public_cname_project': {},
            'public_cname_root': {},
            'public_web_root': {
                'project': {
                    'en': {
                        'latest': {
                            'type': 'link',
                            'target': 'user_builds/project/rtd-builds/latest',
                        },
                    },
                    'projects': {},
                },
                'subproject': {
                    'en': {},
                },
            },
        }

        self.assertEqual(self.project.subprojects.all().count(), 0)
        self.assertEqual(self.subproject.superprojects.all().count(), 0)
        self.project.add_subproject(self.subproject)
        self.assertEqual(self.project.subprojects.all().count(), 1)
        self.assertEqual(self.subproject.superprojects.all().count(), 1)

        self.assertTrue(self.project.versions.first().active)
        self.assertTrue(self.subproject.versions.first().active)
        symlink_project(self.project.pk)

        self.assertFilesystem(filesystem_before)

        self.client.force_login(self.user)
        self.client.post(
            reverse('project_version_detail',
                    kwargs={
                        'project_slug': self.subproject.slug,
                        'version_slug': self.subproject.versions.first().slug,
                    }),
            data={'privacy_level': 'private', 'active': True},
        )

        self.assertEqual(self.subproject.versions.first().privacy_level, 'private')
        self.assertTrue(self.subproject.versions.first().active)

        self.client.post(
            reverse('projects_advanced',
                    kwargs={
                        'project_slug': self.subproject.slug,
                    }),
            data={
                # Required defaults
                'python_interpreter': 'python',
                'default_version': 'latest',

                'privacy_level': 'private',
            },
        )

        self.assertTrue(self.subproject.versions.first().active)
        self.subproject.refresh_from_db()
        self.assertEqual(self.subproject.privacy_level, 'private')
        self.assertFilesystem(filesystem_after)
