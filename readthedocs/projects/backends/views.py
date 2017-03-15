"""
Project views loaded by configuration settings

Use these views instead of calling the views directly, in order to allow for
settings override of the view class.
"""

from django.utils.module_loading import import_string
from django.conf import settings


# Project Import Wizard
ImportWizardView = import_string(getattr(
    settings,
    'PROJECT_IMPORT_VIEW',
    'readthedocs.projects.views.private.ImportWizardView'
))

# Project demo import
ImportDemoView = import_string(getattr(
    settings,
    'PROJECT_IMPORT_DEMO_VIEW',
    'readthedocs.projects.views.private.ImportDemoView'
))
