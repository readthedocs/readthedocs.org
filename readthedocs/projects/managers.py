from django.db import models


class HTMLFileManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(name__endswith=".html")


class AutomationRuleMatchManager(models.Manager):
    def register_match(self, rule, version, max_registers=15):
        created = self.create(
            rule=rule,
            match_arg=rule.get_version_match_pattern(),
            action=rule.action,
            version_name=version.verbose_name,
            version_type=version.type,
        )

        for match in self.filter(rule__project=rule.project)[max_registers:]:
            match.delete()
        return created
