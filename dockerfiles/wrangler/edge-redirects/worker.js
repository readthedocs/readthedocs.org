/**
 * Edge redirects for Read the Docs documentation domains.
 *
 * This Worker answers the redirects El Proxito computes before it touches
 * storage, using one record per hostname stored in Workers KV. Anything it
 * cannot decide from that record is passed to the origin untouched, so the
 * origin stays authoritative and a KV miss degrades to today's behaviour.
 *
 * Redirects handled, in the same order as proxito:
 *
 *   1. HTTP to HTTPS                       (proxito middleware)
 *   2. Collapse `//` in the path           (proxito middleware)
 *   3. Subproject domain to main domain    (ServeDocsBase._get_canonical_redirect_type)
 *   4. Public domain to canonical domain   (ServeDocsBase._get_canonical_redirect_type)
 *   5. `/page/<file>` to the default version          (ServePageRedirect)
 *   6. `/` and `/<lang>/` to the default version      (ServeDocsBase.serve_path)
 *   7. Old language code, `/pt_BR/` to `/pt-br/`     (ServeDocsBase.serve_path)
 *   8. Trailing slash on a version root, `/en/latest` (ServeDocsBase.serve_path)
 *
 * Not handled, always passed to the origin: pull request previews on
 * `*.readthedocs.build`, `/projects/<alias>/page/...`, proxied APIs under
 * `/_/`, user-defined redirects, and anything that needs to know whether a
 * file exists.
 *
 * Record format (one KV key per hostname, `host:<hostname>`):
 *
 *   {
 *     "project": "docs",
 *     "edge_redirects": true,
 *     "public_domain": true,
 *     "https": true,
 *     "language": "en",
 *     "default_version": "stable",
 *     "versioning_scheme": "multiple_versions_with_translations",
 *     "custom_prefix": null,
 *     "canonical_domain": null,
 *     "superproject": null,
 *     "active_versions": ["latest", "stable"],
 *     "translations": {"es": "latest"},
 *     "generation": 1727700000
 *   }
 *
 * `superproject` is `{"hostname": "main.readthedocs.io", "prefix": "/projects/sub/"}`
 * for a subproject served from its own public domain. `translations` maps a
 * language code to the default version of that translation project.
 */

const EDGE_HEADER = "X-RTD-Edge-Redirect";
const REDIRECT_HEADER = "X-RTD-Redirect";

// CDN lifetime for 302s. Mirrors RTD_TEMPORARY_REDIRECT_CDN_CACHE_CONTROL_MAX_AGE.
const REDIRECT_CACHE_MAX_AGE = 1200;

// How long an edge location keeps a KV record before re-reading it.
const KV_CACHE_TTL = 300;

const MULTIPLE_VERSIONS_WITH_TRANSLATIONS = "multiple_versions_with_translations";
const MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS = "multiple_versions_without_translations";
const SINGLE_VERSION_WITHOUT_TRANSLATIONS = "single_version_without_translations";

// Mirrors OLD_LANGUAGES_CODE_MAPPING in readthedocs/projects/constants.py.
const OLD_LANGUAGE_CODES = {
  "nb-no": "nb_NO",
  "pt-br": "pt_BR",
  "es-mx": "es_MX",
  "uk-ua": "uk_UA",
  "zh-cn": "zh_CN",
  "zh-tw": "zh_TW",
};

// Paths proxito routes to views other than ServeDocs. We never redirect these.
const PASS_THROUGH_PREFIXES = ["/_/", "/robots.txt", "/sitemap.xml", "/llms.txt"];

export default {
  async fetch(request, env, ctx) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return fetch(request);
    }

    const url = new URL(request.url);
    const host = url.hostname.toLowerCase();

    let record = null;
    try {
      record = await env.REDIRECTS.get(`host:${host}`, { type: "json", cacheTtl: KV_CACHE_TTL });
    } catch (error) {
      // KV is unavailable. Never fail closed; the origin still knows how to answer.
      return passThrough(request, "kv-error");
    }
    if (!record) {
      return passThrough(request, "no-record");
    }

    const decision = decide(url, record);
    if (!decision) {
      return passThrough(request, "none");
    }

    const live = env.EDGE_REDIRECTS_MODE === "live" && record.edge_redirects === true;
    if (!live) {
      // Shadow mode: tell the origin what we would have done and let it answer.
      return passThrough(request, `${decision.type} ${decision.location}`);
    }

    return redirectResponse(decision, record);
  },
};

/**
 * Decide whether `url` should be redirected given the hostname's record.
 *
 * Returns `{type, location}` or `null`. `type` matches proxito's
 * `RedirectType` names so the `X-RTD-Redirect` header is identical.
 */
