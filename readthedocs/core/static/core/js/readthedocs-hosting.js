READTHEDOCS_DATA = JSON.parse(document.getElementById('READTHEDOCS_DATA').textContent);

function injectExternalVersionWarning() {
    // TODO: make all these banners (injected HTML) templates that users can override with their own.
    // This way, we allow customization of the look&feel without compromising the logic.
    let admonition = `
<div class="admonition warning">
  <p class="admonition-title">Warning</p>
  <p>
    This page
    <a class="reference external" href="${ window.location.protocol }//${ window.location.hostname }/projects/${ READTHEDOCS_DATA.project }/builds/${ READTHEDOCS_DATA.build.id }/">was created </a>
    from a pull request
    (<a class="reference external" href="${ READTHEDOCS_DATA.repository_url }/pull/${ READTHEDOCS_DATA.version }">#${ READTHEDOCS_DATA.version }</a>).
  </p>
</div>
`;

    let main = document.querySelector('[role=main]') || document.querySelector('#main');
    let node = document.createElement("div");
    node.innerHTML = admonition;
    main.insertBefore(node, main.firstChild);
}

function injectDocDiff() {
    let docdiff = document.createElement("script");
    docdiff.setAttribute("async", "async");
    docdiff.setAttribute("src", "/_/static/core/js/readthedocs-doc-diff.js");
    document.head.appendChild(docdiff);
}

function injectOldVersionWarning() {
    // TODO: compute if the user is reading the latest version or not before showing the warning.
    let admonition = `
<div class="admonition warning">
  <p class="admonition-title">Warning</p>
  <p>
    This page documents version
    <a class="reference" href="${ window.location.protocol }//${ window.location.hostname }/${ READTHEDOCS_DATA.language }/${ READTHEDOCS_DATA.version }/">${ READTHEDOCS_DATA.version }</a>.
    The latest version is
    <a class="reference" href="${ window.location.protocol }//${ window.location.hostname }/${ READTHEDOCS_DATA.language }/${ READTHEDOCS_DATA.version }/">${ READTHEDOCS_DATA.version }</a>.
  </p>
</div>
`;

    // Borrowed and adapted from:
    // https://github.com/readthedocs/readthedocs.org/blob/7ce98a4d4f34a4c1845dc6e3e0e5112af7c39b0c/readthedocs/core/static-src/core/js/doc-embed/version-compare.js#L1
    let main = document.querySelector('[role=main]') || document.querySelector('#main');
    let node = document.createElement("div");
    node.innerHTML = admonition;
    main.insertBefore(node, main.firstChild);
}


window.addEventListener("load", (event) => {
    // TODO: use the proxied API here
    // "repository_url" could be retrived using the API, but there are some CORS issues and design decisions
    // that it's probably smart to avoid and just rely on a fixed value from the build output :)
    if (READTHEDOCS_DATA.build.external_version === true) {
        injectExternalVersionWarning();

        if (READTHEDOCS_DATA.features.docdiff.enabled === true) {
            if(!window.location.pathname.endsWith("search.html")) {
                // Avoid injecting doc-diff on search page because it doesn't make sense
                injectDocDiff();
            }
        }
    }
    else {
        // TODO: there some data we need from `/api/v2/footer_html/`,
        // like `is_highest` and `show_version_warning`.
        // However, this call is happening inside the `readthedocs-doc-embed.js`.
        // We could make the call again here for now as demo,
        // but it would be good to refactor that code
        // Inject old version warning only for non-external versions
        injectOldVersionWarning();
    }
});
