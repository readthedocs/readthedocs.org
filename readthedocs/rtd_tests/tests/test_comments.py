from django.test import TestCase
from comments.views import add_node, get_metadata, get_comments, add_comment
from django.test.client import RequestFactory
from rtd_tests.tests.coments_factories import DocumentNodeFactory, DocumentCommentFactory
from rest_framework.test import APIRequestFactory
from comments.models import DocumentNode
from rtd_tests.tests.general_factories import UserFactory
import random


class ModerationTests(TestCase):

    def test_approved_comments(self):
        comment = DocumentCommentFactory()

        # This comment has never been approved...
        self.assertFalse(comment.has_been_approved_since_most_recent_node_change())

        user = UserFactory()

        # ...until now!
        comment.moderate(user=user, approved=True)
        self.assertTrue(comment.has_been_approved_since_most_recent_node_change())

    def test_new_node_snapshot_causes_requed(self):

        comment = DocumentCommentFactory()
        user = UserFactory()
        comment.moderate(user=user, approved=True)

        self.assertTrue(comment.has_been_approved_since_most_recent_node_change())

        comment.node.snapshots.create(hash=random.getrandbits(128))

        self.assertFalse(comment.has_been_approved_since_most_recent_node_change())


class CommentViewsTests(TestCase):

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
