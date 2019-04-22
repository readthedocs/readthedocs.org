import requests
import slumber


def setup_api(token):
    session = requests.Session()
    session.headers.update({'Authorization': f'Token {token}'})
    return slumber.API('http://localhost:8000/api/v3/', session=session)

api = setup_api(123)
