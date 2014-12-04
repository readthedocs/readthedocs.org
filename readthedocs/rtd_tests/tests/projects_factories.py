import factory
from projects.models import Project
from builds.models import Version


class VersionFactory(factory.DjangoModelFactory):
    
    FACTORY_FOR = Version
    
    verbose_name = factory.Sequence(lambda n: "Project %s" % n)
    slug = factory.Sequence(lambda n: "project-%s" % n) 


class ProjectFactory(factory.DjangoModelFactory):

    FACTORY_FOR = Project

    name = factory.Sequence(lambda n: "Project %s" % n)
    slug = factory.Sequence(lambda n: "project-%s" % n) 
    
    version = factory.RelatedFactory(VersionFactory,
                                     'project',
                                     )