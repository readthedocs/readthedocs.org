from requests_toolbelt.adapters.host_header_ssl import HostHeaderSSLAdapter
from requests.adapters import HTTPAdapter


class TimeoutAdapter:

    """
    Adapter to inject ``timeout`` to all the requests.

    Allows us to not wait forever when querying our API internally from the
    builders and make the build fail faster if it goes wrong.

    https://2.python-requests.org//en/master/user/advanced/#transport-adapters
    https://2.python-requests.org//en/master/user/advanced/#timeouts
    """

    def send(self, *args, **kwargs):
        kwargs.update({
            'timeout': 5,  # 5 seconds in total (connect + read)
        })
        return super().send(*args, **kwargs)


class TimeoutHostHeaderSSLAdapter(TimeoutAdapter, HostHeaderSSLAdapter):
    pass


class TimeoutHTTPAdapter(TimeoutAdapter, HTTPAdapter):
    pass
