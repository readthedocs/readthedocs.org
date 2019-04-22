from client import api
from utils import p

p(api.projects('test-builds').get(expand=''))
