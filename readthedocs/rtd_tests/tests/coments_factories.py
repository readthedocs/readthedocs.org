import factory
from comments.models import DocumentComment, DocumentNode, NodeSnapshot
from rtd_tests.tests.general_factories import UserFactory
from rtd_tests.tests.projects_factories import ProjectFactory, VersionFactory
import random


class SnapshotFactory(factory.DjangoModelFactory):
    FACTORY_FOR = NodeSnapshot
    hash = random.getrandbits(128)
    node = factory.SubFactory('rtd_tests.test.comments_factories.DocumentNodeFactory')


class DocumentNodeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DocumentNode

    project = factory.SubFactory(ProjectFactory)
    version = factory.LazyAttribute(lambda a: a.project.versions.all()[0])
    page = "page-about-nothing"

    @classmethod
    def _create(self, *args, **kwargs):
        if not kwargs.get('hash'):
            kwargs['hash'] = random.getrandbits(128)
        return super(DocumentNodeFactory, self)._create(*args, **kwargs)


class DocumentCommentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DocumentComment

    user = factory.SubFactory(UserFactory)
    text = "This is a comment."
    node = factory.SubFactory(DocumentNodeFactory)
