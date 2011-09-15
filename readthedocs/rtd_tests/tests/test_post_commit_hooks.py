from django.test import TestCase
import json

class PostCommitTest(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
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
                    "url": "https://github.com/wraithan/readthedocs.org/commit/11f229c6a78f5bc8cb173104a3f7a68cdb7eb15a"}
                ,
                ],
            "compare": "https://github.com/wraithan/readthedocs.org/compare/5b4e453...5ad7573",
            "created": False,
            "deleted": False,
            "forced": False,
            "pusher": {
                "name": "none"
                },
            "ref": "refs/heads/master",
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
                "watchers": 1
                }
            }


    def test_github_post_commit_hook_knows_the_repo_url(self):
        """
        Test the github post commit hook so only the main repo (or at
        least the one specified in the project) is the only one that
        triggers builds.
        """
        r = self.client.post('/github/', {'payload': json.dumps(self.payload)})
        self.assertEqual(r.status_code, 200)
        self.payload['repository']['url'] = "https://github.com/wraithan/readthedocs.org"
        r = self.client.post('/github/', {'payload': json.dumps(self.payload)})
        self.assertEqual(r.status_code, 404)

    def test_github_post_commit_hook_builds_branch_docs_if_it_should(self):
        """
        Test the github post commit hook to see if it will only build
        versions that are set to be built if the branch they refer to
        is updated. Otherwise it is no op.
        """
        r = self.client.post('/github/', {'payload': json.dumps(self.payload)})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'Build Started: master')
        self.payload['ref'] = 'refs/heads/not_ok'
        r = self.client.post('/github/', {'payload': json.dumps(self.payload)})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.content, 'Not Building: not_ok')
        self.payload['ref'] = 'refs/heads/unknown'
        r = self.client.post('/github/', {'payload': json.dumps(self.payload)})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'Build Started: latest')
