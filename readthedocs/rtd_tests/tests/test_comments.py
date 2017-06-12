from __future__ import absolute_import
import random
from unittest.case import expectedFailure

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory
from django_dynamic_fixture import fixture
from django_dynamic_fixture import get
from django_dynamic_fixture import new
from rest_framework.test import APIRequestFactory, APITestCase

from readthedocs.builds.models import Version
from readthedocs.comments.models import DocumentNode, DocumentComment
from readthedocs.comments.models import NodeSnapshot
from readthedocs.comments.views import add_node, get_metadata, update_node
from readthedocs.projects.models import Project
from readthedocs.projects.views.private import project_comments_moderation
from readthedocs.rtd_tests.utils import create_user


def create_node(hash=None, commit=None, **kwargs):
    snapshot_kwargs = {}
    if hash is not None:
        snapshot_kwargs['hash'] = hash
    if commit is not None:
        snapshot_kwargs['commit'] = commit
    node = get(DocumentNode, **kwargs)
    get(NodeSnapshot, node=node, **snapshot_kwargs)
    return node


class ModerationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = create_user(username='owner', password='test')

        cls.moderated_project = get(Project, comment_moderation=True)
        cls.moderated_project.users.add(cls.owner)

        cls.moderated_node = create_node(project=cls.moderated_project)

        cls.first_moderated_comment = get(DocumentComment,
                                          node=cls.moderated_node)
        cls.second_moderated_comment = get(DocumentComment,
                                           node=cls.moderated_node)

        cls.unmoderated_project = get(Project, comment_moderation=False)
        cls.unmoderated_project.users.add(cls.owner)

        cls.unmoderated_node = create_node(project=cls.unmoderated_project)

        cls.first_unmoderated_comment = get(DocumentComment,
                                            node=cls.unmoderated_node)
        cls.second_unmoderated_comment = get(DocumentComment,
                                             node=cls.unmoderated_node)

    def test_approved_comments(self):
        c = self.first_unmoderated_comment

        # This comment has never been approved...
        self.assertFalse(c.has_been_approved_since_most_recent_node_change())

        # ...until now!
        c.moderate(user=self.owner, decision=1)
        self.assertTrue(c.has_been_approved_since_most_recent_node_change())

    def test_new_node_snapshot_causes_comment_to_show_as_not_approved_since_change(self):

        c = self.first_unmoderated_comment
        c.moderate(user=self.owner, decision=1)

        self.assertTrue(c.has_been_approved_since_most_recent_node_change())
        c.node.snapshots.create(hash=random.getrandbits(128))
        self.assertFalse(c.has_been_approved_since_most_recent_node_change())

    def test_unmoderated_project_shows_all_comments(self):

        visible_comments = self.unmoderated_node.visible_comments()

        self.assertIn(self.first_unmoderated_comment, visible_comments)
        self.assertIn(self.second_unmoderated_comment, visible_comments)

    def test_unapproved_comment_is_not_visible_on_moderated_project(self):

        # We take a look at the visible comments and find that neither comment
        # is among them.
        visible_comments = self.moderated_node.visible_comments()
        self.assertNotIn(self.first_moderated_comment, visible_comments)
        self.assertNotIn(self.second_moderated_comment, visible_comments)

    def test_moderated_project_with_unchanged_nodes_shows_only_approved_comment(self):
        # Approve the first comment...
        self.first_moderated_comment.moderate(user=self.owner, decision=1)

        # ...and find that the first comment, but not the second one, is visible.
        visible_comments = self.moderated_node.visible_comments()
        self.assertIn(self.first_moderated_comment, visible_comments)
        self.assertNotIn(self.second_moderated_comment, visible_comments)

    def test_moderated_project_with_changed_nodes_dont_show_comments_that_havent_been_approved_since(self):
        # Approve the first comment...
        self.first_moderated_comment.moderate(user=self.owner, decision=1)

        # ...but this time, change the node.
        self.first_moderated_comment.node.snapshots.create(hash=random.getrandbits(128))

        # Now it does not show as visible.
        visible_comments = self.moderated_node.visible_comments()
        self.assertNotIn(self.first_moderated_comment, visible_comments)

    def test_unapproved_comments_appear_in_moderation_queue(self):
        queue = self.moderated_project.moderation_queue()
        self.assertIn(self.first_moderated_comment, queue)
        self.assertIn(self.second_moderated_comment, queue)

    def test_approved_comments_do_not_appear_in_moderation_queue(self):
        self.first_moderated_comment.moderate(user=self.owner, decision=1)
        queue = self.moderated_project.moderation_queue()
        self.assertNotIn(self.first_moderated_comment, queue)
        self.assertIn(self.second_moderated_comment, queue)


