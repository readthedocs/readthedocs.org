import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import worker, { decide } from "./worker.js";

const { records, cases } = JSON.parse(readFileSync(new URL("./cases.json", import.meta.url), "utf8"));

for (const c of cases) {
  test(`decide: ${c.name}`, () => {
    const decision = decide(new URL(c.url), records[c.record]);
    if (c.type === null) {
      assert.equal(decision, null);
    } else {
      assert.ok(decision, "expected a redirect");
      assert.equal(decision.type, c.type);
      assert.equal(decision.location, c.location);
    }
  });
}

class FakeKV {
  constructor(entries = {}, { fail = false } = {}) {
    this.entries = entries;
    this.fail = fail;
  }

  async get(key, options) {
    if (this.fail) {
      throw new Error("kv down");
    }
    const value = this.entries[key];
    if (value === undefined) {
      return null;
    }
    return options?.type === "json" ? value : JSON.stringify(value);
  }
}

/** Run the worker with `fetch` stubbed so a pass-through returns the request it would send. */
async function run(url, env) {
  const original = globalThis.fetch;
  globalThis.fetch = async (request) => new Response(`origin:${request.headers.get("X-RTD-Edge-Redirect")}`);
  try {
    return await worker.fetch(new Request(url), env, {});
  } finally {
    globalThis.fetch = original;
  }
}

test("fetch: live mode answers from the edge", async () => {
  const env = { REDIRECTS: new FakeKV({ "host:docs.readthedocs.io": records.docs }), EDGE_REDIRECTS_MODE: "live" };
  const response = await run("https://docs.readthedocs.io/?a=1", env);
  assert.equal(response.status, 302);
  assert.equal(response.headers.get("Location"), "/en/stable/?a=1");
  assert.equal(response.headers.get("X-RTD-Redirect"), "system");
  assert.equal(response.headers.get("CDN-Cache-Control"), "public, max-age=1200");
  assert.equal(response.headers.get("Cache-Tag"), "docs");
});

test("fetch: shadow mode forwards with the decision as a header", async () => {
  const env = { REDIRECTS: new FakeKV({ "host:docs.readthedocs.io": records.docs }), EDGE_REDIRECTS_MODE: "shadow" };
  const response = await run("https://docs.readthedocs.io/", env);
  assert.equal(await response.text(), "origin:system /en/stable/");
});

test("fetch: live mode respects the per-project flag", async () => {
  const record = { ...records.docs, edge_redirects: false };
  const env = { REDIRECTS: new FakeKV({ "host:docs.readthedocs.io": record }), EDGE_REDIRECTS_MODE: "live" };
  const response = await run("https://docs.readthedocs.io/", env);
  assert.equal(await response.text(), "origin:system /en/stable/");
});

test("fetch: no record passes through", async () => {
  const env = { REDIRECTS: new FakeKV({}), EDGE_REDIRECTS_MODE: "live" };
  const response = await run("https://unknown.readthedocs.io/", env);
  assert.equal(await response.text(), "origin:no-record");
});

test("fetch: kv failure passes through", async () => {
  const env = { REDIRECTS: new FakeKV({}, { fail: true }), EDGE_REDIRECTS_MODE: "live" };
  const response = await run("https://docs.readthedocs.io/", env);
  assert.equal(await response.text(), "origin:kv-error");
});

test("fetch: a real page passes through with a 'none' marker", async () => {
  const env = { REDIRECTS: new FakeKV({ "host:docs.readthedocs.io": records.docs }), EDGE_REDIRECTS_MODE: "live" };
  const response = await run("https://docs.readthedocs.io/en/latest/index.html", env);
  assert.equal(await response.text(), "origin:none");
});
