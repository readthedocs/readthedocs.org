#!/usr/bin/env node
/*
 * Compile all `*.mjml` sources under emails/src/ into the matching Django
 * template paths in the readthedocs/ tree.
 *
 * The Django template namespace (e.g. `core/email/base.html`) is mirrored under
 * emails/src/ as the source path. The destination on disk is resolved through
 * `emails/build.config.json`, which maps each namespace prefix to the
 * filesystem template dir that owns it.
 */

const fs = require("fs");
const path = require("path");
const mjml2html = require("mjml");

const ROOT = path.resolve(__dirname, "..");
const SRC_DIR = path.resolve(__dirname, "src");
const CONFIG = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, "build.config.json"), "utf8"),
);

function* walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walk(full);
    } else if (entry.isFile() && entry.name.endsWith(".mjml")) {
      yield full;
    }
  }
}

function resolveDest(namespacePath) {
  // namespacePath looks like "core/email/base.html"
  for (const [prefix, templateDir] of Object.entries(CONFIG.mappings)) {
    if (namespacePath.startsWith(prefix)) {
      return path.join(ROOT, templateDir, namespacePath);
    }
  }
  throw new Error(`No mapping for namespace path: ${namespacePath}`);
}

async function compile(srcFile) {
  const namespacePath = path
    .relative(SRC_DIR, srcFile)
    .replace(/\.mjml$/, ".html");
  const dest = resolveDest(namespacePath);

  const source = fs.readFileSync(srcFile, "utf8");
  const { html, errors } = await mjml2html(source, {
    filePath: srcFile,
    keepComments: false,
    validationLevel: "strict",
  });

  if (errors && errors.length) {
    for (const err of errors) {
      console.error(`[mjml] ${srcFile}: ${err.formattedMessage || err.message}`);
    }
    throw new Error(`MJML compilation failed for ${srcFile}`);
  }

  // MJML strips anything outside <mjml>, so we prepend Django directives that
  // need to be at the top of the rendered template.
  const banner = [
    "{% load i18n %}",
    "{# This file is generated from emails/src/" +
      path.relative(SRC_DIR, srcFile) +
      ". Do not edit by hand. #}",
    "",
  ].join("\n");

  // Strip trailing whitespace and normalize the trailing newline so the output
  // satisfies the project pre-commit hooks (trailing-whitespace, end-of-file).
  const cleaned = (banner + html)
    .split("\n")
    .map((line) => line.replace(/[ \t]+$/, ""))
    .join("\n")
    .replace(/\n+$/, "") + "\n";

  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.writeFileSync(dest, cleaned);
  console.log(`compiled ${path.relative(ROOT, srcFile)} -> ${path.relative(ROOT, dest)}`);
}

async function main() {
  let count = 0;
  for (const src of walk(SRC_DIR)) {
    await compile(src);
    count++;
  }
  console.log(`\nCompiled ${count} email template(s).`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
