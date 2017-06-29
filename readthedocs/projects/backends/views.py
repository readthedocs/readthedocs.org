"""
Project views loaded by configuration settings

Use these views instead of calling the views directly, in order to allow for
settings override of the view class.
"""

from __future__ import absolute_import
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.projects.views import private


# Project Import Wizard
class ImportWizardView(SettingsOverrideObject):
    _default_class = private.ImportWizardView
    _override_setting = 'PROJECT_IMPORT_VIEW'


# Project demo import
class ImportDemoView(SettingsOverrideObject):
    _default_class = private.ImportDemoView
    _override_setting = 'PROJECT_IMPORT_DEMO_VIEW'
