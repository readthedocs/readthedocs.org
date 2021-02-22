import os
import sys
import io

import requests

if sys.version_info.major < 3:
    from urllib import url2pathname  # noqa
else:
    from urllib.request import url2pathname  # noqa


def recurse_while_none(element):
    if element.text is None and element.getchildren():
        return recurse_while_none(element.getchildren()[0])

    href = element.attrib.get('href')
    if not href:
        href = element.attrib.get('id')
    return {element.text: href}


class LocalFileAdapter(requests.adapters.BaseAdapter):

    """
    Protocol Adapter to allow Requests to GET file:// URLs.

    Via https://stackoverflow.com/a/27786580/4169
    """

    @staticmethod
    def _chkpath(method, path):
        """Return an HTTP status for the given filesystem path."""
        if method.lower() in ('put', 'delete'):
            return 501, "Not Implemented"  # TODO
        if method.lower() not in ('get', 'head'):
            return 405, "Method Not Allowed"
        if os.path.isdir(path):
            return 400, "Path Not A File"
        if not os.path.isfile(path):
            return 404, "File Not Found"
        if not os.access(path, os.R_OK):
            return 403, "Access Denied"

        return 200, "OK"

    def send(self, req, **kwargs):  # pylint: disable=unused-argument
        """
        Return the file specified by the given request.

        @type req: C{PreparedRequest}
        @todo: Should I bother filling `response.headers` and processing
               If-Modified-Since and friends using `os.stat`?
        """
        path = os.path.normcase(os.path.normpath(url2pathname(req.path_url)))
        response = requests.Response()

        response.status_code, response.reason = self._chkpath(req.method, path)
        if response.status_code == 200 and req.method.lower() != 'head':
            try:
                response.raw = io.open(path, mode='rb')
            except (OSError, IOError) as err:
                response.status_code = 500
                response.reason = str(err)

        if isinstance(req.url, bytes):
            response.url = req.url.decode('utf-8')
        else:
            response.url = req.url

        response.request = req
        response.connection = self

        return response

    def close(self):
        pass