export function decide(url, record) {
  const path = url.pathname;
  const query = url.search;
  const host = url.hostname.toLowerCase();

  if (PASS_THROUGH_PREFIXES.some((prefix) => path.startsWith(prefix))) {
    return null;
  }

  // 1. HTTP to HTTPS.
  if (url.protocol === "http:" && record.https) {
    return redirect("http_to_https", `https://${url.host}${path}${query}`);
  }

  // 2. Collapse multiple slashes.
  if (path.includes("//")) {
    const clean = "/" + path.replace(/\/\/+/g, "/").replace(/^\/+/, "");
    return redirect("system", `${clean}${query}`);
  }

  // 3. Subproject served from its own domain goes to the main project's domain.
  if (record.superproject) {
    const { hostname, prefix } = record.superproject;
    const location = `https://${hostname}${joinPath(prefix, path)}${query}`;
    return guard(url, redirect("subproject_to_main_domain", location));
  }

  // 4. Public domain goes to the canonical custom domain.
  if (record.public_domain && record.canonical_domain && record.canonical_domain !== host) {
    return redirect("to_canonical_domain", `https://${record.canonical_domain}${path}${query}`);
  }

  // Everything below is relative to the project's URL prefix.
  const prefix = normalizePrefix(record.custom_prefix);
  let rest;
  if (path === prefix.replace(/\/$/, "")) {
    rest = "";
  } else if (path.startsWith(prefix)) {
    rest = path.slice(prefix.length);
  } else {
    return null;
  }

  // 5. /page/<file> to the default version.
  if (rest === "page" || rest.startsWith("page/")) {
    const filename = rest.slice("page/".length);
    const location = resolve(record, prefix, record.language, record.default_version, filename);
    return guard(url, redirect("system", `${location}${query}`));
  }

  if (record.versioning_scheme === SINGLE_VERSION_WITHOUT_TRANSLATIONS) {
    // Single version projects serve docs at the root. Nothing else to decide.
    return null;
  }

  // 6. Root to the default version.
  if (rest === "") {
    const location = resolve(record, prefix, record.language, record.default_version, "");
    return guard(url, redirect("system", `${location}${query}`));
  }

  const segments = rest.split("/");

  if (record.versioning_scheme === MULTIPLE_VERSIONS_WITH_TRANSLATIONS) {
    const [lang, version, ...filename] = segments;

    // 7. Old language code.
    const oldCode = OLD_LANGUAGE_CODES[record.language];
    if (oldCode && lang === oldCode) {
      const location = `${prefix}${record.language}/${segments.slice(1).join("/")}`;
      return guard(url, redirect("system", `${location}${query}`));
    }

    // 6. Language root to that language's default version.
    if (segments.length === 2 && version === "") {
      const defaultVersion = defaultVersionFor(record, lang);
      if (!defaultVersion) {
        return null;
      }
      const location = resolve(record, prefix, lang, defaultVersion, "");
      return guard(url, redirect("system", `${location}${query}`));
    }

    // 8. Trailing slash on /<lang>/<version>.
    if (segments.length === 2 && isKnownVersion(record, lang, version)) {
      return redirect("system", `${path}/${query}`);
    }
    return null;
  }

  if (record.versioning_scheme === MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS) {
    // 8. Trailing slash on /<version>.
    if (segments.length === 1 && record.active_versions.includes(segments[0])) {
      return redirect("system", `${path}/${query}`);
    }
    return null;
  }

  return null;
}

function redirect(type, location) {
  return { type, location };
}

/** Drop a redirect that points back at the same host and path. */
function guard(url, decision) {
  const target = new URL(decision.location, url);
  if (target.hostname === url.hostname && target.pathname === url.pathname) {
    return null;
  }
  return decision;
}

function normalizePrefix(customPrefix) {
  if (!customPrefix) {
    return "/";
  }
  return "/" + customPrefix.replace(/^\/+/, "").replace(/\/*$/, "/");
}

function joinPath(...parts) {
  return (
    "/" +
    parts
      .map((part) => part.replace(/^\/+|\/+$/g, ""))
      .filter(Boolean)
      .join("/") +
    (parts.at(-1).endsWith("/") ? "/" : "")
  );
}

/** Build the path proxito's Resolver would, for this project's versioning scheme. */
function resolve(record, prefix, language, version, filename) {
  const file = filename.replace(/^\/+/, "");
  switch (record.versioning_scheme) {
    case MULTIPLE_VERSIONS_WITH_TRANSLATIONS:
      return `${prefix}${language}/${version}/${file}`;
    case MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS:
      return `${prefix}${version}/${file}`;
    case SINGLE_VERSION_WITHOUT_TRANSLATIONS:
      return `${prefix}${file}`;
    default:
      return `${prefix}${language}/${version}/${file}`;
  }
}

function defaultVersionFor(record, language) {
  if (language === record.language) {
    return record.default_version;
  }
  return (record.translations || {})[language] || null;
}

function isKnownVersion(record, language, version) {
  if (language === record.language) {
    return record.active_versions.includes(version);
  }
  // We only carry the default version for translations; anything else
  // falls through to the origin, which will add the slash itself.
  return (record.translations || {})[language] === version;
}

function redirectResponse(decision, record) {
  const headers = new Headers({
    Location: decision.location,
    [REDIRECT_HEADER]: decision.type,
    [EDGE_HEADER]: "hit",
    "CDN-Cache-Control": `public, max-age=${REDIRECT_CACHE_MAX_AGE}`,
    "Cache-Tag": record.project,
  });
  return new Response(null, { status: 302, headers });
}

function passThrough(request, reason) {
  const headers = new Headers(request.headers);
  headers.set(EDGE_HEADER, reason);
  return fetch(new Request(request, { headers }));
}
