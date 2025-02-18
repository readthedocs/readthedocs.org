import django_dynamic_fixture as fixture
import pytest
from django.test import override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Version
from readthedocs.core.unresolver import (
    InvalidCustomDomainError,
    InvalidExternalDomainError,
    InvalidExternalVersionError,
    InvalidPathForVersionedProjectError,
    InvalidSchemeError,
    InvalidSubdomainError,
    SuspiciousHostnameError,
    TranslationNotFoundError,
    TranslationWithoutVersionError,
    VersionNotFoundError,
    unresolve,
    unresolver,
)
from readthedocs.projects.constants import SINGLE_VERSION_WITHOUT_TRANSLATIONS
from readthedocs.projects.models import Domain
from readthedocs.rtd_tests.tests.test_resolver import ResolverBase


@override_settings(
    PUBLIC_DOMAIN="readthedocs.io",
    RTD_EXTERNAL_VERSION_DOMAIN="dev.readthedocs.build",
)
@pytest.mark.proxito
class UnResolverTests(ResolverBase):
    def test_unresolver(self):
        parts = unresolve(
            "https://pip.readthedocs.io/en/latest/foo.html?search=api#fragment"
        )
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/foo.html")
        self.assertEqual(parts.parsed_url.fragment, "fragment")
        self.assertEqual(parts.parsed_url.query, "search=api")

    def test_filename_wihtout_index(self):
        parts = unresolve(
            "https://pip.readthedocs.io/en/latest/file/", append_indexhtml=False
        )
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/file/")

    def test_no_trailing_slash(self):
        parts = unresolve("https://pip.readthedocs.io/en/latest")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/index.html")

    def test_trailing_slash(self):
        parts = unresolve("https://pip.readthedocs.io/en/latest/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/index.html")

    def test_file_with_trailing_slash(self):
        parts = unresolve("https://pip.readthedocs.io/en/latest/foo/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/foo/index.html")

    def test_project_no_version_and_language(self):
        with pytest.raises(InvalidPathForVersionedProjectError) as excinfo:
            unresolve("https://pip.readthedocs.io/")
        exc = excinfo.value
        self.assertEqual(exc.project, self.pip)
        self.assertEqual(exc.path, "/")

        with pytest.raises(InvalidPathForVersionedProjectError) as excinfo:
            unresolve("https://pip.readthedocs.io/foo/bar")
        exc = excinfo.value
        self.assertEqual(exc.project, self.pip)
        self.assertEqual(exc.path, "/foo/bar")

    def test_subproject_no_version_and_language(self):
        with pytest.raises(InvalidPathForVersionedProjectError) as excinfo:
            unresolve("https://pip.readthedocs.io/projects/sub/")
        exc = excinfo.value
        self.assertEqual(exc.project, self.subproject)
        self.assertEqual(exc.path, "/")

        with pytest.raises(InvalidPathForVersionedProjectError) as excinfo:
            unresolve("https://pip.readthedocs.io/projects/sub/foo/bar")
        exc = excinfo.value
        self.assertEqual(exc.project, self.subproject)
        self.assertEqual(exc.path, "/foo/bar")

    def test_path_no_version(self):
        urls = [
            "https://pip.readthedocs.io/en",
            "https://pip.readthedocs.io/en/",
        ]
        for url in urls:
            with pytest.raises(TranslationWithoutVersionError) as excinfo:
                unresolve(url)
            exc = excinfo.value
            self.assertEqual(exc.project, self.pip)
            self.assertEqual(exc.language, "en")

        urls = [
            "https://pip.readthedocs.io/ja",
            "https://pip.readthedocs.io/ja/",
        ]
        for url in urls:
            with pytest.raises(TranslationWithoutVersionError) as excinfo:
                unresolve(url)
            exc = excinfo.value
            self.assertEqual(exc.project, self.translation)
            self.assertEqual(exc.language, "ja")

    def test_invalid_language_no_version(self):
        urls = [
            "https://pip.readthedocs.io/es",
            "https://pip.readthedocs.io/es/",
        ]
        for url in urls:
            with pytest.raises(TranslationNotFoundError) as excinfo:
                unresolve(url)
            exc = excinfo.value
            self.assertEqual(exc.project, self.pip)
            self.assertEqual(exc.language, "es")
            self.assertEqual(exc.version_slug, None)
            self.assertEqual(exc.filename, "/")

    def test_unresolver_subproject(self):
        parts = unresolve("https://pip.readthedocs.io/projects/sub/ja/latest/foo.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.subproject)
        self.assertEqual(parts.version, self.subproject_version)
        self.assertEqual(parts.filename, "/foo.html")

    def test_unresolve_subproject_with_translation(self):
        parts = unresolve("https://pip.readthedocs.io/projects/sub/es/latest/foo.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.subproject_translation)
        self.assertEqual(parts.version, self.subproject_translation_version)
        self.assertEqual(parts.filename, "/foo.html")

    def test_unresolve_subproject_single_version(self):
        self.subproject.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.subproject.save()
        parts = unresolve("https://pip.readthedocs.io/projects/sub/foo.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.subproject)
        self.assertEqual(parts.version, self.subproject_version)
        self.assertEqual(parts.filename, "/foo.html")

    def test_unresolve_subproject_alias(self):
        relation = self.pip.subprojects.first()
        relation.alias = "sub_alias"
        relation.save()
        parts = unresolve("https://pip.readthedocs.io/projects/sub_alias/ja/latest/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.subproject)
        self.assertEqual(parts.version, self.subproject_version)
        self.assertEqual(parts.filename, "/index.html")

    def test_unresolve_subproject_invalid_version(self):
        with pytest.raises(VersionNotFoundError) as excinfo:
            unresolve("https://pip.readthedocs.io/projects/sub/ja/nothing/foo.html")
        exc = excinfo.value

        self.assertEqual(exc.project, self.subproject)
        self.assertEqual(exc.version_slug, "nothing")
        self.assertEqual(exc.filename, "/foo.html")

    def test_unresolve_subproject_invalid_translation(self):
        with pytest.raises(TranslationNotFoundError) as excinfo:
            unresolve("https://pip.readthedocs.io/projects/sub/fr/latest/foo.html")

        exc = excinfo.value
        self.assertEqual(exc.project, self.subproject)
        self.assertEqual(exc.language, "fr")
        self.assertEqual(exc.filename, "/foo.html")

    def test_unresolver_translation(self):
        parts = unresolve("https://pip.readthedocs.io/ja/latest/foo.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.translation)
        self.assertEqual(parts.version, self.translation_version)
        self.assertEqual(parts.filename, "/foo.html")

    def test_unresolve_no_existing_translation(self):
        with pytest.raises(TranslationNotFoundError) as excinfo:
            unresolve("https://pip.readthedocs.io/es/latest/")
        exc = excinfo.value
        self.assertEqual(exc.project, self.pip)
        self.assertEqual(exc.language, "es")
        self.assertEqual(exc.filename, "/")

    def test_unresolver_custom_domain(self):
        self.domain = fixture.get(
            Domain,
            domain="docs.foobar.com",
            project=self.pip,
            canonical=True,
        )
        parts = unresolve("https://docs.foobar.com/en/latest/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/index.html")

    def test_unresolve_single_version(self):
        self.pip.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.pip.save()
        parts = unresolve("https://pip.readthedocs.io/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/index.html")

    def test_unresolve_single_version_translation_like_path(self):
        self.pip.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.pip.save()
        parts = unresolve("https://pip.readthedocs.io/en/latest/index.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/en/latest/index.html")

    def test_unresolve_single_version_subproject_like_path(self):
        self.pip.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.pip.save()
        parts = unresolve(
            "https://pip.readthedocs.io/projects/other/en/latest/index.html"
        )
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/projects/other/en/latest/index.html")

    def test_unresolve_single_version_subproject(self):
        self.pip.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.pip.save()
        parts = unresolve(
            "https://pip.readthedocs.io/projects/sub/ja/latest/index.html"
        )
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.subproject)
        self.assertEqual(parts.version, self.subproject_version)
        self.assertEqual(parts.filename, "/index.html")

    def test_unresolver_external_version(self):
        version = get(
            Version,
            project=self.pip,
            type=EXTERNAL,
            slug="10",
            active=True,
        )
        parts = unresolve("https://pip--10.dev.readthedocs.build/en/10/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, version)
        self.assertEqual(parts.filename, "/index.html")

    def test_external_version_single_version_project(self):
        self.pip.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.pip.save()
        version = get(
            Version,
            project=self.pip,
            type=EXTERNAL,
            slug="10",
            active=True,
        )
        parts = unresolve("https://pip--10.dev.readthedocs.build/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, version)
        self.assertEqual(parts.filename, "/index.html")

    def test_unexisting_external_version_single_version_project(self):
        self.pip.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.pip.save()
        with pytest.raises(VersionNotFoundError) as excinfo:
            unresolve("https://pip--10.dev.readthedocs.build/")

        exc = excinfo.value
        self.assertEqual(exc.project, self.pip)
        self.assertEqual(exc.version_slug, "10")
        self.assertEqual(exc.filename, "/")

    def test_non_external_version_single_version_project(self):
        self.pip.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.pip.save()

        with pytest.raises(VersionNotFoundError) as excinfo:
            unresolve("https://pip--latest.dev.readthedocs.build/")
        exc = excinfo.value
        self.assertEqual(exc.project, self.pip)
        self.assertEqual(exc.version_slug, "latest")
        self.assertEqual(exc.filename, "/")

    def test_unresolve_external_version_no_existing_version(self):
        with pytest.raises(VersionNotFoundError) as excinfo:
            unresolve("https://pip--10.dev.readthedocs.build/en/10/")

        exc = excinfo.value
        self.assertEqual(exc.project, self.pip)
        self.assertEqual(exc.version_slug, "10")
        self.assertEqual(exc.filename, "/")

    def test_external_version_not_matching_final_version(self):
        with pytest.raises(InvalidExternalVersionError) as excinfo:
            unresolve("https://pip--10.dev.readthedocs.build/en/latest/")
        exc = excinfo.value
        self.assertEqual(exc.project, self.pip)
        self.assertEqual(exc.version_slug, "latest")
        self.assertEqual(exc.external_version_slug, "10")

    def test_normal_version_in_external_version_subdomain(self):
        with pytest.raises(VersionNotFoundError) as excinfo:
            unresolve("https://pip--latest.dev.readthedocs.build/en/latest/")
        exc = excinfo.value
        self.assertEqual(exc.project, self.pip)
        self.assertEqual(exc.version_slug, "latest")
        self.assertEqual(exc.filename, "/")

    def test_malformed_external_version(self):
        with pytest.raises(InvalidExternalDomainError):
            unresolve("https://pip-latest.dev.readthedocs.build/en/latest/")

    def test_unresolver_unknown_host(self):
        with pytest.raises(InvalidCustomDomainError):
            unresolve("https://random.stuff.com/en/latest/")

    def test_unresolver_suspicious_hostname(self):
        with pytest.raises(SuspiciousHostnameError):
            unresolve("https://readthedocs.io.phishing.com/en/latest/")

        with pytest.raises(SuspiciousHostnameError):
            unresolve("https://dev.readthedocs.build.phishing.com/en/latest/")

    @override_settings(
        PUBLIC_DOMAIN="readthedocs.dev",
        RTD_EXTERNAL_VERSION_DOMAIN="build.readthedocs.dev",
    )
    def test_unresolve_overlapping_public_and_external_domains(self):
        external_version = get(
            Version,
            project=self.pip,
            type=EXTERNAL,
            slug="10",
            active=True,
        )
        parts = unresolve("https://pip.readthedocs.dev/en/latest/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/index.html")

        parts = unresolve("https://pip--10.build.readthedocs.dev/en/10/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, external_version)
        self.assertEqual(parts.filename, "/index.html")

    def test_unresolve_invalid_scheme(self):
        invalid_urls = [
            "fttp://pip.readthedocs.io/en/latest/",
            "fttps://pip.readthedocs.io/en/latest/",
            "ssh://pip.readthedocs.io/en/latest/",
            "javascript://pip.readthedocs.io/en/latest/",
            "://pip.readthedocs.io/en/latest/",
        ]
        for url in invalid_urls:
            with pytest.raises(InvalidSchemeError):
                unresolve(url)

        # A triple slash is interpreted as a URL without domain,
        # we don't support that.
        with pytest.raises(InvalidSubdomainError):
            unresolve("https:///pip.readthedocs.io/en/latest/")

    def test_unresolve_domain_with_full_url(self):
        result = unresolver.unresolve_domain("https://pip.readthedocs.io/en/latest/")
        self.assertIsNone(result.domain)
        self.assertEqual(result.project, self.pip)
        self.assertTrue(result.is_from_public_domain)
        self.assertEqual(result.source_domain, "pip.readthedocs.io")

    def test_unresolve_domain_with_full_url_invalid_protocol(self):
        invalid_protocols = [
            "fttp",
            "fttps",
            "ssh",
            "javascript",
        ]
        for protocol in invalid_protocols:
            with pytest.raises(InvalidSchemeError):
                unresolver.unresolve_domain(
                    f"{protocol}://pip.readthedocs.io/en/latest/"
                )
