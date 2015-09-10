/**
 * highlight a given string on a jquery object by wrapping it in
 * span elements with the given class name.
 */
jQuery.fn.highlightText = function(text, className) {
    function highlight(node) {
        if (node.nodeType == 3) {
            var val = node.nodeValue;
            var pos = val.toLowerCase().indexOf(text);
            if (pos >= 0 && !jQuery(node.parentNode).hasClass(className)) {
                var span = document.createElement("span");
                span.className = className;
                span.appendChild(document.createTextNode(val.substr(pos, text.length)));
                node.parentNode.insertBefore(span, node.parentNode.insertBefore(
                    document.createTextNode(val.substr(pos + text.length)),
                    node.nextSibling));
                    node.nodeValue = val.substr(0, pos);
            }
        }
        else if (!jQuery(node).is("button, select, textarea")) {
            jQuery.each(node.childNodes, function() {
                highlight(this);
            });
        }
    }
    return this.each(function() {
        highlight(this);
    });
};
