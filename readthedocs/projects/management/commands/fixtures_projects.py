from django.core.management.base import BaseCommand
from django.forms.models import model_to_dict

from readthedocs.projects.models import Project


class Command(BaseCommand):
	
	help = __doc__
	dry_run = False

	def make_data(self):
		self.test_data_list = []
		p = Project.objects.create(
					name="TestFixture1234", 
					slug="testfixture1234", 
					repo="https://github.com/test", 
					repo_type="git"
		)
		p.save()
		test_data_list.append(model_to_dict(p))

	def handle(self):
		make_data()
		print("Created data")
