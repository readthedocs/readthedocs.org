/**
 * Create and return DOM nodes with given attributes.
 *
 * @param {String} nodeName - Name of the node.
 * @param {Object} attributes - Obj of attributes to be assigned to the node.
 * @return {Object} DOM node.
 */
const createDomNode = (nodeName, attributes) => {
    let node = document.createElement(nodeName);
    if (attributes) {
        for (let attr of Object.keys(attributes)) {
            node.setAttribute(attr, attributes[attr]);
        }
    }
    return node;
};

module.exports = { createDomNode };
