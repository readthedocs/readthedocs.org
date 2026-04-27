# Email templates

Source-of-truth [MJML](https://mjml.io/) templates for transactional email,
plus tooling to compile them to Django HTML and to preview the rendered output.

## Why MJML

The base email layout was previously a hand-rolled XHTML 1.0 transitional file
with inline `<table>` markup and a hand-maintained `<style>` block. MJML
generates that markup from a higher-level component syntax that is much easier
to keep correct across mail clients (Outlook, Gmail, Apple Mail, etc.).

## Layout

```
emails/
├── src/                # *.mjml source files (edit these)
├── build.js            # compiles src/*.mjml -> readthedocs/.../*.html
├── build.config.json   # template-namespace -> filesystem dir mapping
└── preview/
    ├── render.py       # standalone Django renderer (preview only)
    ├── screenshot.js   # puppeteer screenshotter
    └── fixtures.json   # sample contexts for previewing
```

The compiled `.html` files live alongside the templates they replace, with a
banner comment marking them as generated. **Do not edit the generated files** —
edit the matching `.mjml` source under `emails/src/`.

## Compiling

```sh
cd emails/
npm install
node build.js
```

The build script walks `emails/src/`, compiles each `*.mjml`, and writes the
result to the Django template tree resolved through `build.config.json`. Each
generated file is prefixed with `{% load i18n %}` and a "do not edit by hand"
banner.

## Previewing

To produce HTML and PNG previews of the templates rendered against sample
context:

```sh
# from the repo root
uv venv .venv-preview
uv pip install --python .venv-preview/bin/python 'django>=5,<6'
.venv-preview/bin/python emails/preview/render.py
node emails/preview/screenshot.js
```

Outputs land in `emails/preview/out/` and `emails/preview/screenshots/`.
