!function(e){if("object"==typeof exports&&"undefined"!=typeof module)module.exports=e();else if("function"==typeof define&&define.amd)define([],e);else{var t;t="undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:this,t.jqueryMigrate=e()}}(function(){return function e(t,n,r){function o(i,s){if(!n[i]){if(!t[i]){var u="function"==typeof require&&require;if(!s&&u)return u(i,!0);if(a)return a(i,!0);var c=new Error("Cannot find module '"+i+"'");throw c.code="MODULE_NOT_FOUND",c}var d=n[i]={exports:{}};t[i][0].call(d.exports,function(e){var n=t[i][1][e];return o(n?n:e)},d,d.exports,e,t,n,r)}return n[i].exports}for(var a="function"==typeof require&&require,i=0;i<r.length;i++)o(r[i]);return o}({"/home/aim/rtd/checkouts/readthedocs.org/bower_components/jquery-migrate/jquery-migrate.js":[function(e,t,n){!function(e,t,n){function r(n){var r=t.console;a[n]||(a[n]=!0,e.migrateWarnings.push(n),r&&r.warn&&!e.migrateMute&&(r.warn("JQMIGRATE: "+n),e.migrateTrace&&r.trace&&r.trace()))}function o(t,n,o,a){if(Object.defineProperty)try{return void Object.defineProperty(t,n,{configurable:!0,enumerable:!0,get:function(){return r(a),o},set:function(e){r(a),o=e}})}catch(i){}e._definePropertyBroken=!0,t[n]=o}var a={};e.migrateWarnings=[],!e.migrateMute&&t.console&&t.console.log&&t.console.log("JQMIGRATE: Logging is active"),e.migrateTrace===n&&(e.migrateTrace=!0),e.migrateReset=function(){a={},e.migrateWarnings.length=0},"BackCompat"===document.compatMode&&r("jQuery is not compatible with Quirks Mode");var i=e("<input/>",{size:1}).attr("size")&&e.attrFn,s=e.attr,u=e.attrHooks.value&&e.attrHooks.value.get||function(){return null},c=e.attrHooks.value&&e.attrHooks.value.set||function(){return n},d=/^(?:input|button)$/i,l=/^[238]$/,p=/^(?:autofocus|autoplay|async|checked|controls|defer|disabled|hidden|loop|multiple|open|readonly|required|scoped|selected)$/i,f=/^(?:checked|selected)$/i;o(e,"attrFn",i||{},"jQuery.attrFn is deprecated"),e.attr=function(t,o,a,u){var c=o.toLowerCase(),h=t&&t.nodeType;return u&&(s.length<4&&r("jQuery.fn.attr( props, pass ) is deprecated"),t&&!l.test(h)&&(i?o in i:e.isFunction(e.fn[o])))?e(t)[o](a):("type"===o&&a!==n&&d.test(t.nodeName)&&t.parentNode&&r("Can't change the 'type' of an input or button in IE 6/7/8"),!e.attrHooks[c]&&p.test(c)&&(e.attrHooks[c]={get:function(t,r){var o,a=e.prop(t,r);return a===!0||"boolean"!=typeof a&&(o=t.getAttributeNode(r))&&o.nodeValue!==!1?r.toLowerCase():n},set:function(t,n,r){var o;return n===!1?e.removeAttr(t,r):(o=e.propFix[r]||r,o in t&&(t[o]=!0),t.setAttribute(r,r.toLowerCase())),r}},f.test(c)&&r("jQuery.fn.attr('"+c+"') may use property instead of attribute")),s.call(e,t,o,a))},e.attrHooks.value={get:function(e,t){var n=(e.nodeName||"").toLowerCase();return"button"===n?u.apply(this,arguments):("input"!==n&&"option"!==n&&r("jQuery.fn.attr('value') no longer gets properties"),t in e?e.value:null)},set:function(e,t){var n=(e.nodeName||"").toLowerCase();return"button"===n?c.apply(this,arguments):("input"!==n&&"option"!==n&&r("jQuery.fn.attr('value', val) no longer sets properties"),void(e.value=t))}};var h,g,v=e.fn.init,m=e.parseJSON,y=/^([^<]*)(<[\w\W]+>)([^>]*)$/;e.fn.init=function(t,n,o){var a;return t&&"string"==typeof t&&!e.isPlainObject(n)&&(a=y.exec(e.trim(t)))&&a[0]&&("<"!==t.charAt(0)&&r("$(html) HTML strings must start with '<' character"),a[3]&&r("$(html) HTML text after last tag is ignored"),"#"===a[0].charAt(0)&&(r("HTML string cannot start with a '#' character"),e.error("JQMIGRATE: Invalid selector string (XSS)")),n&&n.context&&(n=n.context),e.parseHTML)?v.call(this,e.parseHTML(a[2],n,!0),n,o):v.apply(this,arguments)},e.fn.init.prototype=e.fn,e.parseJSON=function(e){return e||null===e?m.apply(this,arguments):(r("jQuery.parseJSON requires a valid JSON string"),null)},e.uaMatch=function(e){e=e.toLowerCase();var t=/(chrome)[ \/]([\w.]+)/.exec(e)||/(webkit)[ \/]([\w.]+)/.exec(e)||/(opera)(?:.*version|)[ \/]([\w.]+)/.exec(e)||/(msie) ([\w.]+)/.exec(e)||e.indexOf("compatible")<0&&/(mozilla)(?:.*? rv:([\w.]+)|)/.exec(e)||[];return{browser:t[1]||"",version:t[2]||"0"}},e.browser||(h=e.uaMatch(navigator.userAgent),g={},h.browser&&(g[h.browser]=!0,g.version=h.version),g.chrome?g.webkit=!0:g.webkit&&(g.safari=!0),e.browser=g),o(e,"browser",e.browser,"jQuery.browser is deprecated"),e.sub=function(){function t(e,n){return new t.fn.init(e,n)}e.extend(!0,t,this),t.superclass=this,t.fn=t.prototype=this(),t.fn.constructor=t,t.sub=this.sub,t.fn.init=function(r,o){return o&&o instanceof e&&!(o instanceof t)&&(o=t(o)),e.fn.init.call(this,r,o,n)},t.fn.init.prototype=t.fn;var n=t(document);return r("jQuery.sub() is deprecated"),t},e.ajaxSetup({converters:{"text json":e.parseJSON}});var b=e.fn.data;e.fn.data=function(t){var o,a,i=this[0];return!i||"events"!==t||1!==arguments.length||(o=e.data(i,t),a=e._data(i,t),o!==n&&o!==a||a===n)?b.apply(this,arguments):(r("Use of jQuery.fn.data('events') is deprecated"),a)};var w=/\/(java|ecma)script/i,j=e.fn.andSelf||e.fn.addBack;e.fn.andSelf=function(){return r("jQuery.fn.andSelf() replaced by jQuery.fn.addBack()"),j.apply(this,arguments)},e.clean||(e.clean=function(t,n,o,a){n=n||document,n=!n.nodeType&&n[0]||n,n=n.ownerDocument||n,r("jQuery.clean() is deprecated");var i,s,u,c,d=[];if(e.merge(d,e.buildFragment(t,n).childNodes),o)for(u=function(e){if(!e.type||w.test(e.type))return a?a.push(e.parentNode?e.parentNode.removeChild(e):e):o.appendChild(e)},i=0;null!=(s=d[i]);i++)e.nodeName(s,"script")&&u(s)||(o.appendChild(s),"undefined"!=typeof s.getElementsByTagName&&(c=e.grep(e.merge([],s.getElementsByTagName("script")),u),d.splice.apply(d,[i+1,0].concat(c)),i+=c.length));return d});var x=e.event.add,Q=e.event.remove,k=e.event.trigger,N=e.fn.toggle,T=e.fn.live,M=e.fn.die,S="ajaxStart|ajaxStop|ajaxSend|ajaxComplete|ajaxError|ajaxSuccess",C=new RegExp("\\b(?:"+S+")\\b"),H=/(?:^|\s)hover(\.\S+|)\b/,L=function(t){return"string"!=typeof t||e.event.special.hover?t:(H.test(t)&&r("'hover' pseudo-event is deprecated, use 'mouseenter mouseleave'"),t&&t.replace(H,"mouseenter$1 mouseleave$1"))};e.event.props&&"attrChange"!==e.event.props[0]&&e.event.props.unshift("attrChange","attrName","relatedNode","srcElement"),e.event.dispatch&&o(e.event,"handle",e.event.dispatch,"jQuery.event.handle is undocumented and deprecated"),e.event.add=function(e,t,n,o,a){e!==document&&C.test(t)&&r("AJAX events should be attached to document: "+t),x.call(this,e,L(t||""),n,o,a)},e.event.remove=function(e,t,n,r,o){Q.call(this,e,L(t)||"",n,r,o)},e.fn.error=function(){var e=Array.prototype.slice.call(arguments,0);return r("jQuery.fn.error() is deprecated"),e.splice(0,0,"error"),arguments.length?this.bind.apply(this,e):(this.triggerHandler.apply(this,e),this)},e.fn.toggle=function(t,n){if(!e.isFunction(t)||!e.isFunction(n))return N.apply(this,arguments);r("jQuery.fn.toggle(handler, handler...) is deprecated");var o=arguments,a=t.guid||e.guid++,i=0,s=function(n){var r=(e._data(this,"lastToggle"+t.guid)||0)%i;return e._data(this,"lastToggle"+t.guid,r+1),n.preventDefault(),o[r].apply(this,arguments)||!1};for(s.guid=a;i<o.length;)o[i++].guid=a;return this.click(s)},e.fn.live=function(t,n,o){return r("jQuery.fn.live() is deprecated"),T?T.apply(this,arguments):(e(this.context).on(t,this.selector,n,o),this)},e.fn.die=function(t,n){return r("jQuery.fn.die() is deprecated"),M?M.apply(this,arguments):(e(this.context).off(t,this.selector||"**",n),this)},e.event.trigger=function(e,t,n,o){return n||C.test(e)||r("Global events are undocumented and deprecated"),k.call(this,e,t,n||document,o)},e.each(S.split("|"),function(t,n){e.event.special[n]={setup:function(){var t=this;return t!==document&&(e.event.add(document,n+"."+e.guid,function(){e.event.trigger(n,null,t,!0)}),e._data(this,n,e.guid++)),!1},teardown:function(){return this!==document&&e.event.remove(document,n+"."+e._data(this,n)),!1}}})}(jQuery,window)},{}]},{},[])("/home/aim/rtd/checkouts/readthedocs.org/bower_components/jquery-migrate/jquery-migrate.js")});