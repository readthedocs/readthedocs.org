"""
Custom database routers.

https://docs.djangoproject.com/en/4.0/topics/db/multi-db/#automatic-database-routing
"""

from collections import defaultdict


class MapAppsRouter:
    """
    Router to map Django applications to a specific database.

    :py:attr:`apps_to_db` is used to map an application to a database,
    if an application isn't listed here, it will use the ``default`` database.
    """

    def __init__(self):
        self.apps_to_db = defaultdict(lambda: "default")
        self.apps_to_db.update({"telemetry": "telemetry"})

    def db_for_read(self, model, **hints):
        return self.apps_to_db[model._meta.app_label]

    def db_for_write(self, model, **hints):
        return self.apps_to_db[model._meta.app_label]

    def allow_relation(self, obj1, obj2, **hints):
        return self.apps_to_db[obj1._meta.app_label] == self.apps_to_db[obj2._meta.app_label]

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return self.apps_to_db[app_label] == db
