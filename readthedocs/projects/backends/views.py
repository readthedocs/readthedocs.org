'''
Project views loaded by configuration settings

Use these views instead of calling the views directly, in order to allow for
settings override of the view class.
'''

from django.utils.module_loading import import_by_path
from django.conf import settings


# Project Import Wizard
ImportWizardView = import_by_path(getattr(
    settings,
    'PROJECT_IMPORT_VIEW',
    'projects.views.private.ImportWizardView'
))
