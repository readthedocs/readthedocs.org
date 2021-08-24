from allauth.socialaccount.providers.github.provider import GitHubProvider


class RTDGitHubProvider(GitHubProvider):

    supports_permissions_upgrade = True

    def get_extra_permissions_url(self, **kwargs):
        settings = self.get_settings()
        original_scopes = settings.get('SCOPE', [])
        new_scopes = ' '.join(original_scopes + self.get_extra_scopes())
        url = self.get_login_url(
            request=None,
            auth_params=f'scope={new_scopes}',
            **kwargs,
        )
        return url

    def get_extra_scopes(self):
        settings = self.get_settings()
        return settings.get('ADDITIONAL_SCOPE', [])

    @classmethod
    def get_oauth_service(cls, account):
        from readthedocs.oauth.services import GitHubService
        return GitHubService(account.user, account)


provider_classes = [RTDGitHubProvider]
