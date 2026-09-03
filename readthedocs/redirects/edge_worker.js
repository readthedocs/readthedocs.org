/**
 * Reference Cloudflare Worker for serving heavy redirects at the edge.
 *
 * There are two ways the routing data reaches this Worker. Both are
 * supported here; see docs/dev/design/redirects-at-the-edge.rst.
 *
 *   1. No-config (header learning): the origin emits a project's forced
 *      redirects on the `X-RTD-Edge-Redirects` response header. The Worker
 *      caches them per-host in the Cache API and serves subsequent requests
 *      at the edge. This needs no Cloudflare API credentials or sync pipeline.
 *
 *   2. Pre-warmed (KV): a backend pipeline writes the rules into a Workers KV
 *      namespace ahead of time. Useful to absorb an attack from the very
 *      first request, before the edge has learned anything.
 *
 * The matching here must stay in parity with `match_redirect()` in
 * `readthedocs/redirects/edge.py`.
 *
 * Bindings (both optional):
 *   - REDIRECTS_KV: a Workers KV namespace (pre-warmed path).
 */

const SPLAT_PLACEHOLDER = ":splat";
const EXACT_REDIRECT = "exact";
const HEADER = "X-RTD-Edge-Redirects";
// How long the edge trusts header-learned rules (seconds).
const CACHE_TTL = 60;

export default {
  async fetch(request, env, ctx) {
    try {
      const rules = await getRules(request, env);
      if (rules) {
        const redirect = buildRedirect(request, rules);
        if (redirect) {
          return redirect;
        }
      }
    } catch (err) {
      // Fail open: never let an edge bug take down doc serving.
      console.error("edge redirect error", err);
    }

    // Pass through to the origin, and learn any rules it advertises.
    const response = await fetch(request);
    ctx.waitUntil(learnFromResponse(request, response));
    return response;
  },
};

async function getRules(request, env) {
  const cached = await readCachedRules(request);
  if (cached) {
    return cached;
  }
  // Fall back to the pre-warmed KV namespace, if configured.
  if (env.REDIRECTS_KV) {
    const url = new URL(request.url);
    const domain = await env.REDIRECTS_KV.get(`domain:${url.hostname}`, "json");
    if (domain) {
      const project = await env.REDIRECTS_KV.get(`project:${domain.project}`, "json");
      if (project && project.redirects) {
        return project.redirects;
      }
    }
  }
  return null;
}

function cacheKey(request) {
  const url = new URL(request.url);
  // Key only on the host: the rules are per-project, not per-path.
  return new Request(`https://edge-redirects.invalid/${url.hostname}`);
}

async function readCachedRules(request) {
  const hit = await caches.default.match(cacheKey(request));
  if (!hit) {
    return null;
  }
  return hit.json();
}

async function learnFromResponse(request, response) {
  const header = response.headers.get(HEADER);
  if (!header) {
    return;
  }
  let rules;
  try {
    rules = JSON.parse(header);
  } catch (err) {
    return;
  }
  const body = new Response(JSON.stringify(rules), {
    headers: { "Cache-Control": `max-age=${CACHE_TTL}` },
  });
  await caches.default.put(cacheKey(request), body);
}

function buildRedirect(request, rules) {
  const url = new URL(request.url);
  const match = matchRedirect(rules, url.pathname);
  if (!match) {
    return null;
  }
  const target = new URL(match.to, url).toString();
  return new Response(null, {
    status: match.status,
    headers: {
      Location: target,
      // Mirror the origin so analytics can attribute edge redirects.
      "X-RTD-Redirect": "user",
      "X-RTD-Redirect-Source": "edge",
    },
  });
}

function matchRedirect(rules, pathname) {
  const normalized = "/" + pathname.replace(/^\/+/, "");
  const withoutSlash = normalized.replace(/\/+$/, "") || "/";

  for (const redirect of rules) {
    if (redirect.type !== EXACT_REDIRECT) {
      continue;
    }

    if (redirect.from_prefix === null) {
      if (withoutSlash === redirect.from.replace(/\/+$/, "")) {
        return { to: redirect.to, status: redirect.status };
      }
      continue;
    }

    if (normalized.startsWith(redirect.from_prefix)) {
      if (willCauseInfiniteRedirect(redirect.from_prefix, redirect.to, normalized)) {
        continue;
      }
      const splat = normalized.slice(redirect.from_prefix.length);
      const to = redirect.to.replace(SPLAT_PLACEHOLDER, splat);
      return { to, status: redirect.status };
    }
  }

  return null;
}

function willCauseInfiniteRedirect(fromPrefix, toUrl, currentPath) {
  if (!toUrl.includes(SPLAT_PLACEHOLDER)) {
    return false;
  }
  const toWithoutSplat = toUrl.split(SPLAT_PLACEHOLDER)[0];
  const redirectsToSubpath = toWithoutSplat.startsWith(fromPrefix);
  return redirectsToSubpath && currentPath.startsWith(toWithoutSplat);
}
