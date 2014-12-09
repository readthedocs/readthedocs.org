import factory
from comments.models import DocumentComment, DocumentNode
from rtd_tests.tests.general_factories import UserFactory
from rtd_tests.tests.projects_factories import ProjectFactory, VersionFactory
import random


class DocumentNodeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DocumentNode

    project = factory.SubFactory(ProjectFactory)
    version = factory.LazyAttribute(lambda a: a.project.versions.all()[0])
    page = "A page about nothing."
    hash = random.getrandbits(128)


class DocumentCommentFactory(factory.Factory):
    FACTORY_FOR = DocumentComment

    user = factory.SubFactory(UserFactory)
    text = "This is a comment."
    displayed = True
    node = factory.SubFactory(DocumentNodeFactory)