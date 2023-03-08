function injectExternalVersionWarning() {
    let admonition = `
<div class="admonition warning">
  <p class="admonition-title">Warning</p>
  <p>
    This page
    <a class="reference external" href="${ window.location.protocol }//${ window.location.domain }/projects/${ READTHEDOCS_DATA.project }/builds/${ READTHEDOCS_DATA.build.id }/">was created </a>
    from a pull request
    (<a class="reference external" href="${ READTHEDOCS_DATA.repository_url }/pull/${ READTHEDOCS_DATA.version }">#${ READTHEDOCS_DATA.version }</a>).
  </p>
</div>
`;

    let main = document.querySelector('[role=main]');
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

window.addEventListener("load", (event) => {
    if (READTHEDOCS_DATA.build.external_version === true) {
        injectExternalVersionWarning();

        if (READTHEDOCS_DATA.features.docdiff.enabled === true) {
            injectDocDiff();
        }
    }
});