class NodeAndSnapshotTests(TestCase):

    def test_update_with_same_hash_does_not_create_new_snapshot(self):
        node = get(DocumentNode)
        get(NodeSnapshot, node=node)

        hash = "SOMEHASH"
        commit = "SOMEGITCOMMIT"

        # We initially have just one snapshot.
        self.assertEqual(node.snapshots.count(), 1)

        # ...but when we update the hash, we have two.
        node.update_hash(hash, commit)
        self.assertEqual(node.snapshots.count(), 2)

        # If we update with the same exact hash and commit, it doesn't create a new snapshot.
        node.update_hash(hash, commit)
        self.assertEqual(node.snapshots.count(), 2)

    def test_node_cannot_be_created_without_commit_and_hash(self):
        project = get(Project, versions=[fixture()])
        some_version = project.versions.all()[0]

        self.assertRaises(TypeError,
                          DocumentNode.objects.create,
                          project=project,
                          version=some_version,
                          hash=random.getrandbits(128)
                          )

        self.assertRaises(TypeError,
                          DocumentNode.objects.create,
                          project=project,
                          version=some_version,
                          commit=random.getrandbits(128)
                          )

    def test_node_can_be_sought_From_new_hash(self):

        first_hash = "THEoriginalHASH"
        second_hash = 'ANEWCRAZYHASH'

        node = create_node(hash=first_hash)
        get(DocumentComment)
        node.update_hash(second_hash, 'ANEWCRAZYCOMMIT')

        node_from_orm = DocumentNode.objects.from_hash(node.version.slug,
                                                       node.page,
                                                       node.latest_hash(),
                                                       project_slug=node.project.slug)
        self.assertEqual(node, node_from_orm)

        node.update_hash(first_hash, 'AthirdCommit')

        node_from_orm2 = DocumentNode.objects.from_hash(node.version.slug, node.page, first_hash, node.project.slug)
        self.assertEqual(node, node_from_orm2)

    @expectedFailure
    def test_nodes_with_same_hash_oddness(self):

        node_hash = "AcommonHASH"
        page = "somepage"
        commit = "somecommit"
        project = get(Project, versions=[fixture()])

        project.add_node(node_hash=node_hash,
                         page=page,
                         version=project.versions.all()[0].slug,
                         commit=commit,
                         )

        # A new commit with a second instance of the exact same content.
        project.add_node(node_hash=node_hash,
                         page=page,
                         version=project.versions.all()[0].slug,
                         commit="ANEWCOMMIT",
                         )
        try:
            project.nodes.from_hash(project.versions.all()[0].slug, page, node_hash, project.slug)
        except NotImplementedError:
            self.fail("We don't have indexing yet.")


class CommentModerationViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = create_user(username='owner', password='test')

        cls.moderated_project = get(Project, comment_moderation=True)
        cls.moderated_project.users.add(cls.owner)

        cls.moderated_node = get(DocumentNode,
                                 project=cls.moderated_project)
        get(NodeSnapshot, node=cls.moderated_node)

        cls.moderated_comment = get(DocumentComment,
                                    text='Some comment text.',
                                    node=cls.moderated_node)

    def test_unmoderated_comments_are_listed_in_view(self):

        request = RequestFactory()
        request.user = self.owner
        request.META = {}
        response = project_comments_moderation(request, self.moderated_project.slug)

        self.assertContains(response, self.moderated_comment.text)


