import json

from flask import Flask, make_response, redirect, request

app = Flask(__name__)

PRODUCTION_DOMAIN = 'readthedocs.org'


@app.route('/')
def redirect_front():
    version = 'latest'
    language = 'en'
    single_version = False

    SUBDOMAIN = CNAME = False

    if PRODUCTION_DOMAIN in request.host:
        SUBDOMAIN = True
        slug = request.host.split('.')[0]
        path = "/home/docs/checkouts/readthedocs.org/user_builds/{slug}/metadata.json".format(slug=slug)
    else:
        try:
            cname = request.host.split(':')[0]
        except:
            cname = request.host
        CNAME = True
        path = "/home/docs/checkouts/readthedocs.org/cnametoproject/{cname}/metadata.json".format(cname=cname)

    try:
        json_obj = json.load(file(path))
        version = json_obj['version']
        language = json_obj['language']
        single_version = json_obj['single_version']
    except Exception, e:
        print e

    if single_version:
        if SUBDOMAIN:
            sendfile = "/user_builds/{slug}/translations/{language}/{version}".format(slug=slug, language=language, version=version)
        elif CNAME:
            sendfile = "/cnametoproject/{cname}/translation/{language}/{version}/".format(cname=cname, language=language, version=version)
        print "Redirecting {host} to {sendfile}".format(host=request.host, sendfile=sendfile)
        return make_response('', 200, {'X-Send-File': sendfile})
    else:
        url = '/{language}/{version}/'.format(language=language, version=version)
        print "Redirecting {host} to {url}".format(host=request.host, url=url)
        return redirect(url)


if __name__ == '__main__':
    app.run()
