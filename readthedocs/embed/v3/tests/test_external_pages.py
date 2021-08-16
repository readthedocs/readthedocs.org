import os

import pytest

from django.conf import settings
from django.core.cache import cache
from django.urls import reverse

from .utils import srcdir


@pytest.mark.django_db
@pytest.mark.embed_api
class TestEmbedAPIv3ExternalPages:

    @pytest.fixture(autouse=True)
    def setup_method(self, settings):
        settings.USE_SUBDOMAIN = True
        settings.PUBLIC_DOMAIN = 'readthedocs.io'
        settings.RTD_EMBED_API_EXTERNAL_DOMAINS = ['docs.project.com']

        self.api_url = reverse('embed_api_v3')

        yield
        cache.clear()

    @pytest.mark.sphinx('html', srcdir=srcdir, freshenv=True)
    def test_default_main_section(self, app, client, requests_mock):
        app.build()
        path = app.outdir / 'index.html'
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get('https://docs.project.com', text=content)

        params = {
            'url': 'https://docs.project.com',
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        assert response.json() == {
            'url': 'https://docs.project.com',
            'fragment': None,
            'content': '<div class="body" role="main">\n            \n  <section id="title">\n<h1>Title<a class="headerlink" href="https://docs.project.com#title" title="Permalink to this headline">¶</a></h1>\n<p>This is an example page used to test EmbedAPI parsing features.</p>\n<section id="sub-title">\n<h2>Sub-title<a class="headerlink" href="https://docs.project.com#sub-title" title="Permalink to this headline">¶</a></h2>\n<p>This is a reference to <a class="reference internal" href="https://docs.project.com#sub-title"><span class="std std-ref">Sub-title</span></a>.</p>\n</section>\n</section>\n\n\n          </div>',
            'external': True,
        }

    @pytest.mark.sphinx('html', srcdir=srcdir, freshenv=True)
    def test_specific_identifier(self, app, client, requests_mock):
        app.build()
        path = app.outdir / 'index.html'
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get('https://docs.project.com', text=content)

        params = {
            'url': 'https://docs.project.com#sub-title',
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        assert response.json() == {
            'url': 'https://docs.project.com#sub-title',
            'fragment': 'sub-title',
            'content': '<section id="sub-title">\n<h2>Sub-title<a class="headerlink" href="https://docs.project.com#sub-title" title="Permalink to this headline">¶</a></h2>\n<p>This is a reference to <a class="reference internal" href="https://docs.project.com#sub-title"><span class="std std-ref">Sub-title</span></a>.</p>\n</section>',
            'external': True,
        }

    @pytest.mark.sphinx('html', srcdir=srcdir, freshenv=True)
    def test_dl_identifier(self, app, client, requests_mock):
        app.build()
        path = app.outdir / 'configuration.html'
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get('https://docs.project.com/configuration.html', text=content)

        params = {
            'url': 'https://docs.project.com/configuration.html#confval-config1',
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        assert response.json() == {
            'url': 'https://docs.project.com/configuration.html#confval-config1',
            'fragment': 'confval-config1',
            'content': '<dt class="sig sig-object std" id="confval-config1">\n<span class="sig-name descname"><span class="pre">config1</span></span><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="Permalink to this definition">¶</a></dt>',
            'external': True,
        }

    @pytest.mark.sphinx('html', srcdir=srcdir, freshenv=True)
    def test_dl_identifier_doctool_sphinx(self, app, client, requests_mock):
        app.build()
        path = app.outdir / 'configuration.html'
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get('https://docs.project.com/configuration.html', text=content)

        # Calling the API without doctool/doctoolversion/doctoolwriter
        params = {
            'url': 'https://docs.project.com/configuration.html#confval-config1',
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        assert response.json() == {
            'url': 'https://docs.project.com/configuration.html#confval-config1',
            'fragment': 'confval-config1',
            'content': '<dt class="sig sig-object std" id="confval-config1">\n<span class="sig-name descname"><span class="pre">config1</span></span><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="Permalink to this definition">¶</a></dt>',
            'external': True,
        }

        # Calling the API with doctool/doctoolversion/doctoolwriter
        params = {
            'url': 'https://docs.project.com/configuration.html#confval-config1',
            'doctool': 'sphinx',
            'doctoolversion': '4.1.0',
            'doctoolwriter': 'html4',
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        assert response.json() == {
            'url': 'https://docs.project.com/configuration.html#confval-config1',
            'fragment': 'confval-config1',
            'content': '<dl class="std confval">\n<dt class="sig sig-object std" id="confval-config1">\n<span class="sig-name descname"><span class="pre">config1</span></span><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="Permalink to this definition">¶</a></dt>\n<dd><p>Description: This the description for config1</p>\n<p>Default: <code class="docutils literal notranslate"><span class="pre">\'Default</span> <span class="pre">value</span> <span class="pre">for</span> <span class="pre">config\'</span></code></p>\n<p>Type: bool</p>\n</dd></dl>',
            'external': True,
        }

    @pytest.mark.sphinx('html', srcdir=srcdir, freshenv=True)
    @pytest.mark.skipif(os.environ.get('TOX_ENV_NAME') != 'embed-api', reason='sphinxcontrib-bibtex is not installed')
    def test_citation_identifier_doctool_sphinx(self, app, client, requests_mock):
        app.build()
        path = app.outdir / 'bibtex-cite.html'
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get('https://docs.project.com/bibtex-cite.html', text=content)

        # Calling the API without doctool/doctoolversion/doctoolwriter
        params = {
            'url': 'https://docs.project.com/bibtex-cite.html#id4',
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        assert response.json() == {
            'url': 'https://docs.project.com/bibtex-cite.html#id4',
            'fragment': 'id4',
            'content': '<dt class="label" id="id4"><span class="brackets">Nel87</span><span class="fn-backref">(<a href="https://docs.project.com/bibtex-cite.html#id1">1</a>,<a href="https://docs.project.com/bibtex-cite.html#id2">2</a>)</span></dt>',
            'external': True,
        }

        # Calling the API with doctool/doctoolversion/doctoolwriter
        params = {
            'url': 'https://docs.project.com/bibtex-cite.html#id4',
            'doctool': 'sphinx',
            'doctoolversion': '4.1.0',
            'doctoolwriter': 'html5',
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        assert response.json() == {
            'url': 'https://docs.project.com/bibtex-cite.html#id4',
            'fragment': 'id4',
            'content': '<dl class="citation">\n<dt class="label" id="id4"><span class="brackets">Nel87</span><span class="fn-backref">(<a href="https://docs.project.com/bibtex-cite.html#id1">1</a>,<a href="https://docs.project.com/bibtex-cite.html#id2">2</a>)</span></dt>\n<dd><p>Edward Nelson. <em>Radically Elementary Probability Theory</em>. Princeton University Press, 1987.</p>\n</dd>\n</dl>',
            'external': True,
        }

    @pytest.mark.sphinx('html', srcdir=srcdir, freshenv=True)
    def test_glossary_identifier_doctool_sphinx(self, app, client, requests_mock):
        app.build()
        path = app.outdir / 'glossary.html'
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get('https://docs.project.com/glossary.html', text=content)

        # Calling the API without doctool/doctoolversion/doctoolwriter
        params = {
            'url': 'https://docs.project.com/glossary.html#term-Read-the-Docs',
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        assert response.json() == {
            'url': 'https://docs.project.com/glossary.html#term-Read-the-Docs',
            'fragment': 'term-Read-the-Docs',
            'content': '<dt id="term-Read-the-Docs">Read the Docs<a class="headerlink" href="https://docs.project.com/glossary.html#term-Read-the-Docs" title="Permalink to this term">¶</a></dt>',
            'external': True,
        }

        # Calling the API with doctool/doctoolversion/doctoolwriter
        params = {
            'url': 'https://docs.project.com/glossary.html#term-Read-the-Docs',
            'doctool': 'sphinx',
            'doctoolversion': '4.1.0',
            'doctoolwriter': 'html4',
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        assert response.json() == {
            'url': 'https://docs.project.com/glossary.html#term-Read-the-Docs',
            'fragment': 'term-Read-the-Docs',
            'content': '<dl class="glossary simple">\n<dt id="term-Read-the-Docs">Read the Docs<a class="headerlink" href="https://docs.project.com/glossary.html#term-Read-the-Docs" title="Permalink to this term">¶</a></dt><dd><p>Best company ever.</p>\n</dd>\n</dl>',
            'external': True,
        }
