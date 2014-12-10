from django.test import TestCase
from comments.views import add_node, get_metadata
from django.test.client import RequestFactory
from rtd_tests.tests.coments_factories import DocumentNodeFactory, DocumentCommentFactory
from rest_framework.test import APIRequestFactory
from comments.models import DocumentNode
from rtd_tests.tests.general_factories import UserFactory


class ModerationTests(TestCase):

    def test_approved_comments(self):
        comment = DocumentCommentFactory()
        
        # This comment has never been approved...
        self.assertFalse(comment.has_been_approved_since_most_recent_node_change())

        user = UserFactory()
        
        # ...until now!
        comment.moderate(user=user, approved=True)
        self.assertTrue(comment.has_been_approved_since_most_recent_node_change())


    def test_anchor_change_causes_reque(self):

#         node = comment.node
#         latest_snapshot = node.snapshots.latest()
#         hash = latest_snapshot.hash

        self.fail()


class CommentViewsTests(TestCase):

    def test_get_metadata(self):

        node = DocumentNodeFactory()

        request_factory = APIRequestFactory()
        get_data = {
                    'project': node.project.slug,
                    'version': node.version.slug,
                    'page': node.page
                    }
        request = request_factory.get('/_get_metadata/', get_data)
        response = get_metadata(request)
        response.render()

        number_of_comments = response.data[node.latest_hash()]

        # There haven't been any comments yet.
        self.assertEqual(number_of_comments, 0)

        # Now we'll make one.
        comment = DocumentCommentFactory(node=node, text="Our first comment!")

        second_request = request_factory.get('/_get_metadata/', get_data)
        second_response = get_metadata(request)
        second_response.render()

        number_of_comments = second_response.data[node.latest_hash()]

        # And sure enough - one comment.
        self.assertEqual(number_of_comments, 1)


    def test_add_node_view(self):

        node = DocumentNodeFactory()

        # There's just one DocumentNode.
        self.assertEqual(DocumentNode.objects.count(), 1)

        request_factory = APIRequestFactory()

        post_data = {
                     'document': node.page,
                     'id': node.latest_hash(),
                     'project': node.project.slug,
                     'version': node.version.slug,
                     }

        request = request_factory.post('/_add_node/', post_data)
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
        second_request = request_factory.post('/_add_node/', post_data)
        second_response = add_node(request)
        second_response.render()

        # ...and this time, we *will* have created a new node.
        self.assertTrue(second_response.data['created'])

        # We do now have exactly one Node.
        self.assertEqual(DocumentNode.objects.count(), 1)