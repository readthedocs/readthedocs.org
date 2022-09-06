/**
 * Create and return DOM nodes with given attributes.
 *
 * @param {String} nodeName - Name of the node.
 * @param {Object} attributes - Obj of attributes to be assigned to the node.
 * @return {Object} DOM node.
 */
function createDomNode(nodeName, attributes) {
    let node = document.createElement(nodeName);
    if (attributes) {
        for (let attr of Object.keys(attributes)) {
            node.setAttribute(attr, attributes[attr]);
        }
    }
    return node;
}

function domReady(fn) {
    // If the DOM is already done parsing
    if (document.readyState === "complete" || document.readyState === "interactive") {
        setTimeout(fn, 1);
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
}

module.exports = { createDomNode, domReady};
