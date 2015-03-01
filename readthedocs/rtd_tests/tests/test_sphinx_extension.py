from django.test import TestCase

import mock
from docutils import nodes, utils

from readthedocs_ext.comments import backend, hasher, translator


def _pass(*args, **kwargs):
    pass


class TestBuildCommand(TestCase):

    '''Test Sphinx Extension'''

    def setUp(self):
        self.nodes = {
            u'nil-0-0104c4104242a022004402100860ac01886600192002010200e0800041804000': 0,
            u'nil-0-0c0036514c0704960c021c0801b22c0cd97084058d046202049a0610022280cb': 0,
            u'nil-0-2010040804000000000040280000110000008008000001000300002000000803': 0,
            u'nil-0-5c1174a210a346001c001c409012c8599480cf838820241e35a68204f2322044': 0,
            u'nil-0-79d9400e4498e821fb9809940ab40289421205b1884e05276106133103344e5c': 0,
            u'nil-0-800908000220c1200000600054000000050a000041200b000402080080180090': 0,
            u'nil-0-900b18c50008852280206411d1011000808200800a00021000000a00805800d0': 0,
            u'nil-0-9941022808db2114a634119008802aeb0880552941001288680992c491e89048': 0,
            u'nil-1-0bb0b5cd7c7db9c7d7525a29b7ba7fb5665fb33dc9f0d3aeb6c56c87e4b0806a': 0,
            u'nil-1-1d49dc400a5003ea92933e38900323a30c3a8575490062852e454a8ceaa01d4b': 0,
            u'nil-1-3d40b4f90e3469e7f7631eb97c98039e949b85bd212042deaee57c8ce6f8c1eb': 0,
            u'nil-1-59b11c0507119d2eafb139b9d584b3942d2301291b002e56a9c98b056632a58e': 0,
            u'nil-1-79a01ec88670996d827a1fa9f1b32b231495c1e3591276942e1d4ab7b8a9a96b': 0,
            u'nil-1-7bc13409aebab9c6726254a6ef3d2bfe6e109fcd4d4a76c46f4987f5fca8af5b': 0,
            u'nil-1-9bb031c90e79e9efc7413ad089c06ac74e13037541307fb6b6456cc0a4908ab9': 0,
            u'nil-1-ebb0bd9c16999376e63196b92d866f33d0e601f1c9a56df62749c224d02020cb': 0,
            u'nil-2-189e720149348920079255801791819b283068300900205622280325540f0242': 0,
            u'nil-2-1c9ea20321378c2032d294931791991a2a32488021426152a6880619c80f884a': 0,
            u'nil-2-4d2233490234a9248386df8a2403a5a24d0ad029d8442e67370563897878f067': 0,
            u'nil-2-7fd4d3dc1e3788e553d3b9ccf09b25b46d5ee839a3a0ee242d492484e012ee2e': 0,
            u'nil-2-b9bfcb95ad36b243f61374aabfd69f7ae9df6a62b920f71f2b194f077e9f2c7b': 0,
            u'nil-2-c550342a220e19eccd16390873ac0036277b2941dd7c2a2675470a94e238c5b9': 0,
            u'nil-3-199815ed0730814caf635db8a6c4e3d36821c9f5d96b6bd0a34b2a31e8f029af': 0,
            u'nil-3-1dd20999a6d597650e609bf446c20ddfccf9897429b074c43647680fc2f6ab3f': 0,
            u'nil-3-91e0a9090250012de2fb52aa723253d69e9ab397491c4e6e3247c45ee0f42885': 0
        }
        self.test_string = 'This allows comments on certain pages to wither slower than the default for the project.'
        self.test_node = nodes.Text(self.test_string)

        self.builder = mock.MagicMock()
        self.builder.current_docname = 'foobar'
        self.builder.storage = mock.Mock()
        self.builder.storage.get_metadata = mock.MagicMock(return_value=self.nodes)
        with mock.patch('readthedocs_ext.comments.translator.UUIDTranslator.__init__', _pass):
            self.trans = translator.UUIDTranslator()

    def _compare_string_to_list(self, input, hash_list):
        mod_node = nodes.Text(input)
        hash_obj = hasher.hash_node(mod_node, obj=True)
        match = hasher.compare_hash(hash_obj, hash_list)
        return match

    def test_hash_command(self):
        '''Test hash resolution for content'''
        hash_obj = hasher.hash_node(self.test_node, obj=True)
        match = hasher.compare_hash(hash_obj, self.nodes.keys())
        self.assertEqual(match, 'nil-3-199815ed0730814caf635db8a6c4e3d36821c9f5d96b6bd0a34b2a31e8f029af')
        for dec in range(1, 20):
            modified_string = self.test_string[dec:]
            print "Mod string " + modified_string
            match = self._compare_string_to_list(modified_string, self.nodes.keys())
            self.assertEqual(match, 'nil-3-199815ed0730814caf635db8a6c4e3d36821c9f5d96b6bd0a34b2a31e8f029af')

    """
    def test_get_metadata(self):
        # Default
        self.trans.update_hash(self.test_node, self.builder)
        self.builder.storage.get_metadata.assert_called_with('foobar')

        # New file
        self.builder.current_docname = 'sweet-doc'
        self.trans.update_hash(self.test_node, self.builder)
        self.builder.storage.get_metadata.assert_called_with('sweet-doc')

    def test_update_node(self):
        self.trans.update_hash(self.test_node, self.builder)
        self.builder.storage.update_node.assert_called_with(
            commit='foobar',
            old_hash=u'nil-3-199815ed0730814caf635db8a6c4e3d36821c9f5d96b6bd0a34b2a31e8f029af',
            new_hash='nil-199815ed0730814caf635db8a6c4e3d36821c9f5d96b6bd0a34b2a31e8f029af'
        )

    def test_add_node(self):
        new_string = 'This string doesnt exist in the hashes'
        new_node = nodes.Text(new_string)
        self.trans.update_hash(new_node, self.builder)
        self.builder.storage.add_node.assert_called_with(
            source='This string doesnt exist in the hashes',
            document='foobar',
            id='nil-52902498441ac8b4280001045028818022aa48a04040c8118e4cac8440d1800a'
        )
    """


"""
class TestBuildIntegration(TestCase):

    '''Test Sphinx Integration'''

    def setUp(self):

        self.test_string = 'A new node for kong.'
        self.test_node = nodes.Text(self.test_string)

        with mock.patch('readthedocs_ext.comments.translator.UUIDTranslator.__init__', _pass):
            self.builder = mock.MagicMock()
            self.builder.project = 'kong'
            self.builder.version = 'latest'
            self.builder.current_docname = 'index'
            self.builder.config.websupport2_base_url = 'http://localhost:8000/websupport/'
            self.builder.storage = backend.WebStorage(builder=self.builder)
            self.trans = translator.UUIDTranslator()

    def test_update_node(self):
        resp = self.trans.update_hash(self.test_node, self.builder)
        self.assertTrue(resp.status_code == 200)
        #self.assertTrue(resp.json()['created'])

"""