from bamboo_boy.utils import with_canopy
import random

from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework.test import APIRequestFactory

from comments.models import DocumentNode
from comments.views import add_node, get_metadata, get_comments, add_comment, update_node
from privacy.backend import AdminNotAuthorized
from rtd_tests.tests.coments_factories import DocumentNodeFactory, \
                DocumentCommentFactory, ProjectsWithComments
from rtd_tests.tests.general_factories import UserFactory
from rtd_tests.tests.projects_factories import ProjectFactory
from projects.views.private import project_comments_moderation


@with_canopy(ProjectsWithComments)
class ModerationTests(TestCase):

    def test_approved_comments(self):
        c = self.canopy.first_unmoderated_comment

        # This comment has never been approved...
        self.assertFalse(c.has_been_approved_since_most_recent_node_change())

        # ...until now!
        c.moderate(user=self.canopy.owner, approved=True)
        self.assertTrue(c.has_been_approved_since_most_recent_node_change())

    def test_new_node_snapshot_causes_comment_to_show_as_not_approved_since_change(self):

        c = self.canopy.first_unmoderated_comment
        c.moderate(user=self.canopy.owner, approved=True)

        self.assertTrue(c.has_been_approved_since_most_recent_node_change())
        c.node.snapshots.create(hash=random.getrandbits(128))
        self.assertFalse(c.has_been_approved_since_most_recent_node_change())

    def test_unmoderated_project_shows_all_comments(self):

        visible_comments = self.canopy.unmoderated_node.visible_comments()

        self.assertIn(self.canopy.first_unmoderated_comment, visible_comments)
        self.assertIn(self.canopy.second_unmoderated_comment, visible_comments)

    def test_moderated_project_does_not_show_unapproved_comment(self):

        # We take a look at the visible comments and find that neither comment is among them.
        visible_comments = self.canopy.moderated_node.visible_comments()
        self.assertNotIn(self.canopy.first_moderated_comment, visible_comments)
        self.assertNotIn(self.canopy.second_moderated_comment, visible_comments)

    def test_moderated_project_with_unchanged_nodes_shows_only_approved_comment(self):
        # Approve the first comment...
        self.canopy.first_moderated_comment.moderate(user=self.canopy.owner, approved=True)

        # ...and find that the first comment, but not the second one, is visible.
        visible_comments = self.canopy.moderated_node.visible_comments()
        self.assertIn(self.canopy.first_moderated_comment, visible_comments)
        self.assertNotIn(self.canopy.second_moderated_comment, visible_comments)

    def test_moderated_project_with_changed_nodes_dont_show_comments_that_havent_been_approved_since(self):
        # Approve the first comment...
        self.canopy.first_moderated_comment.moderate(user=self.canopy.owner, approved=True)

        # ...but this time, change the node.
        self.canopy.first_moderated_comment.node.snapshots.create(hash=random.getrandbits(128))

        # Now it does not show as visible.
        visible_comments = self.canopy.moderated_node.visible_comments()
        self.assertNotIn(self.canopy.first_moderated_comment, visible_comments)

    def test_stranger_is_not_allowed_to_moderate(self):
        stranger = UserFactory()

        self.assertRaises(
            AdminNotAuthorized,
            self.canopy.first_moderated_comment.moderate,
            user=stranger,
            approved=True)


@with_canopy(ProjectsWithComments)
class CommentModerationViewsTests(TestCase):

    def test_unmoderated_comments_are_listed_in_view(self):

        request = RequestFactory()
        request.user = self.canopy.owner
        request.META = {}
        response = project_comments_moderation(request, self.canopy.moderated_project.slug)

        self.assertIn(self.canopy.first_moderated_comment.text, response.content)

