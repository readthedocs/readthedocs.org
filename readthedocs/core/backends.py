# -*- coding: utf-8 -*-

"""Email backends for core app."""

import smtplib

from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.utils import DNS_NAME


class SSLEmailBackend(EmailBackend):

    def open(self):
        if self.connection:
            return False
        try:
            self.connection = smtplib.SMTP_SSL(
                self.host,
                self.port,
                local_hostname=DNS_NAME.get_fqdn(),
            )
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception:
            if not self.fail_silently:
                raise
