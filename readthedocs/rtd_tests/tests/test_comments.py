from django.test import TestCase
from comments.views import add_node
from django.test.client import RequestFactory
from rtd_tests.tests.coments_factories import DocumentNodeFactory
from rest_framework.test import APIRequestFactory
from comments.models import DocumentNode


class CommentViewsTests(TestCase):

    def test_add_node_view(self):

        node = DocumentNodeFactory()

        # There's just one DocumentNode.
        self.assertEqual(DocumentNode.objects.count(), 1)

        request_factory = APIRequestFactory()

        post_data = {
                     'document': node.page,
                     'id': node.hash,
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