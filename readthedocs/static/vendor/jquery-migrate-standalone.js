!function(e){"object"==typeof exports&&"undefined"!=typeof module?module.exports=e():"function"==typeof define&&define.amd?define([],e):("undefined"!=typeof window?window:"undefined"!=typeof global?global:"undefined"!=typeof self?self:this).jqueryMigrate=e()}(function(){return function r(o,a,i){function s(t,e){if(!a[t]){if(!o[t]){var n="function"==typeof require&&require;if(!e&&n)return n(t,!0);if(u)return u(t,!0);throw(e=new Error("Cannot find module '"+t+"'")).code="MODULE_NOT_FOUND",e}n=a[t]={exports:{}},o[t][0].call(n.exports,function(e){return s(o[t][1][e]||e)},n,n.exports,r,o,a,i)}return a[t].exports}for(var u="function"==typeof require&&require,e=0;e<i.length;e++)s(i[e]);return s}({"/usr/src/app/readthedocs.org/bower_components/jquery-migrate/jquery-migrate.js":[function(e,t,n){function u(e){var t=o.console;s[e]||(s[e]=!0,c.migrateWarnings.push(e),t&&t.warn&&!c.migrateMute&&(t.warn("JQMIGRATE: "+e),c.migrateTrace&&t.trace&&t.trace()))}function r(e,t,n,r){if(Object.defineProperty)try{return void Object.defineProperty(e,t,{configurable:!0,enumerable:!0,get:function(){return u(r),n},set:function(e){u(r),n=e}})}catch(e){}c._definePropertyBroken=!0,e[t]=n}function a(e){return"string"!=typeof e||c.event.special.hover?e:(O.test(e)&&u("'hover' pseudo-event is deprecated, use 'mouseenter mouseleave'"),e&&e.replace(O,"mouseenter$1 mouseleave$1"))}var c,o,i,s,d,p,l,f,g,h,v,m,y,b,w,j,x,Q,N,k,T,M,S,C,H,L,A,O;c=jQuery,o=window,s={},c.migrateWarnings=[],!c.migrateMute&&o.console&&o.console.log&&o.console.log("JQMIGRATE: Logging is active"),c.migrateTrace===i&&(c.migrateTrace=!0),c.migrateReset=function(){s={},c.migrateWarnings.length=0},"BackCompat"===document.compatMode&&u("jQuery is not compatible with Quirks Mode"),d=c("<input/>",{size:1}).attr("size")&&c.attrFn,p=c.attr,l=c.attrHooks.value&&c.attrHooks.value.get||function(){return null},f=c.attrHooks.value&&c.attrHooks.value.set||function(){return i},g=/^(?:input|button)$/i,h=/^[238]$/,v=/^(?:autofocus|autoplay|async|checked|controls|defer|disabled|hidden|loop|multiple|open|readonly|required|scoped|selected)$/i,m=/^(?:checked|selected)$/i,r(c,"attrFn",d||{},"jQuery.attrFn is deprecated"),c.attr=function(e,t,n,r){var o=t.toLowerCase(),a=e&&e.nodeType;return r&&(p.length<4&&u("jQuery.fn.attr( props, pass ) is deprecated"),e&&!h.test(a)&&(d?t in d:c.isFunction(c.fn[t])))?c(e)[t](n):("type"===t&&n!==i&&g.test(e.nodeName)&&e.parentNode&&u("Can't change the 'type' of an input or button in IE 6/7/8"),!c.attrHooks[o]&&v.test(o)&&(c.attrHooks[o]={get:function(e,t){var n=c.prop(e,t);return!0===n||"boolean"!=typeof n&&(n=e.getAttributeNode(t))&&!1!==n.nodeValue?t.toLowerCase():i},set:function(e,t,n){return!1===t?c.removeAttr(e,n):((t=c.propFix[n]||n)in e&&(e[t]=!0),e.setAttribute(n,n.toLowerCase())),n}},m.test(o)&&u("jQuery.fn.attr('"+o+"') may use property instead of attribute")),p.call(c,e,t,n))},c.attrHooks.value={get:function(e,t){var n=(e.nodeName||"").toLowerCase();return"button"===n?l.apply(this,arguments):("input"!==n&&"option"!==n&&u("jQuery.fn.attr('value') no longer gets properties"),t in e?e.value:null)},set:function(e,t){var n=(e.nodeName||"").toLowerCase();if("button"===n)return f.apply(this,arguments);"input"!==n&&"option"!==n&&u("jQuery.fn.attr('value', val) no longer sets properties"),e.value=t}},b=c.fn.init,w=c.parseJSON,j=/^([^<]*)(<[\w\W]+>)([^>]*)$/,c.fn.init=function(e,t,n){var r;return e&&"string"==typeof e&&!c.isPlainObject(t)&&(r=j.exec(c.trim(e)))&&r[0]&&("<"!==e.charAt(0)&&u("$(html) HTML strings must start with '<' character"),r[3]&&u("$(html) HTML text after last tag is ignored"),"#"===r[0].charAt(0)&&(u("HTML string cannot start with a '#' character"),c.error("JQMIGRATE: Invalid selector string (XSS)")),t&&t.context&&(t=t.context),c.parseHTML)?b.call(this,c.parseHTML(r[2],t,!0),t,n):b.apply(this,arguments)},c.fn.init.prototype=c.fn,c.parseJSON=function(e){return e||null===e?w.apply(this,arguments):(u("jQuery.parseJSON requires a valid JSON string"),null)},c.uaMatch=function(e){e=e.toLowerCase();e=/(chrome)[ \/]([\w.]+)/.exec(e)||/(webkit)[ \/]([\w.]+)/.exec(e)||/(opera)(?:.*version|)[ \/]([\w.]+)/.exec(e)||/(msie) ([\w.]+)/.exec(e)||e.indexOf("compatible")<0&&/(mozilla)(?:.*? rv:([\w.]+)|)/.exec(e)||[];return{browser:e[1]||"",version:e[2]||"0"}},c.browser||(y={},(L=c.uaMatch(navigator.userAgent)).browser&&(y[L.browser]=!0,y.version=L.version),y.chrome?y.webkit=!0:y.webkit&&(y.safari=!0),c.browser=y),r(c,"browser",c.browser,"jQuery.browser is deprecated"),c.sub=function(){function n(e,t){return new n.fn.init(e,t)}c.extend(!0,n,this),n.superclass=this,((n.fn=n.prototype=this()).constructor=n).sub=this.sub,n.fn.init=function(e,t){return t&&t instanceof c&&!(t instanceof n)&&(t=n(t)),c.fn.init.call(this,e,t,r)},n.fn.init.prototype=n.fn;var r=n(document);return u("jQuery.sub() is deprecated"),n},c.ajaxSetup({converters:{"text json":c.parseJSON}}),x=c.fn.data,c.fn.data=function(e){var t,n=this[0];return!n||"events"!==e||1!==arguments.length||(t=c.data(n,e),n=c._data(n,e),t!==i&&t!==n||n===i)?x.apply(this,arguments):(u("Use of jQuery.fn.data('events') is deprecated"),n)},Q=/\/(java|ecma)script/i,N=c.fn.andSelf||c.fn.addBack,c.fn.andSelf=function(){return u("jQuery.fn.andSelf() replaced by jQuery.fn.addBack()"),N.apply(this,arguments)},c.clean||(c.clean=function(e,t,n,r){t=(t=!(t=t||document).nodeType&&t[0]||t).ownerDocument||t,u("jQuery.clean() is deprecated");var o,a,i,s=[];if(c.merge(s,c.buildFragment(e,t).childNodes),n)for(a=function(e){if(!e.type||Q.test(e.type))return r?r.push(e.parentNode?e.parentNode.removeChild(e):e):n.appendChild(e)},o=0;null!=(i=s[o]);o++)c.nodeName(i,"script")&&a(i)||(n.appendChild(i),void 0!==i.getElementsByTagName&&(i=c.grep(c.merge([],i.getElementsByTagName("script")),a),s.splice.apply(s,[o+1,0].concat(i)),o+=i.length));return s}),k=c.event.add,T=c.event.remove,M=c.event.trigger,S=c.fn.toggle,C=c.fn.live,H=c.fn.die,L="ajaxStart|ajaxStop|ajaxSend|ajaxComplete|ajaxError|ajaxSuccess",A=new RegExp("\\b(?:"+L+")\\b"),O=/(?:^|\s)hover(\.\S+|)\b/,c.event.props&&"attrChange"!==c.event.props[0]&&c.event.props.unshift("attrChange","attrName","relatedNode","srcElement"),c.event.dispatch&&r(c.event,"handle",c.event.dispatch,"jQuery.event.handle is undocumented and deprecated"),c.event.add=function(e,t,n,r,o){e!==document&&A.test(t)&&u("AJAX events should be attached to document: "+t),k.call(this,e,a(t||""),n,r,o)},c.event.remove=function(e,t,n,r,o){T.call(this,e,a(t)||"",n,r,o)},c.fn.error=function(){var e=Array.prototype.slice.call(arguments,0);return u("jQuery.fn.error() is deprecated"),e.splice(0,0,"error"),arguments.length?this.bind.apply(this,e):(this.triggerHandler.apply(this,e),this)},c.fn.toggle=function(n,e){if(!c.isFunction(n)||!c.isFunction(e))return S.apply(this,arguments);u("jQuery.fn.toggle(handler, handler...) is deprecated");function t(e){var t=(c._data(this,"lastToggle"+n.guid)||0)%a;return c._data(this,"lastToggle"+n.guid,1+t),e.preventDefault(),r[t].apply(this,arguments)||!1}var r=arguments,o=n.guid||c.guid++,a=0;for(t.guid=o;a<r.length;)r[a++].guid=o;return this.click(t)},c.fn.live=function(e,t,n){return u("jQuery.fn.live() is deprecated"),C?C.apply(this,arguments):(c(this.context).on(e,this.selector,t,n),this)},c.fn.die=function(e,t){return u("jQuery.fn.die() is deprecated"),H?H.apply(this,arguments):(c(this.context).off(e,this.selector||"**",t),this)},c.event.trigger=function(e,t,n,r){return n||A.test(e)||u("Global events are undocumented and deprecated"),M.call(this,e,t,n||document,r)},c.each(L.split("|"),function(e,t){c.event.special[t]={setup:function(){var e=this;return e!==document&&(c.event.add(document,t+"."+c.guid,function(){c.event.trigger(t,null,e,!0)}),c._data(this,t,c.guid++)),!1},teardown:function(){return this!==document&&c.event.remove(document,t+"."+c._data(this,t)),!1}}})},{}]},{},[])("/usr/src/app/readthedocs.org/bower_components/jquery-migrate/jquery-migrate.js")});
