#!/usr/bin/env python

"""Check Nginx config on readthedocs.org."""

import sys
import requests


# Globals to keep count of test results
TESTS = 0
FAILS = 0

def served_by_nginx(url):
    """Return True if url returns 200 and is served by Nginx."""
    r = requests.get(url, allow_redirects=False)
    status = (r.status_code == 200)
    nginx = ('x-served' in r.headers and r.headers['x-served'] == 'Nginx')
    return all([status, nginx])

def served_by_django(url):
    """Return True if url returns 200 and is served by Django. (NOT Nginx)"""
    r = requests.get(url, allow_redirects=False)
    status = (r.status_code == 200)
    django = ('x-served' not in r.headers)
    return all([status, django])

def served(url):
    """Return True if url returns 200."""
    r = requests.get(url, allow_redirects=False)
    return r.status_code == 200

def redirected(url, location):
    """Return True if url is redirected to location."""
    r = requests.get(url, allow_redirects=False)
    status = (r.status_code in (301, 302))
    redirect = ('location' in r.headers and r.headers['location'] == location)
    return all([status, redirect])

def count(fn):
    def wrapped(*args, **kwargs):
        global TESTS, FAILS
        TESTS += 1
        result = fn(*args, **kwargs)
        if result is False:
            FAILS += 1
        return result
    return wrapped

@count
def run_test(fn, *args):
    """Run test and print result."""
    ret_value = fn(*args)
    result = 'ok' if ret_value else 'ERROR'
    url = args[0]
    print "{url: <65} ...  {result}".format(url=url, result=result)
    return ret_value

def header(msg):
    """Give each test a sexy header."""
    print
    print msg
    print "-----------------------------"

def summary_results(num_tests, num_fails):
    results = ['\n']
    results.append("%d URLs tested." % num_tests)
    if num_fails == 1:
        results.append("%d URL FAILED." % num_fails)
    elif num_fails > 1:
        results.append("%d URLs FAILED." % num_fails)
    else:
        results.append("All URLs passed.")
    return "\n".join(results)


def main():

    header('Served by Nginx')
    nginx_urls = subdomain_urls + cname_urls + single_version_urls + translation_urls + project_urls
    for url in nginx_urls:
        run_test(served_by_nginx, url)

    header('Served by Django')
    for url in rtd_urls:
        run_test(served_by_django, url)

    header('Served')
    for url in other_urls:
        run_test(served, url)

    header('Redirected')
    for url, redirect in redirected_urls:
        run_test(redirected, url, redirect)

    print summary_results(TESTS, FAILS)

    exit_code = 1 if (FAILS > 0) else 0
    return exit_code


if __name__ == '__main__':

    # served_by_nginx()
    subdomain_urls = [
        'https://pip.readthedocs.org/en/latest/',
        'https://pip.readthedocs.org/en/latest/usage.html',
        'https://pip.readthedocs.org/en/1.4.1/',
        'https://pip.readthedocs.org/en/1.4.1/news.html',
    ]

    # served_by_nginx()
    cname_urls = [
        'http://docs.fabfile.org/en/latest/',
        'http://docs.fabfile.org/en/latest/faq.html',
        'http://site.ericholscher.com/',
        'http://site.ericholscher.com/bike/',
    ]

    # served_by_nginx()
    translation_urls = [
        "http://phpmyadmin.readthedocs.org/ja/latest/",
        "http://phpmyadmin.readthedocs.org/cs/latest/",
        "http://phpmyadmin.readthedocs.org/en/latest/",
    ]

    # served_by_nginx()
    single_version_urls = [
        'https://ericholschercom.readthedocs.org',
        'https://ericholschercom.readthedocs.org/',
        'https://ericholschercom.readthedocs.org/en/latest/',
        'https://ericholschercom.readthedocs.org/about/',
        'https://ericholschercom.readthedocs.org/en/latest/about/'
    ]

    # served_by_django()
    project_urls = [
        'http://docs.pylonsproject.org/projects/pyramid/en/latest/',
        'http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/install.html',
        'http://docs.pylonsproject.org/projects/pyramid_amon/en/latest/',
        'http://docs.pylonsproject.org/projects/pyramid_amon/en/latest/genindex.html',
        'http://edx.readthedocs.org/projects/devdata/en/latest/',
        'http://edx.readthedocs.org/projects/devdata/en/latest/course_data_formats/course_xml.html',
    ]

    # served_by_django()
    rtd_urls = [
        'https://readthedocs.org/search/',
        'https://readthedocs.org/projects/julia/',
        'https://readthedocs.org/api/v1/?format=json',
        'https://readthedocs.org/accounts/login/',
        'https://readthedocs.org/security/',
        'https://readthedocs.org/profiles/Wraithan/',
    ]

    # served()
    other_urls = [
        'http://docs.fabfile.org/robots.txt',
        'http://docs.fabfile.org/favicon.ico',
        'https://readthedocs.org/robots.txt',
        'https://readthedocs.org/favicon.ico',
        'https://envdir.readthedocs.org/robots.txt',
        'https://envdir.readthedocs.org/favicon.ico',
        'https://media.readthedocs.org/javascript/readthedocs-doc-embed.js',
        'https://media.readthedocs.org/css/sphinx_rtd_theme.css',
    ]

    # redirected()
    redirected_urls = [
        [
            'https://pip.readthedocs.org/',
            'https://pip.readthedocs.org/en/latest/'
        ],
        [
            'https://pip.readthedocs.org/en/',
            'https://pip.readthedocs.org/en/latest/'
        ],
        [
            'https://pip.readthedocs.org/en/latest',
            'https://pip.readthedocs.org/en/latest/'
        ],
        [
            'https://pip.readthedocs.org/latest/',
            'https://pip.readthedocs.org/en/latest/'
        ],
        [
            'https://pip.readthedocs.org/page/cookbook.html',
            'https://pip.readthedocs.org/en/latest/cookbook.html'
        ],
        [
            'https://readthedocs.org/docs/pip/en/latest/',
            'https://pip.readthedocs.org/en/latest/'
        ],
        [
            'https://readthedocs.org/docs/pip/latest/',
            'https://readthedocs.org/docs/pip/en/latest/'
        ],
        [
            'https://readthedocs.org/docs/pip/en/',
            'https://readthedocs.org/docs/pip/en/latest/'
        ],
    ]

    sys.exit(main())