class CommentAPIViewsTests(TestCase):

    request_factory = APIRequestFactory()

    def test_get_comments_view(self):
        node = DocumentNodeFactory()
        request = self.request_factory.get('/_get_comments', {'node': node.latest_hash()})
        response = get_comments(request)
        response.render()

        comments = response.data['comments']

        # Since there are no comments, we expect and empty list.
        self.assertEqual(comments, [])

        comment_text = "Now our node has a comment!"
        comment = DocumentCommentFactory(node=node, text=comment_text)

        second_request = self.request_factory.get('/_get_comments', {'node': node.latest_hash()})
        second_response = get_comments(request)
        second_response.render()

        comment_as_retrived_from_api = second_response.data['comments'][0]['text']

        self.assertEqual(comment_text, comment_as_retrived_from_api)

    def test_get_metadata_view(self):

        node = DocumentNodeFactory()

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
        comment = DocumentCommentFactory(node=node, text="Our first comment!")

        second_request = self.request_factory.get('/_get_metadata/', get_data)
        second_response = get_metadata(request)
        second_response.render()

        number_of_comments = second_response.data[node.latest_hash()]

        # And sure enough - one comment.
        self.assertEqual(number_of_comments, 1)


    def test_add_node_view(self):

        node = DocumentNodeFactory()

        # There's just one DocumentNode.
        self.assertEqual(DocumentNode.objects.count(), 1)

        post_data = {
                     'document': node.page,
                     'id': node.latest_hash(),
                     'project': node.project.slug,
                     'version': node.version.slug,
                     }

        request = self.request_factory.post('/_add_node/', post_data)
        response = add_node(request)

        # Everything went, you know, OK.
        self.assertEqual(response.status_code, 200)

        response.render()

        # We won't have created a new DocumentNode, since this one already existed.
        self.assertFalse(response.data['created'])

        # Now let's delete the node....
        node.delete()

        # ...we have no nodes.
        self.assertEqual(DocumentNode.objects.count(), 0)

        # Hit the API again.
        second_request = self.request_factory.post('/_add_node/', post_data)
        second_response = add_node(request)
        second_response.render()

        # ...and this time, we *will* have created a new node.
        self.assertTrue(second_response.data['created'])

        # We do now have exactly one Node.
        self.assertEqual(DocumentNode.objects.count(), 1)

    def test_update_node_view(self):

        node = DocumentNodeFactory()

        # Our node has one snapshot.
        self.assertEqual(node.snapshots.count(), 1)

        new_hash = "CRAZYnewHASHtoUPDATEnode"
        commit = "COOLNEWGITCOMMITHASH"

        post_data = {
            'new_hash': new_hash,
            'commit': commit
        }

        request = self.request_factory.post('/_update_node/', post_data)
        response = update_node(request, node.id)
        response.render()

        self.assertEqual(response.data['current_hash'], new_hash)

        # We now have two snapshots.
        self.assertEqual(node.snapshots.count(), 2)
        # And the latest hash is the one we just set.
        self.assertEqual(node.latest_hash(), new_hash)

    def test_add_comment_view_without_existing_hash(self):

        comment_text = "Here's a comment added to a new hash."
        node = DocumentNodeFactory()
        user = UserFactory()

        post_data = {
            'node': random.getrandbits(128),
            'project': node.project.slug,
            'version': node.version.slug,
            'page': node.page,
            'text': comment_text
        }

        request = self.request_factory.post('/_add_comment', post_data)
        request.user = user
        response = add_comment(request)
        response.render()

        self.assertTrue(response.data['created'])  # We created a new node.

    def test_add_comment_view_with_existing_hash(self):

        node = DocumentNodeFactory()
        user = UserFactory()

        comment_text = "Here's a comment added through the comment view."

        post_data = {
            'node': node.latest_hash(),
            'project': node.project.slug,
            'version': node.version.slug,
            'page': node.page,
            'text': comment_text
        }

        request = self.request_factory.post('/_add_comment', post_data)
        request.user = user
        response = add_comment(request)
        response.render()

        self.assertFalse(response.data['created'])  # We didn't create a node.
