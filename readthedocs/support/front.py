"""Front's API client."""

import requests


class FrontClient:

    """Wrapper around Front's API."""

    BASE_URL = 'https://api2.frontapp.com'

    def __init__(self, token):
        self.token = token

    @property
    def _headers(self):
        headers = {
            "Authorization": f"Bearer {self.token}",
        }
        return headers

    def _get_url(self, path):
        return f'{self.BASE_URL}{path}'

    def get(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self._headers)
        return requests.get(self._get_url(path), **kwargs)

    def patch(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self._headers)
        return requests.patch(self._get_url(path), **kwargs)