class CommentAPIViewsTests(APITestCase):

    request_factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        cls.owner = create_user(username='owner', password='test')

        cls.moderated_project = get(Project, comment_moderation=True)
        cls.moderated_project.users.add(cls.owner)
        cls.moderated_version = get(Version, project=cls.moderated_project)

        cls.moderated_node = get(DocumentNode,
                                 project=cls.moderated_project,
                                 version=cls.moderated_version)
        get(NodeSnapshot, node=cls.moderated_node)

    def test_get_comments_view(self):

        number_of_comments = DocumentComment.objects.count()

        response = self.client.get('/api/v2/comments/')
        self.assertEqual(number_of_comments, response.data['count'])

        # moooore comments.
        get(DocumentComment, n=50, node=self.moderated_node)

        response = self.client.get('/api/v2/comments/')
        self.assertEqual(number_of_comments + 50, response.data['count'])

    def test_get_metadata_view(self):

        node = create_node()

        get_data = {
            'project': node.project.slug,
            'version': node.version.slug,
            'page': node.page
        }
        request = self.request_factory.get('/_get_metadata/', get_data)
        response = get_metadata(request)
        response.render()

        number_of_comments = response.data[node.latest_hash()]

        # There haven't been any comments yet.
        self.assertEqual(number_of_comments, 0)

        # Now we'll make one.
        get(DocumentComment, node=node, text="Our first comment!")

        second_request = self.request_factory.get('/_get_metadata/', get_data)
        second_response = get_metadata(second_request)
        second_response.render()

        number_of_comments = second_response.data[node.latest_hash()]

        # And sure enough - one comment.
        self.assertEqual(number_of_comments, 1)

    def test_add_node_view(self):

        node = self.moderated_project.nodes.all()[0]

        post_data = {
            'document': node.page,
            'id': node.latest_hash(),
            'project': node.project.slug,
            'version': node.version.slug,
            'commit': node.latest_commit(),
        }

        # Now let's delete the node....
        DocumentNode.objects.all().delete()

        # ...we have no nodes.
        self.assertEqual(DocumentNode.objects.count(), 0)

        # Hit the API again.
        request = self.request_factory.post('/_add_node/', post_data)
        response = add_node(request)

        # We do now have exactly one Node.
        self.assertEqual(DocumentNode.objects.count(), 1)

    def test_update_node_view(self):

        node = create_node()

        # Our node has one snapshot.
        self.assertEqual(node.snapshots.count(), 1)

        new_hash = "CRAZYnewHASHtoUPDATEnode"
        commit = "COOLNEWGITCOMMITHASH"

        post_data = {
            'old_hash': node.latest_hash(),
            'new_hash': new_hash,
            'commit': commit,
            'project': node.project.slug,
            'version': node.version.slug,
            'page': node.page
        }

        request = self.request_factory.post('/_update_node/', post_data)
        response = update_node(request)
        response.render()

        self.assertEqual(response.data['current_hash'], new_hash)

        # We now have two snapshots.
        self.assertEqual(node.snapshots.count(), 2)
        # And the latest hash is the one we just set.
        self.assertEqual(node.latest_hash(), new_hash)

    def test_add_comment_view_without_existing_hash(self):

        comment_text = "Here's a comment added to a new hash."
        version = get(Version, project=fixture())
        node = create_node(project=version.project, version=version)
        user = create_user(username='test', password='test')

        number_of_nodes = DocumentNode.objects.count()

        post_data = {
            'node': random.getrandbits(128),
            'commit': random.getrandbits(128),
            'project': node.project.slug,
            'version': node.version.slug,
            'document_page': node.page,
            'text': comment_text
        }

        self.client.login(username="test", password="test")

        response = self.client.post('/api/v2/comments/', post_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['text'], comment_text)
        self.assertEqual(DocumentNode.objects.count(), number_of_nodes + 1)  # We created a new node.

    def test_add_comment_view_with_existing_hash(self):

        node = create_node()
        user = create_user(username='test', password='test')

        comment_text = "Here's a comment added through the comment view."

        post_data = {
            'node': node.latest_hash(),
            'commit': node.latest_hash(),
            'project': node.project.slug,
            'version': node.version.slug,
            'document_page': node.page,
            'text': comment_text
        }

        self.client.login(username="test", password="test")
        response = self.client.post('/api/v2/comments/', post_data)

        comment_from_orm = node.comments.filter(text=comment_text)
        self.assertTrue(comment_from_orm.exists())

        self.assertEqual(comment_from_orm[0].node, node,
                         "The comment exists, but lives in a different node!  Not supposed to happen.")

    def test_add_comment_view_with_changed_hash(self):

        first_hash = "THEoriginalHASH"
        second_hash = 'ANEWCRAZYHASH'

        comment_text = "This comment will follow its node despite hash changing."

        # Create a comment on a node whose latest hash is the first one.
        node = create_node(hash=first_hash)
        get(DocumentComment, node=node, text=comment_text)

        # Now change the node's hash.
        node.update_hash(second_hash, 'ANEWCRAZYCOMMIT')

        node_from_orm = DocumentNode.objects.from_hash(version_slug=node.version.slug,
                                                       page=node.page,
                                                       node_hash=node.latest_hash(),
                                                       project_slug=node.project.slug)

        # It's the same node.
        self.assertEqual(node, node_from_orm)

        # Get all the comments with the second hash.
        query_params = {'node': second_hash,
                        'document_page': node.page,
                        'project': node.project.slug,
                        'version': node.version.slug,
                        }

        response = self.client.get('/api/v2/comments/', query_params)

        self.assertEqual(response.data['results'][0]['text'], comment_text)

    def test_moderate_comment_by_approving(self):
        user = create_user(username='test', password='test')

        project = get(Project, versions=[fixture()])
        project.users.add(user)
        node = create_node(project=project)

        comment = get(DocumentComment, node=node)

        post_data = {
            'decision': 1,
        }

        self.assertFalse(comment.has_been_approved_since_most_recent_node_change())

        self.client.login(username="test", password="test")
        response = self.client.put('/api/v2/comments/%s/moderate/' % comment.id, post_data)
        self.assertEqual(response.data['decision'], 1)
        self.assertTrue(comment.has_been_approved_since_most_recent_node_change())

    def test_stranger_cannot_moderate_comments(self):

        node = create_node()
        comment = get(DocumentComment, node=node)

        post_data = {
            'decision': 1,
        }

        response = self.client.put('/api/v2/comments/%s/moderate/' % comment.id,
                                   post_data
                                   )

        self.assertEqual(response.status_code, 403)

    test_retrieve_comment_on_old_hash = test_post_comment_on_old_hash = None
