!function i(o,a,r){function s(t,e){if(!a[t]){if(!o[t]){var n="function"==typeof require&&require;if(!e&&n)return n(t,!0);if(d)return d(t,!0);throw(e=new Error("Cannot find module '"+t+"'")).code="MODULE_NOT_FOUND",e}n=a[t]={exports:{}},o[t][0].call(n.exports,function(e){return s(o[t][1][e]||e)},n,n.exports,i,o,a,r)}return a[t].exports}for(var d="function"==typeof require&&require,e=0;e<r.length;e++)s(r[e]);return s}({1:[function(e,t,n){var i="undefined"!=typeof window?window.jQuery:e("jquery");t.exports.ThemeNav={navBar:null,win:null,winScroll:!1,winResize:!1,linkScroll:!1,winPosition:0,winHeight:null,docHeight:null,isRunning:!1,enable:function(t){var n=this;"undefined"==typeof withStickNav&&(t=!0),n.isRunning||(n.isRunning=!0,i(function(e){n.init(e),n.reset(),n.win.on("hashchange",n.reset),t&&n.win.on("scroll",function(){n.linkScroll||n.winScroll||(n.winScroll=!0,requestAnimationFrame(function(){n.onScroll()}))}),n.win.on("resize",function(){n.winResize||(n.winResize=!0,requestAnimationFrame(function(){n.onResize()}))}),n.onResize()}))},enableSticky:function(){this.enable(!0)},init:function(n){n(document);var i=this;this.navBar=n("div.wy-side-scroll:first"),this.win=n(window),n(document).on("click","[data-toggle='wy-nav-top']",function(){n("[data-toggle='wy-nav-shift']").toggleClass("shift"),n("[data-toggle='rst-versions']").toggleClass("shift")}).on("click",".wy-menu-vertical .current ul li a",function(){var e=n(this);n("[data-toggle='wy-nav-shift']").removeClass("shift"),n("[data-toggle='rst-versions']").toggleClass("shift"),i.toggleCurrent(e),i.hashChange()}).on("click","[data-toggle='rst-current-version']",function(){n("[data-toggle='rst-versions']").toggleClass("shift-up")}),n("table.docutils:not(.field-list,.footnote,.citation)").wrap("<div class='wy-table-responsive'></div>"),n("table.docutils.footnote").wrap("<div class='wy-table-responsive footnote'></div>"),n("table.docutils.citation").wrap("<div class='wy-table-responsive citation'></div>"),n(".wy-menu-vertical ul").not(".simple").siblings("a").each(function(){var t=n(this);(expand=n('<span class="toctree-expand"></span>')).on("click",function(e){return i.toggleCurrent(t),e.stopPropagation(),!1}),t.prepend(expand)})},reset:function(){var e=encodeURI(window.location.hash)||"#";try{var t,n=$(".wy-menu-vertical"),i=n.find('[href="'+e+'"]');0===i.length&&(t=$('.document [id="'+e.substring(1)+'"]').closest("div.section"),0===(i=n.find('[href="#'+t.attr("id")+'"]')).length&&(i=n.find('[href="#"]'))),0<i.length&&($(".wy-menu-vertical .current").removeClass("current"),i.addClass("current"),i.closest("li.toctree-l1").addClass("current"),i.closest("li.toctree-l1").parent().addClass("current"),i.closest("li.toctree-l1").addClass("current"),i.closest("li.toctree-l2").addClass("current"),i.closest("li.toctree-l3").addClass("current"),i.closest("li.toctree-l4").addClass("current"))}catch(e){console.log("Error expanding nav for anchor",e)}},onScroll:function(){this.winScroll=!1;var e=this.win.scrollTop(),t=e+this.winHeight,n=this.navBar.scrollTop()+(e-this.winPosition);e<0||t>this.docHeight||(this.navBar.scrollTop(n),this.winPosition=e)},onResize:function(){this.winResize=!1,this.winHeight=this.win.height(),this.docHeight=$(document).height()},hashChange:function(){this.linkScroll=!0,this.win.one("hashchange",function(){this.linkScroll=!1})},toggleCurrent:function(e){e=e.closest("li");e.siblings("li.current").removeClass("current"),e.siblings().find("li.current").removeClass("current"),e.find("> ul li.current").removeClass("current"),e.toggleClass("current")}},"undefined"!=typeof window&&(window.SphinxRtdTheme={Navigation:t.exports.ThemeNav,StickyNav:t.exports.ThemeNav});for(var a=0,o=["ms","moz","webkit","o"],r=0;r<o.length&&!window.requestAnimationFrame;++r)window.requestAnimationFrame=window[o[r]+"RequestAnimationFrame"],window.cancelAnimationFrame=window[o[r]+"CancelAnimationFrame"]||window[o[r]+"CancelRequestAnimationFrame"];window.requestAnimationFrame||(window.requestAnimationFrame=function(e,t){var n=(new Date).getTime(),i=Math.max(0,16-(n-a)),o=window.setTimeout(function(){e(n+i)},i);return a=n+i,o}),window.cancelAnimationFrame||(window.cancelAnimationFrame=function(e){clearTimeout(e)})},{jquery:"jquery"}],2:[function(e,t,n){(n={THEME_RTD:"sphinx_rtd_theme",THEME_ALABASTER:"alabaster",THEME_MKDOCS_RTD:"readthedocs",THEME_CELERY:"sphinx_celery",THEME_BABEL:"babel",THEME_CLICK:"click",THEME_FLASK_SQLALCHEMY:"flask-sqlalchemy",THEME_FLASK:"flask",THEME_JINJA:"jinja",THEME_PLATTER:"platter",THEME_POCOO:"pocoo",THEME_WERKZEUG:"werkzeug",DEFAULT_PROMO_PRIORITY:5,MINIMUM_PROMO_PRIORITY:10,MAXIMUM_PROMO_PRIORITY:1,LOW_PROMO_PRIORITY:10}).ALABASTER_LIKE_THEMES=[n.THEME_ALABASTER,n.THEME_CELERY,n.THEME_BABEL,n.THEME_CLICK,n.THEME_FLASK_SQLALCHEMY,n.THEME_FLASK,n.THEME_JINJA,n.THEME_PLATTER,n.THEME_POCOO,n.THEME_WERKZEUG],n.PROMO_TYPES={LEFTNAV:"doc",FOOTER:"site-footer",FIXED_FOOTER:"fixed-footer"},t.exports=n},{}],3:[function(e,t,n){var o=e("./rtd-data"),a=e("./version-compare"),r="#readthedocs-embed-flyout";t.exports={init:function(){var e={project:(t=o.get()).project,version:t.version,page:t.page||"",theme:t.get_theme_name()},e=("docroot"in t&&(e.docroot=t.docroot),"source_suffix"in t&&(e.source_suffix=t.source_suffix),0===window.location.pathname.indexOf("/projects/")&&(e.subproject=!0),t.proxied_api_host+"/api/v2/footer_html/?"+new URLSearchParams(e).toString()),e=(fetch(e,{method:"GET"}).then(e=>{if(e.ok)return e.json();throw new Error}).then(t=>{t.show_version_warning&&a.init(t.version_compare);{var n=o.get();let e=document.querySelector(r);if(null!==e)e.innerHTML=t.html;else if(n.is_sphinx_builder()&&n.is_rtd_like_theme()){let e=document.querySelector("div.rst-other-versions");null!==e&&(e.innerHTML=t.html)}else document.body.insertAdjacentHTML("beforeend",t.html);if(t.version_active)t.version_supported;else for(var i of document.getElementsByClassName("rst-current-version"))i.classList.add("rst-out-of-date");return}}).catch(e=>{console.error("Error loading Read the Docs footer")}),{project:t.project,version:t.version,absolute_uri:window.location.href}),t=t.proxied_api_host+"/api/v2/analytics/?"+new URLSearchParams(e).toString();fetch(t,{method:"GET",cache:"no-store"}).then(e=>{if(!e.ok)throw new Error}).catch(e=>{console.error("Error registering page view")})}}},{"./rtd-data":4,"./version-compare":9}],4:[function(e,t,n){var i=e("./constants"),o={is_rtd_like_theme:function(){return 1===document.querySelectorAll("div.rst-other-versions").length||(this.theme===i.THEME_RTD||this.theme===i.THEME_MKDOCS_RTD)},is_alabaster_like_theme:function(){return-1<i.ALABASTER_LIKE_THEMES.indexOf(this.get_theme_name())},is_sphinx_builder:function(){return!("builder"in this)||"mkdocs"!==this.builder},is_mkdocs_builder:function(){return"builder"in this&&"mkdocs"===this.builder},get_theme_name:function(){return this.theme},show_promo:function(){return("https://readthedocs.org"===this.api_host||"http://devthedocs.org"===this.api_host||"http://127.0.0.1:8000"===this.api_host)&&!0!==this.ad_free}};t.exports={get:function(){var e=Object.create(o);return Object.assign(e,{api_host:"https://readthedocs.org",ad_free:!1,proxied_static_path:"/_/static/"},window.READTHEDOCS_DATA),"proxied_api_host"in e||(e.proxied_api_host="/_"),e}}},{"./constants":2}],5:[function(e,t,n){const i=e("./rtd-data"),{createDomNode:y,domReady:s}=e("./utils"),b=3,T=100;function o(e){this.value=e,this.isSafe=!0}function S(e){return new o(e)}function x(e,t){t.isSafe?e.innerHTML=t.value:e.innerText=t}function a(o){function e(v){var e=document.createElement("a"),n=(e.href=o.proxied_api_host+"/api/v2/search/",e.search="?q="+encodeURIComponent(v)+"&project="+E+"&version="+a+"&language="+r,function(e,t){e.jquery?e.text(t):e.innerText=t});function w(){let e=document.getElementById("search-progress");null!==e&&e.replaceChildren(),Search.stopPulse(),n(Search.title,_("Search Results"))}function t(e){var t=e.results||[];if(t.length){for(var i=0;i<t.length;i+=1){var o=t[i],a=o.blocks;let n=y("li");var r,s=o.title,d=(o.highlights.title.length&&(s=S(o.highlights.title[0])),o.path+"?highlight="+encodeURIComponent(v));let e=y("a",{href:d});x(e,s);for(r of e.getElementsByTagName("span"))r.className="highlighted";if(n.appendChild(e),o.project!==E){let e=y("span");e.innerText=" (from project "+o.project_alias+")",n.appendChild(e)}for(var l=0;l<a.length;l+=1){var c,h=a[l];let t=y("div",{class:"context"});if("section"===h.type){var u=h.title,p=d+"#"+h.id,f=[h.content.substr(0,T)+" ..."];if(h.highlights.title.length&&(u=S(h.highlights.title[0])),h.highlights.content.length)for(var m=h.highlights.content,f=[],g=0;g<m.length&&g<b;g+=1)f.push(S("... "+m[g]+" ..."));let e=function(e,t,n){var i,o=document.createElement("div"),a=document.createElement("a");a.href=t,x(a,e),o.appendChild(a);let r=[o];for(i of n){var s=document.createElement("div");x(s,i),r.push(s)}return r}(u,p,f);e.forEach(e=>{t.appendChild(e)})}for(c of t.getElementsByTagName("span"))c.className="highlighted";n.appendChild(t),l<a.length-1&&n.appendChild(y("div",{class:"rtd_search_hits_spacing"}))}Search.output.jquery?Search.output.append($(n)):Search.output.appendChild(n)}n(Search.status,_("Search finished, found %s page(s) matching the search query.").replace("%s",t.length))}else console.log("Read the Docs search failed. Falling back to Sphinx search."),Search.query_fallback(v);w()}function i(){console.debug("Read the Docs search failed. Falling back to Sphinx search."),Search.query_fallback(v),w()}fetch(e.href,{method:"GET"}).then(e=>{if(e.ok)return e.json();throw new Error}).then(e=>{0<e.results.length?t(e):i()}).catch(e=>{i()})}var t,E=o.project,a=o.version,r=o.language||"en";"undefined"!=typeof Search&&E&&a&&(o.features&&o.features.docsearch_disabled?console.log("Server side search is disabled."):(t=Search.query,Search.query_fallback=t,Search.query=e)),s(function(){"undefined"!=typeof Search&&Search.init()})}t.exports={init:function(){var e=i.get();e.is_sphinx_builder()?a(e):console.log("Server side search is disabled.")}}},{"./rtd-data":4,"./utils":8}],6:[function(i,e,t){const o=i("./rtd-data"),a=i("./utils")["domReady"];e.exports={init:function(){var e,t=o.get(),n=document.querySelector("[data-toggle='rst-current-version']");null!=n&&n.addEventListener("click",function(){var e=$("[data-toggle='rst-versions']").hasClass("shift-up")?"was_open":"was_closed";"undefined"!=typeof READTHEDOCS_DATA&&READTHEDOCS_DATA.global_analytics_code&&("undefined"!=typeof gtag?gtag("event","Click",{event_category:"Flyout",event_label:e,send_to:"rtfd"}):"undefined"!=typeof ga?ga("rtfd.send","event","Flyout","Click",e):"undefined"!=typeof _gaq&&_gaq.push(["rtfd._setAccount","UA-17997319-1"],["rtfd._trackEvent","Flyout","Click",e]))}),void 0===window.SphinxRtdTheme&&(e=i("./../../../../../../bower_components/sphinx-rtd-theme/js/theme.js").ThemeNav,a(function(){setTimeout(function(){e.navBar||e.enable()},1e3)}),t.is_rtd_like_theme()&&!$("div.wy-side-scroll:first").length&&(console.log("Applying theme sidebar fix..."),n=$("nav.wy-nav-side:first"),t=$("<div />").addClass("wy-side-scroll"),n.children().detach().appendTo(t),t.prependTo(n),e.navBar=t))}}},{"./../../../../../../bower_components/sphinx-rtd-theme/js/theme.js":1,"./rtd-data":4,"./utils":8}],7:[function(e,t,n){e("./constants");var s,d=e("./rtd-data"),l="[data-ea-publisher]",c="#ethical-ad-placement";function h(){var e=!1;return $("<div />").attr("id","rtd-detection").attr("class","ethical-rtd").html("&nbsp;").appendTo("body"),0===$("#rtd-detection").height()&&(e=!0),$("#rtd-detection").remove(),e}function u(){console.log("---------------------------------------------------------------------------------------"),console.log("Read the Docs hosts documentation for tens of thousands of open source projects."),console.log("We fund our development (we are open source) and operations through advertising."),console.log("We promise to:"),console.log(" - never let advertisers run 3rd party JavaScript"),console.log(" - never sell user data to advertisers or other 3rd parties"),console.log(" - only show advertisements of interest to developers"),console.log("Read more about our approach to advertising here: https://docs.readthedocs.io/en/latest/advertising/ethical-advertising.html"),console.log("%cPlease allow our Ethical Ads or go ad-free:","font-size: 2em"),console.log("https://docs.readthedocs.io/en/latest/advertising/ad-blocking.html"),console.log("--------------------------------------------------------------------------------------")}function p(e){e&&(e=e.attr("class","keep-us-sustainable"),$("<p />").text("Support Read the Docs!").appendTo(e),$("<p />").html('Please help keep us sustainable by <a href="https://docs.readthedocs.io/en/latest/advertising/ad-blocking.html#allowing-ethical-ads">allowing our Ethical Ads in your ad blocker</a> or <a href="https://readthedocs.org/sustainability/">go ad-free</a> by subscribing.').appendTo(e),$("<p />").text("Thank you! ❤️").appendTo(e))}t.exports={init:function(){var t,e,n,i,o,a,r;(s=d.get()).show_promo()&&(o=null,a="readthedocs-sidebar",t=0<$(l).length?($(l).attr("data-ea-publisher","readthedocs"),$(l).attr("data-ea-manual","true"),"image"!==$(l).attr("data-ea-type")&&"text"!==$(l).attr("data-ea-type")&&$(l).attr("data-ea-type","readthedocs-sidebar"),$(l)):(0<$(c).length?(o=c,e=s.is_rtd_like_theme()?"ethical-rtd ethical-dark-theme":"ethical-alabaster"):s.is_mkdocs_builder()&&s.is_rtd_like_theme()?(o="nav.wy-nav-side",e="ethical-rtd ethical-dark-theme"):s.is_rtd_like_theme()?(o="nav.wy-nav-side > div.wy-side-scroll",e="ethical-rtd ethical-dark-theme"):s.is_alabaster_like_theme()&&(o="div.sphinxsidebar > div.sphinxsidebarwrapper",e="ethical-alabaster"),o?((!(r=(i=$("<div />").appendTo(o)).offset())||r.top-window.scrollY+200>window.innerHeight)&&(s.is_rtd_like_theme()?(o=$("<div />").insertAfter("footer hr"),e="ethical-rtd",Math.random()<=.25&&(n="stickybox",a="image")):s.is_alabaster_like_theme()&&(o="div.bodywrapper .body",e="ethical-alabaster")),i.remove(),$("<div />").attr("id","rtd-sidebar").attr("data-ea-publisher","readthedocs").attr("data-ea-type",a).attr("data-ea-manual","true").attr("data-ea-style",n).addClass(e).appendTo(o)):null),(r=document.createElement("script")).src="https://media.ethicalads.io/media/client/beta/ethicalads.min.js",r.type="text/javascript",r.async=!0,r.id="ethicaladsjs",document.getElementsByTagName("head")[0].appendChild(r),$.ajax({url:s.api_host+"/api/v2/sustainability/data/",crossDomain:!0,xhrFields:{withCredentials:!0},dataType:"jsonp",data:{format:"jsonp",project:s.project},success:function(e){t&&!e.ad_free&&(e.keywords&&t.attr("data-ea-keywords",e.keywords.join("|")),e.campaign_types&&t.attr("data-ea-campaign-types",e.campaign_types.join("|")),e.publisher&&t.attr("data-ea-publisher",e.publisher),"undefined"!=typeof ethicalads?ethicalads.load():!s.ad_free&&h()?(u(),p(t)):document.getElementById("ethicaladsjs").addEventListener("load",function(){"undefined"!=typeof ethicalads&&ethicalads.load()}))},error:function(){console.error("Error loading Read the Docs user and project information"),!s.ad_free&&h()&&(u(),p(t))}}))}}},{"./constants":2,"./rtd-data":4}],8:[function(e,t,n){t.exports={createDomNode:function(e,t){let n=document.createElement(e);if(t)for(var i of Object.keys(t))n.setAttribute(i,t[i]);return n},domReady:function(e){"complete"===document.readyState||"interactive"===document.readyState?setTimeout(e,1):document.addEventListener("DOMContentLoaded",e)}}},{}],9:[function(e,t,n){const a=e("./rtd-data"),r=e("./utils")["createDomNode"];t.exports={init:function(n){var i,o=a.get();if(!n.is_highest){o=window.location.pathname.replace(o.version,n.slug);let t=r("div",{class:"admonition warning"}),e=r("a",{href:o});e.innerText=n.slug,t.innerHTML='<p class="first admonition-title">Note</p> <p class="last"> You are not reading the most recent version of this documentation. '+e.outerHTML+" is the latest version available.</p>";for(i of["[role=main]","main","div.body","div.document"]){let e=document.querySelector(i);if(null!==e){e.prepend(t);break}}}}}},{"./rtd-data":4,"./utils":8}],10:[function(i,e,t){const o=i("./doc-embed/sponsorship"),a=i("./doc-embed/footer.js"),r=i("./doc-embed/sphinx"),s=i("./doc-embed/search"),n=i("./doc-embed/utils")["domReady"],d=i("./doc-embed/rtd-data");n(function(){var t=function(){a.init(),r.init(),s.init(),o.init()};if(window.jQuery)t();else{console.debug("JQuery not found. Injecting.");var n=d.get();let e=document.createElement("script");e.type="text/javascript",e.src=n.proxied_static_path+"vendor/jquery.js",e.onload=function(){window.$=i("jquery"),window.jQuery=window.$,t()},document.head.appendChild(e)}})},{"./doc-embed/footer.js":3,"./doc-embed/rtd-data":4,"./doc-embed/search":5,"./doc-embed/sphinx":6,"./doc-embed/sponsorship":7,"./doc-embed/utils":8,jquery:"jquery"}]},{},[10]);
