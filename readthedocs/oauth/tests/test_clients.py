import jwt
from django.conf import settings

from readthedocs.oauth import clients


def test_gh_app_jwt_is_signed_with_the_private_key_parsed_once():
    clients._load_gh_app_private_key.cache_clear()
    public_key = clients._get_gh_app_private_key().public_key()

    for _ in range(3):
        token = clients.get_gh_app_client().auth.token
        payload = jwt.decode(token, public_key, algorithms=["RS256"])
        assert payload["iss"] == str(settings.GITHUB_APP_CLIENT_ID)

    assert clients._load_gh_app_private_key.cache_info().misses == 1
