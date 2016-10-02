from django.test import TestCase
import json
import logging
import mock

from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects import tasks

log = logging.getLogger(__name__)


class BasePostCommitTest(TestCase):
    def _setup(self):
        self.rtfd = get(
            Project, repo='https://github.com/rtfd/readthedocs.org', slug='read-the-docs')
        self.rtfd_not_ok = get(
            Version, project=self.rtfd, slug='not_ok', identifier='not_ok', active=False)
        self.rtfd_awesome = get(
            Version, project=self.rtfd, slug='awesome', identifier='awesome', active=True)

        self.pip = get(Project, repo='https://bitbucket.org/pip/pip', repo_type='hg')
        self.pip_not_ok = get(
            Version, project=self.pip, slug='not_ok', identifier='not_ok', active=False)
        self.sphinx = get(Project, repo='https://bitbucket.org/sphinx/sphinx', repo_type='git')

        self.mocks = [mock.patch('readthedocs.core.views.hooks.trigger_build')]
        self.patches = [m.start() for m in self.mocks]

        self.client.login(username='eric', password='test')


class GitLabWebHookTest(BasePostCommitTest):
    fixtures = ["eric"]

    def setUp(self):
        self._setup()

        self.payload = {
            "object_kind": "push",
            "before": "95790bf891e76fee5e1747ab589903a6a1f80f22",
            "after": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
            "ref": "refs/heads/awesome",
            "checkout_sha": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
            "user_id": 4,
            "user_name": "John Smith",
            "user_email": "john@example.com",
            "project_id": 15,
            "project":{
                "name":"readthedocs",
                "description":"",
                "web_url":"http://example.com/mike/diaspora",
                "avatar_url": None,
                "git_ssh_url":"git@github.com:rtfd/readthedocs.org.git",
                "git_http_url":"http://github.com/rtfd/readthedocs.org.git",
                "namespace":"Mike",
                "visibility_level":0,
                "path_with_namespace":"mike/diaspora",
                "default_branch":"master",
                "homepage":"http://example.com/mike/diaspora",
                "url":"git@github.com/rtfd/readthedocs.org.git",
                "ssh_url":"git@github.com/rtfd/readthedocs.org.git",
                "http_url":"http://github.com/rtfd/readthedocs.org.git"
            },
            "repository":{
                "name": "Diaspora",
                "url": "git@github.com:rtfd/readthedocs.org.git",
                "description": "",
                "homepage": "http://github.com/rtfd/readthedocs.org",
                "git_http_url": "http://github.com/rtfd/readthedocs.org.git",
                "git_ssh_url": "git@github.com:rtfd/readthedocs.org.git",
                "visibility_level": 0
            },
            "commits": [
                {
                    "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
                    "message": "Update Catalan translation to e38cb41.",
                    "timestamp": "2011-12-12T14:27:31+02:00",
                    "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
                    "author": {
                        "name": "Jordi Mallach",
                        "email": "jordi@softcatala.org"
                    },
                    "added": ["CHANGELOG"],
                    "modified": ["app/controller/application.rb"],
                    "removed": []
                },
                {
                    "id": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
                    "message": "fixed readme",
                    "timestamp": "2012-01-03T23:36:29+02:00",
                    "url": "http://example.com/mike/diaspora/commit/da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
                    "author": {
                        "name": "GitLab dev user",
                        "email": "gitlabdev@dv6700.(none)"
                    },
                    "added": ["CHANGELOG"],
                    "modified": ["app/controller/application.rb"],
                    "removed": []
                }
            ],
            "total_commits_count": 4
        }

    def test_gitlab_post_commit_hook_builds_branch_docs_if_it_should(self):
        """GitLab webhook should only build active versions"""
        r = self.client.post('/gitlab/', data=json.dumps(self.payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) Build Started: github.com/rtfd/readthedocs.org [awesome]')
        self.payload['ref'] = 'refs/heads/not_ok'
        r = self.client.post('/gitlab/', data=json.dumps(self.payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) Not Building: github.com/rtfd/readthedocs.org [not_ok]')
        self.payload['ref'] = 'refs/heads/unknown'
        r = self.client.post('/gitlab/', data=json.dumps(self.payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, '(URL Build) No known branches were pushed to.')

    def test_gitlab_post_commit_knows_default_branches(self):
        """
        Test the gitlab post commit hook so that the default branch
        will be respected and built as the latest version.
        """
        rtd = Project.objects.get(slug='read-the-docs')
        old_default = rtd.default_branch
        rtd.default_branch = 'master'
        rtd.save()
        self.payload['ref'] = 'refs/heads/master'

        r = self.client.post('/gitlab/', data=json.dumps(self.payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) Build Started: github.com/rtfd/readthedocs.org [latest]')

        rtd.default_branch = old_default
        rtd.save()


class GitHubPostCommitTest(BasePostCommitTest):
    fixtures = ["eric"]

    def setUp(self):
        self._setup()

        self.payload = {
            "after": "5ad757394b926e5637ffeafe340f952ef48bd270",
            "base_ref": "refs/heads/master",
            "before": "5b4e453dc913b08642b1d4fb10ed23c9d6e5b129",
            "commits": [
                {
                    "added": [],
                    "author": {
                        "email": "eric@ericholscher.com",
                        "name": "Eric Holscher",
                        "username": "ericholscher"
                    },
                    "distinct": False,
                    "id": "11f229c6a78f5bc8cb173104a3f7a68cdb7eb15a",
                    "message": "Fix it on the front list as well.",
                    "modified": [
                        "readthedocs/templates/core/project_list_detailed.html"
                    ],
                    "removed": [],
                    "timestamp": "2011-09-12T19:38:55-07:00",
                    "url": ("https://github.com/wraithan/readthedocs.org/"
                            "commit/11f229c6a78f5bc8cb173104a3f7a68cdb7eb15a")
                },
            ],
            "compare": ("https://github.com/wraithan/readthedocs.org/compare/"
                        "5b4e453...5ad7573"),
            "created": False,
            "deleted": False,
            "forced": False,
            "pusher": {
                "name": "none"
            },
            "ref": "refs/heads/awesome",
            "repository": {
                "created_at": "2011/09/09 14:20:13 -0700",
                "description": "source code to readthedocs.org",
                "fork": True,
                "forks": 0,
                "has_downloads": True,
                "has_issues": False,
                "has_wiki": True,
                "homepage": "http://rtfd.org/",
                "language": "Python",
                "name": "readthedocs.org",
                "open_issues": 0,
                "owner": {
                    "email": "XWraithanX@gmail.com",
                    "name": "wraithan"
                },
                "private": False,
                "pushed_at": "2011/09/12 22:33:34 -0700",
                "size": 140,
                "url": "https://github.com/rtfd/readthedocs.org",
                "ssh_url": "git@github.com:rtfd/readthedocs.org.git",
                "watchers": 1

            }
        }

    def test_github_upper_case_repo(self):
        """
        Test the github post commit hook will build properly with upper case
        repository.
        This allows for capitalization differences in post-commit hook URL's.
        """
        payload = self.payload.copy()
        payload['repository']['url'] = payload['repository']['url'].upper()
        r = self.client.post('/github/', data=json.dumps(payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content,
            '(URL Build) Build Started: HTTPS://GITHUB.COM/RTFD/READTHEDOCS.ORG [awesome]'
        )
        self.payload['ref'] = 'refs/heads/not_ok'

    def test_400_on_no_ref(self):
        """
        GitHub sometimes sends us a post-commit hook without a ref.
        This means we don't know what branch to build,
        so return a 400.
        """
        payload = self.payload.copy()
        del payload['ref']
        r = self.client.post('/github/', data=json.dumps(payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_private_repo_mapping(self):
        """
        Test for private GitHub repo mapping.

        Previously we were missing triggering post-commit hooks because
        we only compared against the *public* ``github.com/user/repo`` URL.
        Users can also enter a ``github.com:user/repo`` URL,
        which we should support.
        """
        self.rtfd.repo = 'git@github.com:rtfd/readthedocs.org'
        self.rtfd.save()
        payload = self.payload.copy()
        r = self.client.post('/github/', data=json.dumps(payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) Build Started: github.com/rtfd/readthedocs.org [awesome]')

    def test_github_post_commit_hook_builds_branch_docs_if_it_should(self):
        """
        Test the github post commit hook to see if it will only build
        versions that are set to be built if the branch they refer to
        is updated. Otherwise it is no op.
        """
        r = self.client.post('/github/', data=json.dumps(self.payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) Build Started: github.com/rtfd/readthedocs.org [awesome]')
        self.payload['ref'] = 'refs/heads/not_ok'
        r = self.client.post('/github/', data=json.dumps(self.payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) Not Building: github.com/rtfd/readthedocs.org [not_ok]')
        self.payload['ref'] = 'refs/heads/unknown'
        r = self.client.post('/github/', data=json.dumps(self.payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, '(URL Build) No known branches were pushed to.')

    def test_github_post_commit_knows_default_branches(self):
        """
        Test the github post commit hook so that the default branch
        will be respected and built as the latest version.
        """
        rtd = Project.objects.get(slug='read-the-docs')
        old_default = rtd.default_branch
        rtd.default_branch = 'master'
        rtd.save()
        self.payload['ref'] = 'refs/heads/master'

        r = self.client.post('/github/', data=json.dumps(self.payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) Build Started: github.com/rtfd/readthedocs.org [latest]')

        rtd.default_branch = old_default
        rtd.save()


class CorePostCommitTest(BasePostCommitTest):
    fixtures = ["eric"]

    def setUp(self):
        self._setup()

    def test_core_commit_hook(self):
        rtd = Project.objects.get(slug='read-the-docs')
        rtd.default_branch = 'master'
        rtd.save()
        r = self.client.post('/build/%s' % rtd.pk, {'version_slug': 'master'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r._headers['location'][1], 'http://testserver/projects/read-the-docs/builds/')

    def test_hook_state_tracking(self):
        rtd = Project.objects.get(slug='read-the-docs')
        self.assertEqual(Project.objects.get(slug='read-the-docs').has_valid_webhook, False)
        self.client.post('/build/%s' % rtd.pk, {'version_slug': 'latest'})
        # Need to re-query to get updated DB entry
        self.assertEqual(Project.objects.get(slug='read-the-docs').has_valid_webhook, True)


class BitBucketHookTests(BasePostCommitTest):

    def setUp(self):
        self._setup()

        self.hg_payload = {
            "canon_url": "https://bitbucket.org",
            "commits": [
                {
                    "author": "marcus",
                    "branch": "default",
                    "files": [
                        {
                            "file": "somefile.py",
                            "type": "modified"
                        }
                    ],
                    "message": "Added some featureA things",
                    "node": "d14d26a93fd2",
                    "parents": [
                            "1b458191f31a"
                    ],
                    "raw_author": "Marcus Bertrand <marcus@somedomain.com>",
                    "raw_node": "d14d26a93fd28d3166fa81c0cd3b6f339bb95bfe",
                    "revision": 3,
                    "size": -1,
                    "timestamp": "2012-05-30 06:07:03",
                    "utctimestamp": "2012-05-30 04:07:03+00:00"
                }
            ],
            "repository": {
                "absolute_url": "/pip/pip/",
                "fork": False,
                "is_private": True,
                "name": "Project X",
                "owner": "marcus",
                "scm": "hg",
                "slug": "project-x",
                "website": ""
            },
            "user": "marcus"
        }

        self.git_payload = {
            "canon_url": "https://bitbucket.org",
            "commits": [
                {
                    "author": "marcus",
                    "branch": "master",
                    "files": [
                        {
                            "file": "somefile.py",
                            "type": "modified"
                        }
                    ],
                    "message": "Added some more things to somefile.py\n",
                    "node": "620ade18607a",
                    "parents": [
                            "702c70160afc"
                    ],
                    "raw_author": "Marcus Bertrand <marcus@somedomain.com>",
                    "raw_node": "620ade18607ac42d872b568bb92acaa9a28620e9",
                    "revision": None,
                    "size": -1,
                    "timestamp": "2012-05-30 05:58:56",
                    "utctimestamp": "2012-05-30 03:58:56+00:00"
                }
            ],
            "repository": {
                "absolute_url": "/sphinx/sphinx/",
                "fork": False,
                "is_private": True,
                "name": "Project X",
                "owner": "marcus",
                "scm": "git",
                "slug": "project-x",
                "website": "https://atlassian.com/"
            },
            "user": "marcus"
        }

    def test_bitbucket_post_commit(self):
        r = self.client.post('/bitbucket/', data=json.dumps(self.hg_payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) Build Started: bitbucket.org/pip/pip [latest]')

        r = self.client.post('/bitbucket/', data=json.dumps(self.git_payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) Build Started: bitbucket.org/sphinx/sphinx [latest]')

    def test_bitbucket_post_commit_hook_builds_branch_docs_if_it_should(self):
        """
        Test the bitbucket post commit hook to see if it will only build
        versions that are set to be built if the branch they refer to
        is updated. Otherwise it is no op.
        """
        r = self.client.post('/bitbucket/', data=json.dumps(self.hg_payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) Build Started: bitbucket.org/pip/pip [latest]')

        self.hg_payload['commits'] = [{
            "branch": "not_ok",
        }]
        r = self.client.post('/bitbucket/', data=json.dumps(self.hg_payload),
                             content_type='application/json')
        self.assertEqual(
            r.content, '(URL Build) Not Building: bitbucket.org/pip/pip [not_ok]')

        self.hg_payload['commits'] = [{
            "branch": "unknown",
        }]
        r = self.client.post('/bitbucket/', data=json.dumps(self.hg_payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) No known branches were pushed to.')

    def test_bitbucket_default_branch(self):
        self.test_project = get(
            Project, repo='HTTPS://bitbucket.org/test/project', slug='test-project',
            default_branch='integration', repo_type='git',
        )

        self.git_payload['commits'] = [{
            "branch": "integration",
        }]
        self.git_payload['repository'] = {
            'absolute_url': '/test/project/'
        }

        r = self.client.post('/bitbucket/', data=json.dumps(self.git_payload),
                             content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.content, '(URL Build) Build Started: bitbucket.org/test/project [latest]')


