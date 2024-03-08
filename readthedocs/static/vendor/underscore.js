require=function e(u,i,o){function l(t,n){if(!i[t]){if(!u[t]){var r="function"==typeof require&&require;if(!n&&r)return r(t,!0);if(a)return a(t,!0);throw(n=new Error("Cannot find module '"+t+"'")).code="MODULE_NOT_FOUND",n}r=i[t]={exports:{}},u[t][0].call(r.exports,function(n){return l(u[t][1][n]||n)},r,r.exports,e,u,i,o)}return i[t].exports}for(var a="function"==typeof require&&require,n=0;n<o.length;n++)l(o[n]);return l}({underscore:[function(n,O,F){!function(){function c(u,i,n){if(void 0===i)return u;switch(null==n?3:n){case 1:return function(n){return u.call(i,n)};case 2:return function(n,t){return u.call(i,n,t)};case 3:return function(n,t,r){return u.call(i,n,t,r)};case 4:return function(n,t,r,e){return u.call(i,n,t,r,e)}}return function(){return u.apply(i,arguments)}}function n(i){return function(r,e,n){var u={};return e=b.iteratee(e,n),b.each(r,function(n,t){t=e(n,t,r);i(u,n,t)}),u}}function l(n,t,r,e){if(t&&b.every(n,b.isArray))return v.apply(e,n);for(var u=0,i=n.length;u<i;u++){var o=n[u];b.isArray(o)||b.isArguments(o)?t?p.apply(e,o):l(o,t,r,e):r||e.push(o)}return e}function o(){}function t(t){function r(n){return t[n]}var n="(?:"+b.keys(t).join("|")+")",e=RegExp(n),u=RegExp(n,"g");return function(n){return e.test(n=null==n?"":""+n)?n.replace(u,r):n}}function a(n){return"\\"+A[n]}function e(n){return this._chain?b(n).chain():n}var r=this,u=r._,i=Array.prototype,f=Object.prototype,s=Function.prototype,p=i.push,h=i.slice,v=i.concat,g=f.toString,y=f.hasOwnProperty,f=Array.isArray,d=Object.keys,m=s.bind,b=function(n){return n instanceof b?n:this instanceof b?void(this._wrapped=n):new b(n)},_=(void 0!==F?(F=void 0!==O&&O.exports?O.exports=b:F)._=b:r._=b,b.VERSION="1.7.0",b.iteratee=function(n,t,r){return null==n?b.identity:b.isFunction(n)?c(n,t,r):b.isObject(n)?b.matches(n):b.property(n)},b.each=b.forEach=function(n,t,r){if(null==n)return n;if(t=c(t,r),(i=n.length)===+i)for(u=0;u<i;u++)t(n[u],u,n);else for(var e=b.keys(n),u=0,i=e.length;u<i;u++)t(n[e[u]],e[u],n);return n},b.map=b.collect=function(n,t,r){if(null==n)return[];t=b.iteratee(t,r);for(var e,u=n.length!==+n.length&&b.keys(n),i=(u||n).length,o=Array(i),l=0;l<i;l++)e=u?u[l]:l,o[l]=t(n[e],e,n);return o},"Reduce of empty array with no initial value"),w=(b.reduce=b.foldl=b.inject=function(n,t,r,e){null==n&&(n=[]),t=c(t,e,4);var u,i=n.length!==+n.length&&b.keys(n),o=(i||n).length,l=0;if(arguments.length<3){if(!o)throw new TypeError(_);r=n[i?i[l++]:l++]}for(;l<o;l++)u=i?i[l]:l,r=t(r,n[u],u,n);return r},b.reduceRight=b.foldr=function(n,t,r,e){null==n&&(n=[]),t=c(t,e,4);var u,i=n.length!==+n.length&&b.keys(n),o=(i||n).length;if(arguments.length<3){if(!o)throw new TypeError(_);r=n[i?i[--o]:--o]}for(;o--;)u=i?i[o]:o,r=t(r,n[u],u,n);return r},b.find=b.detect=function(n,e,t){var u;return e=b.iteratee(e,t),b.some(n,function(n,t,r){if(e(n,t,r))return u=n,!0}),u},b.filter=b.select=function(n,e,t){var u=[];return null==n||(e=b.iteratee(e,t),b.each(n,function(n,t,r){e(n,t,r)&&u.push(n)})),u},b.reject=function(n,t,r){return b.filter(n,b.negate(b.iteratee(t)),r)},b.every=b.all=function(n,t,r){if(null==n)return!0;t=b.iteratee(t,r);for(var e,u=n.length!==+n.length&&b.keys(n),i=(u||n).length,o=0;o<i;o++)if(!t(n[e=u?u[o]:o],e,n))return!1;return!0},b.some=b.any=function(n,t,r){if(null==n)return!1;t=b.iteratee(t,r);for(var e,u=n.length!==+n.length&&b.keys(n),i=(u||n).length,o=0;o<i;o++)if(t(n[e=u?u[o]:o],e,n))return!0;return!1},b.contains=b.include=function(n,t){return null!=n&&(n.length!==+n.length&&(n=b.values(n)),0<=b.indexOf(n,t))},b.invoke=function(n,t){var r=h.call(arguments,2),e=b.isFunction(t);return b.map(n,function(n){return(e?t:n[t]).apply(n,r)})},b.pluck=function(n,t){return b.map(n,b.property(t))},b.where=function(n,t){return b.filter(n,b.matches(t))},b.findWhere=function(n,t){return b.find(n,b.matches(t))},b.max=function(n,e,t){var r,u,i=-1/0,o=-1/0;if(null==e&&null!=n)for(var l=0,a=(n=n.length===+n.length?n:b.values(n)).length;l<a;l++)r=n[l],i<r&&(i=r);else e=b.iteratee(e,t),b.each(n,function(n,t,r){u=e(n,t,r),(o<u||u===-1/0&&i===-1/0)&&(i=n,o=u)});return i},b.min=function(n,e,t){var r,u,i=1/0,o=1/0;if(null==e&&null!=n)for(var l=0,a=(n=n.length===+n.length?n:b.values(n)).length;l<a;l++)(r=n[l])<i&&(i=r);else e=b.iteratee(e,t),b.each(n,function(n,t,r){((u=e(n,t,r))<o||u===1/0&&i===1/0)&&(i=n,o=u)});return i},b.shuffle=function(n){for(var t,r=n&&n.length===+n.length?n:b.values(n),e=r.length,u=Array(e),i=0;i<e;i++)(t=b.random(0,i))!==i&&(u[i]=u[t]),u[t]=r[i];return u},b.sample=function(n,t,r){return null==t||r?(n=n.length!==+n.length?b.values(n):n)[b.random(n.length-1)]:b.shuffle(n).slice(0,Math.max(0,t))},b.sortBy=function(n,e,t){return e=b.iteratee(e,t),b.pluck(b.map(n,function(n,t,r){return{value:n,index:t,criteria:e(n,t,r)}}).sort(function(n,t){var r=n.criteria,e=t.criteria;if(r!==e){if(e<r||void 0===r)return 1;if(r<e||void 0===e)return-1}return n.index-t.index}),"value")},b.groupBy=n(function(n,t,r){b.has(n,r)?n[r].push(t):n[r]=[t]}),b.indexBy=n(function(n,t,r){n[r]=t}),b.countBy=n(function(n,t,r){b.has(n,r)?n[r]++:n[r]=1}),b.sortedIndex=function(n,t,r,e){for(var u=(r=b.iteratee(r,e,1))(t),i=0,o=n.length;i<o;){var l=i+o>>>1;r(n[l])<u?i=1+l:o=l}return i},b.toArray=function(n){return n?b.isArray(n)?h.call(n):n.length===+n.length?b.map(n,b.identity):b.values(n):[]},b.size=function(n){return null==n?0:(n.length===+n.length?n:b.keys(n)).length},b.partition=function(n,e,t){e=b.iteratee(e,t);var u=[],i=[];return b.each(n,function(n,t,r){(e(n,t,r)?u:i).push(n)}),[u,i]},b.first=b.head=b.take=function(n,t,r){if(null!=n)return null==t||r?n[0]:t<0?[]:h.call(n,0,t)},b.initial=function(n,t,r){return h.call(n,0,Math.max(0,n.length-(null==t||r?1:t)))},b.last=function(n,t,r){if(null!=n)return null==t||r?n[n.length-1]:h.call(n,Math.max(n.length-t,0))},b.rest=b.tail=b.drop=function(n,t,r){return h.call(n,null==t||r?1:t)},b.compact=function(n){return b.filter(n,b.identity)},b.flatten=function(n,t){return l(n,t,!1,[])},b.without=function(n){return b.difference(n,h.call(arguments,1))},b.uniq=b.unique=function(n,t,r,e){if(null==n)return[];b.isBoolean(t)||(e=r,r=t,t=!1),null!=r&&(r=b.iteratee(r,e));for(var u=[],i=[],o=0,l=n.length;o<l;o++){var a,c=n[o];t?(o&&i===c||u.push(c),i=c):r?(a=r(c,o,n),b.indexOf(i,a)<0&&(i.push(a),u.push(c))):b.indexOf(u,c)<0&&u.push(c)}return u},b.union=function(){return b.uniq(l(arguments,!0,!0,[]))},b.intersection=function(n){if(null==n)return[];for(var t=[],r=arguments.length,e=0,u=n.length;e<u;e++){var i=n[e];if(!b.contains(t,i)){for(var o=1;o<r&&b.contains(arguments[o],i);o++);o===r&&t.push(i)}}return t},b.difference=function(n){var t=l(h.call(arguments,1),!0,!0,[]);return b.filter(n,function(n){return!b.contains(t,n)})},b.zip=function(n){if(null==n)return[];for(var t=b.max(arguments,"length").length,r=Array(t),e=0;e<t;e++)r[e]=b.pluck(arguments,e);return r},b.object=function(n,t){if(null==n)return{};for(var r={},e=0,u=n.length;e<u;e++)t?r[n[e]]=t[e]:r[n[e][0]]=n[e][1];return r},b.indexOf=function(n,t,r){if(null==n)return-1;var e=0,u=n.length;if(r){if("number"!=typeof r)return n[e=b.sortedIndex(n,t)]===t?e:-1;e=r<0?Math.max(0,u+r):r}for(;e<u;e++)if(n[e]===t)return e;return-1},b.lastIndexOf=function(n,t,r){if(null==n)return-1;var e=n.length;for("number"==typeof r&&(e=r<0?e+r+1:Math.min(e,r+1));0<=--e;)if(n[e]===t)return e;return-1},b.range=function(n,t,r){arguments.length<=1&&(t=n||0,n=0),r=r||1;for(var e=Math.max(Math.ceil((t-n)/r),0),u=Array(e),i=0;i<e;i++,n+=r)u[i]=n;return u},b.bind=function(r,e){var u,i;if(m&&r.bind===m)return m.apply(r,h.call(arguments,1));if(b.isFunction(r))return u=h.call(arguments,2),i=function(){if(!(this instanceof i))return r.apply(e,u.concat(h.call(arguments)));o.prototype=r.prototype;var n=new o,t=(o.prototype=null,r.apply(n,u.concat(h.call(arguments))));return b.isObject(t)?t:n};throw new TypeError("Bind must be called on a function")},b.partial=function(u){var i=h.call(arguments,1);return function(){for(var n=0,t=i.slice(),r=0,e=t.length;r<e;r++)t[r]===b&&(t[r]=arguments[n++]);for(;n<arguments.length;)t.push(arguments[n++]);return u.apply(this,t)}},b.bindAll=function(n){var t,r,e=arguments.length;if(e<=1)throw new Error("bindAll must be passed function names");for(t=1;t<e;t++)n[r=arguments[t]]=b.bind(n[r],n);return n},b.memoize=function(e,u){function i(n){var t=i.cache,r=u?u.apply(this,arguments):n;return b.has(t,r)||(t[r]=e.apply(this,arguments)),t[r]}return i.cache={},i},b.delay=function(n,t){var r=h.call(arguments,2);return setTimeout(function(){return n.apply(null,r)},t)},b.defer=function(n){return b.delay.apply(b,[n,1].concat(h.call(arguments,1)))},b.throttle=function(r,e,u){function i(){f=!1===u.leading?0:b.now(),c=null,a=r.apply(o,l),c||(o=l=null)}var o,l,a,c=null,f=0;u=u||{};return function(){var n=b.now(),t=(f||!1!==u.leading||(f=n),e-(n-f));return o=this,l=arguments,t<=0||e<t?(clearTimeout(c),c=null,f=n,a=r.apply(o,l),c||(o=l=null)):c||!1===u.trailing||(c=setTimeout(i,t)),a}},b.debounce=function(t,r,e){function u(){var n=b.now()-a;n<r&&0<n?i=setTimeout(u,r-n):(i=null,e||(c=t.apply(l,o),i||(l=o=null)))}var i,o,l,a,c;return function(){l=this,o=arguments,a=b.now();var n=e&&!i;return i=i||setTimeout(u,r),n&&(c=t.apply(l,o),l=o=null),c}},b.wrap=function(n,t){return b.partial(t,n)},b.negate=function(n){return function(){return!n.apply(this,arguments)}},b.compose=function(){var r=arguments,e=r.length-1;return function(){for(var n=e,t=r[e].apply(this,arguments);n--;)t=r[n].call(this,t);return t}},b.after=function(n,t){return function(){if(--n<1)return t.apply(this,arguments)}},b.before=function(n,t){var r;return function(){return 0<--n?r=t.apply(this,arguments):t=null,r}},b.once=b.partial(b.before,2),b.keys=function(n){if(!b.isObject(n))return[];if(d)return d(n);var t,r=[];for(t in n)b.has(n,t)&&r.push(t);return r},b.values=function(n){for(var t=b.keys(n),r=t.length,e=Array(r),u=0;u<r;u++)e[u]=n[t[u]];return e},b.pairs=function(n){for(var t=b.keys(n),r=t.length,e=Array(r),u=0;u<r;u++)e[u]=[t[u],n[t[u]]];return e},b.invert=function(n){for(var t={},r=b.keys(n),e=0,u=r.length;e<u;e++)t[n[r[e]]]=r[e];return t},b.functions=b.methods=function(n){var t,r=[];for(t in n)b.isFunction(n[t])&&r.push(t);return r.sort()},b.extend=function(n){if(!b.isObject(n))return n;for(var t,r,e=1,u=arguments.length;e<u;e++)for(r in t=arguments[e])y.call(t,r)&&(n[r]=t[r]);return n},b.pick=function(n,t,r){var e,u={};if(null==n)return u;if(b.isFunction(t))for(e in t=c(t,r),n){var i=n[e];t(i,e,n)&&(u[e]=i)}else{var o=v.apply([],h.call(arguments,1));n=new Object(n);for(var l=0,a=o.length;l<a;l++)(e=o[l])in n&&(u[e]=n[e])}return u},b.omit=function(n,t,r){var e;return t=b.isFunction(t)?b.negate(t):(e=b.map(v.apply([],h.call(arguments,1)),String),function(n,t){return!b.contains(e,t)}),b.pick(n,t,r)},b.defaults=function(n){if(!b.isObject(n))return n;for(var t=1,r=arguments.length;t<r;t++){var e,u=arguments[t];for(e in u)void 0===n[e]&&(n[e]=u[e])}return n},b.clone=function(n){return b.isObject(n)?b.isArray(n)?n.slice():b.extend({},n):n},b.tap=function(n,t){return t(n),n},function(n,t,r,e){if(n===t)return 0!==n||1/n==1/t;if(null==n||null==t)return n===t;n instanceof b&&(n=n._wrapped),t instanceof b&&(t=t._wrapped);var u=g.call(n);if(u!==g.call(t))return!1;switch(u){case"[object RegExp]":case"[object String]":return""+n==""+t;case"[object Number]":return+n!=+n?+t!=+t:0==+n?1/+n==1/t:+n==+t;case"[object Date]":case"[object Boolean]":return+n==+t}if("object"!=typeof n||"object"!=typeof t)return!1;for(var i=r.length;i--;)if(r[i]===n)return e[i]===t;var o=n.constructor,l=t.constructor;if(o!==l&&"constructor"in n&&"constructor"in t&&!(b.isFunction(o)&&o instanceof o&&b.isFunction(l)&&l instanceof l))return!1;if(r.push(n),e.push(t),"[object Array]"===u){if(c=(s=n.length)===t.length)for(;s--&&(c=w(n[s],t[s],r,e)););}else{var a,c,f=b.keys(n),s=f.length;if(c=b.keys(t).length===s)for(;s--&&(a=f[s],c=b.has(t,a)&&w(n[a],t[a],r,e)););}return r.pop(),e.pop(),c}),s=(b.isEqual=function(n,t){return w(n,t,[],[])},b.isEmpty=function(n){if(null==n)return!0;if(b.isArray(n)||b.isString(n)||b.isArguments(n))return 0===n.length;for(var t in n)if(b.has(n,t))return!1;return!0},b.isElement=function(n){return!(!n||1!==n.nodeType)},b.isArray=f||function(n){return"[object Array]"===g.call(n)},b.isObject=function(n){var t=typeof n;return"function"==t||"object"==t&&!!n},b.each(["Arguments","Function","String","Number","Date","RegExp"],function(t){b["is"+t]=function(n){return g.call(n)==="[object "+t+"]"}}),b.isArguments(arguments)||(b.isArguments=function(n){return b.has(n,"callee")}),"function"!=typeof/./&&(b.isFunction=function(n){return"function"==typeof n||!1}),b.isFinite=function(n){return isFinite(n)&&!isNaN(parseFloat(n))},b.isNaN=function(n){return b.isNumber(n)&&n!==+n},b.isBoolean=function(n){return!0===n||!1===n||"[object Boolean]"===g.call(n)},b.isNull=function(n){return null===n},b.isUndefined=function(n){return void 0===n},b.has=function(n,t){return null!=n&&y.call(n,t)},b.noConflict=function(){return r._=u,this},b.identity=function(n){return n},b.constant=function(n){return function(){return n}},b.noop=function(){},b.property=function(t){return function(n){return n[t]}},b.matches=function(n){var u=b.pairs(n),i=u.length;return function(n){if(null==n)return!i;n=new Object(n);for(var t=0;t<i;t++){var r=u[t],e=r[0];if(r[1]!==n[e]||!(e in n))return!1}return!0}},b.times=function(n,t,r){var e=Array(Math.max(0,n));t=c(t,r,1);for(var u=0;u<n;u++)e[u]=t(u);return e},b.random=function(n,t){return null==t&&(t=n,n=0),n+Math.floor(Math.random()*(t-n+1))},b.now=Date.now||function(){return(new Date).getTime()},{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#x27;","`":"&#x60;"}),f=b.invert(s),x=(b.escape=t(s),b.unescape=t(f),b.result=function(n,t){var r;if(null!=n)return r=n[t],b.isFunction(r)?n[t]():r},0),j=(b.uniqueId=function(n){var t=++x+"";return n?n+t:t},b.templateSettings={evaluate:/<%([\s\S]+?)%>/g,interpolate:/<%=([\s\S]+?)%>/g,escape:/<%-([\s\S]+?)%>/g},/(.)^/),A={"'":"'","\\":"\\","\r":"r","\n":"n","\u2028":"u2028","\u2029":"u2029"},k=/\\|'|\r|\n|\u2028|\u2029/g;b.template=function(i,n,t){n=b.defaults({},n=!n&&t?t:n,b.templateSettings);var t=RegExp([(n.escape||j).source,(n.interpolate||j).source,(n.evaluate||j).source].join("|")+"|$","g"),o=0,l="__p+='";i.replace(t,function(n,t,r,e,u){return l+=i.slice(o,u).replace(k,a),o=u+n.length,t?l+="'+\n((__t=("+t+"))==null?'':_.escape(__t))+\n'":r?l+="'+\n((__t=("+r+"))==null?'':__t)+\n'":e&&(l+="';\n"+e+"\n__p+='"),n}),l+="';\n",l="var __t,__p='',__j=Array.prototype.join,print=function(){__p+=__j.call(arguments,'');};\n"+(l=n.variable?l:"with(obj||{}){\n"+l+"}\n")+"return __p;\n";try{var r=new Function(n.variable||"obj","_",l)}catch(n){throw n.source=l,n}function e(n){return r.call(this,n,b)}t=n.variable||"obj";return e.source="function("+t+"){\n"+l+"}",e},b.chain=function(n){n=b(n);return n._chain=!0,n};b.mixin=function(r){b.each(b.functions(r),function(n){var t=b[n]=r[n];b.prototype[n]=function(){var n=[this._wrapped];return p.apply(n,arguments),e.call(this,t.apply(b,n))}})},b.mixin(b),b.each(["pop","push","reverse","shift","sort","splice","unshift"],function(t){var r=i[t];b.prototype[t]=function(){var n=this._wrapped;return r.apply(n,arguments),"shift"!==t&&"splice"!==t||0!==n.length||delete n[0],e.call(this,n)}}),b.each(["concat","join","slice"],function(n){var t=i[n];b.prototype[n]=function(){return e.call(this,t.apply(this._wrapped,arguments))}}),b.prototype.value=function(){return this._wrapped},"function"==typeof define&&define.amd&&define("underscore",[],function(){return b})}.call(this)},{}]},{},[]);
