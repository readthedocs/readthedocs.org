const rtddata = require('./rtd-data');
const { createDomNode } = require('./utils');


function init(data) {
    let rtd = rtddata.get();

    /// Out of date message

    if (data.is_highest) {
        return;
    }

    let currentURL = window.location.pathname.replace(rtd['version'], data.slug);
    let warning = createDomNode('div', {class: 'admonition warning'});
    let link = createDomNode('a', {href: currentURL});
    link.innerText = data.slug;
    warning.innerHTML = '<p class="first admonition-title">Note</p> ' +
        '<p class="last"> ' +
        'You are not reading the most recent version of this documentation. ' +
        link.outerHTML +
        ' is the latest version available.' +
        '</p>';

    let selectors = ['[role=main]', 'main', 'div.body', 'div.document'];
    for (let selector of selectors) {
        let element = document.querySelector(selector);
        if (element !== null) {
            element.prepend(warning);
            break;
        }
    }
}


module.exports = {
    init: init
};
