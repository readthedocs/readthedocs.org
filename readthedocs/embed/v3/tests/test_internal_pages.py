from contextlib import contextmanager
from unittest import mock

import django_dynamic_fixture as fixture
import docutils
import pytest
from django.core.cache import cache
from django.urls import reverse
from packaging.version import Version

from readthedocs.projects.models import Project
from readthedocs.subscriptions.constants import TYPE_EMBED_API
from readthedocs.subscriptions.products import RTDProductFeature

from .utils import compare_content_without_blank_lines, get_anchor_link_title, srcdir


@pytest.mark.django_db
@pytest.mark.embed_api
class TestEmbedAPIv3InternalPages:
    @pytest.fixture(autouse=True)
    def setup_method(self, settings):
        settings.PUBLIC_DOMAIN = "readthedocs.io"
        settings.RTD_EMBED_API_EXTERNAL_DOMAINS = []
        settings.RTD_DEFAULT_FEATURES = dict(
            [RTDProductFeature(TYPE_EMBED_API).to_item()]
        )

        self.api_url = reverse("embed_api_v3")

        self.project = fixture.get(Project, slug="project")

        yield
        cache.clear()

    def _mock_open(self, content):
        @contextmanager
        def f(*args, **kwargs):
            read_mock = mock.MagicMock()
            read_mock.read.return_value = content
            yield read_mock

        return f

    @pytest.mark.sphinx("html", srcdir=srcdir, freshenv=True)
    @mock.patch("readthedocs.embed.v3.views.build_media_storage.open")
    @mock.patch("readthedocs.embed.v3.views.build_media_storage.exists")
    def test_default_main_section(self, storage_exists, storage_open, app, client):
        app.build()
        path = app.outdir / "index.html"
        assert path.exists() is True
        content = open(path).read()

        storage_exists.return_value = True
        storage_open.side_effect = self._mock_open(content)

        params = {
            "url": "https://project.readthedocs.io/en/latest/",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200

        title = get_anchor_link_title("heading")

        # Note the difference between `<section>` and `<div class="section">`
        if Version(docutils.__version__) >= Version("0.17"):
            content = f"""
                <div class="body" role="main">
                    <section id="title">
                        <h1>Title<a class="headerlink" href="https://project.readthedocs.io/en/latest/#title" title="{title}">¶</a></h1>
                        <p>This is an example page used to test EmbedAPI parsing features.</p>
                        <section id="sub-title">
                            <h2>Sub-title<a class="headerlink" href="https://project.readthedocs.io/en/latest/#sub-title" title="{title}">¶</a></h2>
                            <p>This is a reference to <a class="reference internal" href="https://project.readthedocs.io/en/latest/#sub-title"><span class="std std-ref">Sub-title</span></a>.</p>
                        </section>
                        <section id="manual-reference-section">
                            <span id="manual-reference"></span><h2>Manual Reference Section<a class="headerlink" href="https://project.readthedocs.io/en/latest/#manual-reference-section" title="{title}">¶</a></h2>
                            <p>This is a reference to a manual reference <a class="reference internal" href="https://project.readthedocs.io/en/latest/#manual-reference"><span class="std std-ref">Manual Reference Section</span></a>.</p>
                        </section>
                    </section>
                    <div class="clearer"></div>
                </div>
            """
        else:
            content = """
            <div class="body" role="main">
                <div class="section" id="title">
                    <h1>Title<a class="headerlink" href="https://project.readthedocs.io/en/latest/#title" title="{title}">¶</a></h1>
                    <p>This is an example page used to test EmbedAPI parsing features.</p>
                    <div class="section" id="sub-title">
                        <h2>Sub-title<a class="headerlink" href="https://project.readthedocs.io/en/latest/#sub-title" title="{title}">¶</a></h2>
                        <p>This is a reference to <a class="reference internal" href="https://project.readthedocs.io/en/latest/#sub-title"><span class="std std-ref">Sub-title</span></a>.</p>
                    </div>
                    <div class="section" id="manual-reference-section">
                        <span id="manual-reference"></span><h2>Manual Reference Section<a class="headerlink" href="https://project.readthedocs.io/en/latest/#manual-reference-section" title="{title}">¶</a></h2>
                        <p>This is a reference to a manual reference <a class="reference internal" href="https://project.readthedocs.io/en/latest/#manual-reference"><span class="std std-ref">Manual Reference Section</span></a>.</p>
                    </div>
                </div>
            </div>
            """

        json_response = response.json()
        assert json_response == {
            "url": "https://project.readthedocs.io/en/latest/",
            "fragment": None,
            "content": mock.ANY,
            "external": False,
        }
        compare_content_without_blank_lines(json_response["content"], content)

    @pytest.mark.sphinx("html", srcdir=srcdir, freshenv=False)
    @mock.patch("readthedocs.embed.v3.views.build_media_storage.open")
    @mock.patch("readthedocs.embed.v3.views.build_media_storage.exists")
    def test_s3_storage_decoded_filename(
        self, storage_exists, storage_open, app, client
    ):
        storage_exists.return_value = True
        storage_open.side_effect = self._mock_open('<div id="section">content</div>')

        params = {
            "url": "https://project.readthedocs.io/en/latest/My%20Spaced%20File.html#section",
        }
        response = client.get(self.api_url, params)
        assert response.status_code == 200

        storage_open.assert_called_once_with("html/project/latest/My Spaced File.html")
