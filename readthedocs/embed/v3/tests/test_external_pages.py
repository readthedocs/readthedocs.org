from unittest import mock

import docutils
import pytest
import sphinx
from django.core.cache import cache
from django.urls import reverse
from packaging.version import Version

from .utils import compare_content_without_blank_lines, get_anchor_link_title, srcdir


@pytest.mark.django_db
@pytest.mark.embed_api
class TestEmbedAPIv3ExternalPages:
    @pytest.fixture(autouse=True)
    def setup_method(self, settings):
        settings.PUBLIC_DOMAIN = "readthedocs.io"
        settings.RTD_EMBED_API_EXTERNAL_DOMAINS = [r"^docs\.project\.com$"]

        self.api_url = reverse("embed_api_v3")

        yield
        cache.clear()

    @pytest.mark.sphinx("html", srcdir=srcdir, freshenv=True)
    def test_default_main_section(self, app, client, requests_mock):
        app.build()
        path = app.outdir / "index.html"
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get("https://docs.project.com", text=content)

        params = {
            "url": "https://docs.project.com",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200

        title = get_anchor_link_title("heading")

        # The output is different because docutils is outputting this,
        # and we're not sanitizing it, but just passing it through.
        if Version(docutils.__version__) >= Version("0.17"):
            content = f"""
                <div class="body" role="main">
                    <section id="title">
                        <h1>Title<a class="headerlink" href="https://docs.project.com#title" title="{title}">¶</a></h1>
                        <p>This is an example page used to test EmbedAPI parsing features.</p>
                        <section id="sub-title">
                            <h2>Sub-title<a class="headerlink" href="https://docs.project.com#sub-title" title="{title}">¶</a></h2>
                            <p>This is a reference to <a class="reference internal" href="https://docs.project.com#sub-title"><span class="std std-ref">Sub-title</span></a>.</p>
                        </section>
                        <section id="manual-reference-section">
                            <span id="manual-reference"></span><h2>Manual Reference Section<a class="headerlink" href="https://docs.project.com#manual-reference-section" title="{title}">¶</a></h2>
                            <p>This is a reference to a manual reference <a class="reference internal" href="https://docs.project.com#manual-reference"><span class="std std-ref">Manual Reference Section</span></a>.</p>
                        </section>
                    </section>
                    <div class="clearer"></div>
                </div>
            """
        else:
            content = """
                <div class="body" role="main">
                    <div class="section" id="title">
                        <h1>Title<a class="headerlink" href="https://docs.project.com#title" title="{title}">¶</a></h1>
                        <p>This is an example page used to test EmbedAPI parsing features.</p>
                        <div class="section" id="sub-title">
                            <h2>Sub-title<a class="headerlink" href="https://docs.project.com#sub-title" title="{title}">¶</a></h2>
                            <p>This is a reference to <a class="reference internal" href="https://docs.project.com#sub-title"><span class="std std-ref">Sub-title</span></a>.</p>
                        </div>
                        <div class="section" id="manual-reference-section">
                            <span id="manual-reference"></span><h2>Manual Reference Section<a class="headerlink" href="https://docs.project.com#manual-reference-section" title="{title}">¶</a></h2>
                            <p>This is a reference to a manual reference <a class="reference internal" href="https://docs.project.com#manual-reference"><span class="std std-ref">Manual Reference Section</span></a>.</p>
                        </div>
                    </div>
                </div>
            """

        json_response = response.json()
        assert json_response == {
            "url": "https://docs.project.com",
            "fragment": None,
            "content": mock.ANY,
            "external": True,
        }
        compare_content_without_blank_lines(json_response["content"], content)

    @pytest.mark.sphinx("html", srcdir=srcdir, freshenv=True)
    def test_specific_main_content_selector(self, app, client, requests_mock):
        app.build()
        path = app.outdir / "index.html"
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get("https://docs.project.com", text=content)

        params = {
            "url": "https://docs.project.com",
            "maincontent": "#invalid-selector",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 404

        params = {
            "url": "https://docs.project.com",
            "maincontent": "section",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        # Check the main three sections are returned.
        assert "Title" in response.json()["content"]
        assert "Sub-title" in response.json()["content"]
        assert "Manual Reference Section" in response.json()["content"]

    @pytest.mark.sphinx("html", srcdir=srcdir, freshenv=True)
    def test_specific_identifier(self, app, client, requests_mock):
        app.build()
        path = app.outdir / "index.html"
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get("https://docs.project.com", text=content)

        params = {
            "url": "https://docs.project.com#sub-title",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200

        title = get_anchor_link_title("heading")

        if Version(docutils.__version__) >= Version("0.17"):
            content = f'<section id="sub-title">\n<h2>Sub-title<a class="headerlink" href="https://docs.project.com#sub-title" title="{title}">¶</a></h2>\n<p>This is a reference to <a class="reference internal" href="https://docs.project.com#sub-title"><span class="std std-ref">Sub-title</span></a>.</p>\n</section>'
        else:
            content = f'<div class="section" id="sub-title">\n<h2>Sub-title<a class="headerlink" href="https://docs.project.com#sub-title" title="{title}">¶</a></h2>\n<p>This is a reference to <a class="reference internal" href="https://docs.project.com#sub-title"><span class="std std-ref">Sub-title</span></a>.</p>\n</div>'

        assert response.json() == {
            "url": "https://docs.project.com#sub-title",
            "fragment": "sub-title",
            "content": content,
            "external": True,
        }

    @pytest.mark.sphinx("html", srcdir=srcdir, freshenv=True)
    def test_dl_identifier(self, app, client, requests_mock):
        app.build()
        path = app.outdir / "configuration.html"
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get("https://docs.project.com/configuration.html", text=content)

        params = {
            "url": "https://docs.project.com/configuration.html#confval-config1",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200

        title = get_anchor_link_title("definition")

        if sphinx.version_info < (3, 5, 0):
            content = f'<dt id="confval-config1">\n<code class="sig-name descname">config1</code><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="{title}">¶</a></dt>'
        elif sphinx.version_info[:2] == (3, 5):
            content = f'<dt id="confval-config1">\n<code class="sig-name descname"><span class="pre">config1</span></code><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="{title}">¶</a></dt>'
        else:
            content = f'<dt class="sig sig-object std" id="confval-config1">\n<span class="sig-name descname"><span class="pre">config1</span></span><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="{title}">¶</a></dt>'

        assert response.json() == {
            "url": "https://docs.project.com/configuration.html#confval-config1",
            "fragment": "confval-config1",
            "content": content,
            "external": True,
        }

    @pytest.mark.sphinx("html", srcdir=srcdir, freshenv=True)
    def test_dl_identifier_doctool_sphinx(self, app, client, requests_mock):
        app.build()
        path = app.outdir / "configuration.html"
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get("https://docs.project.com/configuration.html", text=content)

        # Calling the API without doctool
        params = {
            "url": "https://docs.project.com/configuration.html#confval-config1",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200

        title = get_anchor_link_title("definition")

        if sphinx.version_info < (3, 5, 0):
            content = f'<dt id="confval-config1">\n<code class="sig-name descname">config1</code><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="{title}">¶</a></dt>'
        elif sphinx.version_info[:2] == (3, 5):
            content = f'<dt id="confval-config1">\n<code class="sig-name descname"><span class="pre">config1</span></code><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="{title}">¶</a></dt>'
        else:
            content = f'<dt class="sig sig-object std" id="confval-config1">\n<span class="sig-name descname"><span class="pre">config1</span></span><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="{title}">¶</a></dt>'

        assert response.json() == {
            "url": "https://docs.project.com/configuration.html#confval-config1",
            "fragment": "confval-config1",
            "content": content,
            "external": True,
        }

        # Calling the API with doctool
        params = {
            "url": "https://docs.project.com/configuration.html#confval-config1",
            "doctool": "sphinx",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200

        if sphinx.version_info < (3, 0, 0):  # <3.0
            content = f'<dl class="confval">\n<dt id="confval-config1">\n<code class="sig-name descname">config1</code><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="{title}">¶</a></dt>\n<dd><p>Description: This the description for config1</p>\n<p>Default: <code class="docutils literal notranslate"><span class="pre">\'Default</span> <span class="pre">value</span> <span class="pre">for</span> <span class="pre">config\'</span></code></p>\n<p>Type: bool</p>\n</dd></dl>'
        elif sphinx.version_info[:2] == (3, 5):
            content = f'<dl class="std confval">\n<dt id="confval-config1">\n<code class="sig-name descname"><span class="pre">config1</span></code><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="{title}">¶</a></dt>\n<dd><p>Description: This the description for config1</p>\n<p>Default: <code class="docutils literal notranslate"><span class="pre">\'Default</span> <span class="pre">value</span> <span class="pre">for</span> <span class="pre">config\'</span></code></p>\n<p>Type: bool</p>\n</dd></dl>'
        elif sphinx.version_info < (4, 0, 0):  # >3.0,=!3.5.x,<4.0
            content = f'<dl class="std confval">\n<dt id="confval-config1">\n<code class="sig-name descname">config1</code><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="{title}">¶</a></dt>\n<dd><p>Description: This the description for config1</p>\n<p>Default: <code class="docutils literal notranslate"><span class="pre">\'Default</span> <span class="pre">value</span> <span class="pre">for</span> <span class="pre">config\'</span></code></p>\n<p>Type: bool</p>\n</dd></dl>'
        else:  # >=4.0
            content = f'<dl class="std confval">\n<dt class="sig sig-object std" id="confval-config1">\n<span class="sig-name descname"><span class="pre">config1</span></span><a class="headerlink" href="https://docs.project.com/configuration.html#confval-config1" title="{title}">¶</a></dt>\n<dd><p>Description: This the description for config1</p>\n<p>Default: <code class="docutils literal notranslate"><span class="pre">\'Default</span> <span class="pre">value</span> <span class="pre">for</span> <span class="pre">config\'</span></code></p>\n<p>Type: bool</p>\n</dd></dl>'

        assert response.json() == {
            "url": "https://docs.project.com/configuration.html#confval-config1",
            "fragment": "confval-config1",
            "content": content,
            "external": True,
        }

    # TODO: make the test to behave properly with docutils>17. The structure of
    # the HTML has changed and the ids are not generated as `idX` anymore.
    @pytest.mark.skipif(
        Version(docutils.__version__) >= Version("0.18"),
        reason="docutils>0.18 is not yet supported",
    )
    @pytest.mark.sphinx("html", srcdir=srcdir, freshenv=True)
    def test_citation_identifier_doctool_sphinx(self, app, client, requests_mock):
        app.build()
        path = app.outdir / "bibtex-cite.html"
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get("https://docs.project.com/bibtex-cite.html", text=content)

        # Calling the API without doctool
        params = {
            "url": "https://docs.project.com/bibtex-cite.html#id4",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        assert response.json() == {
            "url": "https://docs.project.com/bibtex-cite.html#id4",
            "fragment": "id4",
            "content": '<dt class="label" id="id4"><span class="brackets">Nel87</span><span class="fn-backref">(<a href="https://docs.project.com/bibtex-cite.html#id1">1</a>,<a href="https://docs.project.com/bibtex-cite.html#id2">2</a>)</span></dt>',
            "external": True,
        }

        # Calling the API with doctool
        params = {
            "url": "https://docs.project.com/bibtex-cite.html#id4",
            "doctool": "sphinx",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200
        assert response.json() == {
            "url": "https://docs.project.com/bibtex-cite.html#id4",
            "fragment": "id4",
            "content": '<dl class="citation">\n<dt class="label" id="id4"><span class="brackets">Nel87</span><span class="fn-backref">(<a href="https://docs.project.com/bibtex-cite.html#id1">1</a>,<a href="https://docs.project.com/bibtex-cite.html#id2">2</a>)</span></dt>\n<dd><p>Edward Nelson. <em>Radically Elementary Probability Theory</em>. Princeton University Press, 1987.</p>\n</dd>\n</dl>',
            "external": True,
        }

    @pytest.mark.sphinx("html", srcdir=srcdir, freshenv=True)
    def test_glossary_identifier_doctool_sphinx(self, app, client, requests_mock):
        app.build()
        path = app.outdir / "glossary.html"
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get("https://docs.project.com/glossary.html", text=content)

        # Note there are differences on the case of the fragment
        if sphinx.version_info >= (3, 0, 0):
            fragment = "term-Read-the-Docs"
        else:
            fragment = "term-read-the-docs"

        # Calling the API without doctool
        url = f"https://docs.project.com/glossary.html#{fragment}"
        params = {
            "url": url,
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200

        title = get_anchor_link_title("term")

        if sphinx.version_info >= (3, 5, 0):
            content = f'<dt id="{fragment}">Read the Docs<a class="headerlink" href="https://docs.project.com/glossary.html#{fragment}" title="{title}">¶</a></dt>'
        else:
            content = f'<dt id="{fragment}">Read the Docs</dt>'

        assert response.json() == {
            "url": url,
            "fragment": fragment,
            "content": content,
            "external": True,
        }

        # Calling the API with doctool
        params = {
            "url": url,
            "doctool": "sphinx",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200

        if Version(docutils.__version__) >= Version("0.18"):
            classes = "simple glossary"
        else:
            classes = "glossary simple"

        if sphinx.version_info >= (3, 5, 0):
            content = f'<dl class="{classes}">\n\n<dt id="{fragment}">Read the Docs<a class="headerlink" href="https://docs.project.com/glossary.html#{fragment}" title="{title}">¶</a></dt><dd><p>Best company ever.</p>\n</dd>\n</dl>'
        else:
            content = f'<dl class="{classes}">\n\n<dt id="{fragment}">Read the Docs</dt><dd><p>Best company ever.</p>\n</dd>\n</dl>'

        assert response.json() == {
            "url": url,
            "content": content,
            "fragment": fragment,
            "external": True,
        }

    @pytest.mark.sphinx("html", srcdir=srcdir, freshenv=True)
    def test_manual_references(self, app, client, requests_mock):
        app.build()
        path = app.outdir / "index.html"
        assert path.exists() is True
        content = open(path).read()
        requests_mock.get("https://docs.project.com/", text=content)

        # Calling the API without doctool
        fragment = "manual-reference"
        url = f"https://docs.project.com/#{fragment}"
        params = {
            "url": url,
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200

        content = f'<span id="{fragment}"></span>'
        assert response.json() == {
            "url": url,
            "fragment": fragment,
            "content": content,
            "external": True,
        }

        # Calling the API with doctool
        params = {
            "url": url,
            "doctool": "sphinx",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200

        title = get_anchor_link_title("heading")

        # Note the difference between `<section>` and `<div class="section">`
        if Version(docutils.__version__) >= Version("0.17"):
            content = f'<section id="manual-reference-section">\n<span id="manual-reference"></span><h2>Manual Reference Section<a class="headerlink" href="https://docs.project.com/#manual-reference-section" title="{title}">¶</a></h2>\n<p>This is a reference to a manual reference <a class="reference internal" href="https://docs.project.com/#manual-reference"><span class="std std-ref">Manual Reference Section</span></a>.</p>\n</section>'
        else:
            content = f'<div class="section" id="manual-reference-section">\n<span id="manual-reference"></span><h2>Manual Reference Section<a class="headerlink" href="https://docs.project.com/#manual-reference-section" title="{title}">¶</a></h2>\n<p>This is a reference to a manual reference <a class="reference internal" href="https://docs.project.com/#manual-reference"><span class="std std-ref">Manual Reference Section</span></a>.</p>\n</div>'

        assert response.json() == {
            "url": url,
            "content": content,
            "fragment": fragment,
            "external": True,
        }
