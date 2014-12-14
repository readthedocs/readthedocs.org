import factory
from projects.models import Project
from builds.models import Version
from bamboo_boy.materials import Clump


class VersionFactory(factory.DjangoModelFactory):

    FACTORY_FOR = Version

    verbose_name = factory.Sequence(lambda n: "Project %s" % n)
    slug = factory.Sequence(lambda n: "project-%s" % n)


class ProjectFactory(factory.DjangoModelFactory):

    FACTORY_FOR = Project

    name = factory.Sequence(lambda n: "Project %s" % n)
    slug = factory.Sequence(lambda n: "project-%s" % n)
    documentation_type = "sphinx"
    conf_py_file = "test_conf.py"

    version = factory.RelatedFactory(VersionFactory,
                                     'project',
                                     )


class OneProjectWithTranslationsOneWithout(Clump):

    def build_canopy(self):
        self.project_with_translations = self.include_factory(
            ProjectFactory, 1)[0]
        self.first_translation = ProjectFactory(
            main_language_project=self.project_with_translations)
        pass
