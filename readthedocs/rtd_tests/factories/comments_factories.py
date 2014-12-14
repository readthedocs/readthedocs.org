from bamboo_boy.materials import Clump
import random

import factory

from comments.models import DocumentComment, DocumentNode, NodeSnapshot
from rtd_tests.factories.general_factories import UserFactory
from rtd_tests.factories.projects_factories import ProjectFactory


class SnapshotFactory(factory.DjangoModelFactory):
    FACTORY_FOR = NodeSnapshot
    hash = random.getrandbits(128)
    node = factory.SubFactory(
        'rtd_tests.test.comments_factories.DocumentNodeFactory')


class DocumentNodeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DocumentNode

    project = factory.SubFactory(ProjectFactory)
    version = factory.LazyAttribute(lambda a: a.project.versions.all()[0])
    page = "page-about-nothing"

    @classmethod
    def _create(self, *args, **kwargs):
        if not kwargs.get('hash'):
            kwargs['hash'] = random.getrandbits(128)
        if not kwargs.get('commit'):
            kwargs['commit'] = random.getrandbits(128)
        return super(DocumentNodeFactory, self)._create(*args, **kwargs)


class DocumentCommentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DocumentComment

    user = factory.SubFactory(UserFactory)
    text = "This is a comment."
    node = factory.SubFactory(DocumentNodeFactory)


class ProjectsWithComments(Clump):

    def build_canopy(self):
        self.moderated_project = self.include_factory(ProjectFactory,
                                                      1,
                                                      comment_moderation=True
                                                      )[0]
        self.moderated_node = self.include_factory(
            DocumentNodeFactory, 1, project=self.moderated_project)[0]

        self.first_moderated_comment, self.second_moderated_comment = self.include_factory(
            DocumentCommentFactory, 2, node=self.moderated_node)

        self.unmoderated_project = self.include_factory(ProjectFactory,
                                                        1,
                                                        comment_moderation=False
                                                        )[0]
        self.unmoderated_node = self.include_factory(
            DocumentNodeFactory, 1, project=self.unmoderated_project)[0]

        self.first_unmoderated_comment, self.second_unmoderated_comment = self.include_factory(
            DocumentCommentFactory, 2, node=self.unmoderated_node)

        self.owner = self.include_factory(
            UserFactory, 1, username="owner", password="test")[0]
        self.moderated_project.users.add(self.owner)
        self.unmoderated_project.users.add(self.owner)
