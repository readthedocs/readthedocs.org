(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);throw new Error("Cannot find module '"+o+"'")}var f=n[o]={exports:{}};t[o][0].call(f.exports,function(e){var n=t[o][1][e];return s(n?n:e)},f,f.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
/*!
Waypoints - 3.1.1
Copyright © 2011-2015 Caleb Troughton
Licensed under the MIT license.
https://github.com/imakewebthings/waypoints/blog/master/licenses.txt
*/
!function(){"use strict";function t(n){if(!n)throw new Error("No options passed to Waypoint constructor");if(!n.element)throw new Error("No element option passed to Waypoint constructor");if(!n.handler)throw new Error("No handler option passed to Waypoint constructor");this.key="waypoint-"+e,this.options=t.Adapter.extend({},t.defaults,n),this.element=this.options.element,this.adapter=new t.Adapter(this.element),this.callback=n.handler,this.axis=this.options.horizontal?"horizontal":"vertical",this.enabled=this.options.enabled,this.triggerPoint=null,this.group=t.Group.findOrCreate({name:this.options.group,axis:this.axis}),this.context=t.Context.findOrCreateByElement(this.options.context),t.offsetAliases[this.options.offset]&&(this.options.offset=t.offsetAliases[this.options.offset]),this.group.add(this),this.context.add(this),i[this.key]=this,e+=1}var e=0,i={};t.prototype.queueTrigger=function(t){this.group.queueTrigger(this,t)},t.prototype.trigger=function(t){this.enabled&&this.callback&&this.callback.apply(this,t)},t.prototype.destroy=function(){this.context.remove(this),this.group.remove(this),delete i[this.key]},t.prototype.disable=function(){return this.enabled=!1,this},t.prototype.enable=function(){return this.context.refresh(),this.enabled=!0,this},t.prototype.next=function(){return this.group.next(this)},t.prototype.previous=function(){return this.group.previous(this)},t.invokeAll=function(t){var e=[];for(var n in i)e.push(i[n]);for(var o=0,r=e.length;r>o;o++)e[o][t]()},t.destroyAll=function(){t.invokeAll("destroy")},t.disableAll=function(){t.invokeAll("disable")},t.enableAll=function(){t.invokeAll("enable")},t.refreshAll=function(){t.Context.refreshAll()},t.viewportHeight=function(){return window.innerHeight||document.documentElement.clientHeight},t.viewportWidth=function(){return document.documentElement.clientWidth},t.adapters=[],t.defaults={context:window,continuous:!0,enabled:!0,group:"default",horizontal:!1,offset:0},t.offsetAliases={"bottom-in-view":function(){return this.context.innerHeight()-this.adapter.outerHeight()},"right-in-view":function(){return this.context.innerWidth()-this.adapter.outerWidth()}},window.Waypoint=t}(),function(){"use strict";function t(t){window.setTimeout(t,1e3/60)}function e(t){this.element=t,this.Adapter=o.Adapter,this.adapter=new this.Adapter(t),this.key="waypoint-context-"+i,this.didScroll=!1,this.didResize=!1,this.oldScroll={x:this.adapter.scrollLeft(),y:this.adapter.scrollTop()},this.waypoints={vertical:{},horizontal:{}},t.waypointContextKey=this.key,n[t.waypointContextKey]=this,i+=1,this.createThrottledScrollHandler(),this.createThrottledResizeHandler()}var i=0,n={},o=window.Waypoint,r=window.onload;e.prototype.add=function(t){var e=t.options.horizontal?"horizontal":"vertical";this.waypoints[e][t.key]=t,this.refresh()},e.prototype.checkEmpty=function(){var t=this.Adapter.isEmptyObject(this.waypoints.horizontal),e=this.Adapter.isEmptyObject(this.waypoints.vertical);t&&e&&(this.adapter.off(".waypoints"),delete n[this.key])},e.prototype.createThrottledResizeHandler=function(){function t(){e.handleResize(),e.didResize=!1}var e=this;this.adapter.on("resize.waypoints",function(){e.didResize||(e.didResize=!0,o.requestAnimationFrame(t))})},e.prototype.createThrottledScrollHandler=function(){function t(){e.handleScroll(),e.didScroll=!1}var e=this;this.adapter.on("scroll.waypoints",function(){(!e.didScroll||o.isTouch)&&(e.didScroll=!0,o.requestAnimationFrame(t))})},e.prototype.handleResize=function(){o.Context.refreshAll()},e.prototype.handleScroll=function(){var t={},e={horizontal:{newScroll:this.adapter.scrollLeft(),oldScroll:this.oldScroll.x,forward:"right",backward:"left"},vertical:{newScroll:this.adapter.scrollTop(),oldScroll:this.oldScroll.y,forward:"down",backward:"up"}};for(var i in e){var n=e[i],o=n.newScroll>n.oldScroll,r=o?n.forward:n.backward;for(var s in this.waypoints[i]){var l=this.waypoints[i][s],a=n.oldScroll<l.triggerPoint,h=n.newScroll>=l.triggerPoint,p=a&&h,u=!a&&!h;(p||u)&&(l.queueTrigger(r),t[l.group.id]=l.group)}}for(var c in t)t[c].flushTriggers();this.oldScroll={x:e.horizontal.newScroll,y:e.vertical.newScroll}},e.prototype.innerHeight=function(){return this.element==this.element.window?o.viewportHeight():this.adapter.innerHeight()},e.prototype.remove=function(t){delete this.waypoints[t.axis][t.key],this.checkEmpty()},e.prototype.innerWidth=function(){return this.element==this.element.window?o.viewportWidth():this.adapter.innerWidth()},e.prototype.destroy=function(){var t=[];for(var e in this.waypoints)for(var i in this.waypoints[e])t.push(this.waypoints[e][i]);for(var n=0,o=t.length;o>n;n++)t[n].destroy()},e.prototype.refresh=function(){var t,e=this.element==this.element.window,i=this.adapter.offset(),n={};this.handleScroll(),t={horizontal:{contextOffset:e?0:i.left,contextScroll:e?0:this.oldScroll.x,contextDimension:this.innerWidth(),oldScroll:this.oldScroll.x,forward:"right",backward:"left",offsetProp:"left"},vertical:{contextOffset:e?0:i.top,contextScroll:e?0:this.oldScroll.y,contextDimension:this.innerHeight(),oldScroll:this.oldScroll.y,forward:"down",backward:"up",offsetProp:"top"}};for(var o in t){var r=t[o];for(var s in this.waypoints[o]){var l,a,h,p,u,c=this.waypoints[o][s],f=c.options.offset,d=c.triggerPoint,y=0,g=null==d;c.element!==c.element.window&&(y=c.adapter.offset()[r.offsetProp]),"function"==typeof f?f=f.apply(c):"string"==typeof f&&(f=parseFloat(f),c.options.offset.indexOf("%")>-1&&(f=Math.ceil(r.contextDimension*f/100))),l=r.contextScroll-r.contextOffset,c.triggerPoint=y+l-f,a=d<r.oldScroll,h=c.triggerPoint>=r.oldScroll,p=a&&h,u=!a&&!h,!g&&p?(c.queueTrigger(r.backward),n[c.group.id]=c.group):!g&&u?(c.queueTrigger(r.forward),n[c.group.id]=c.group):g&&r.oldScroll>=c.triggerPoint&&(c.queueTrigger(r.forward),n[c.group.id]=c.group)}}for(var w in n)n[w].flushTriggers();return this},e.findOrCreateByElement=function(t){return e.findByElement(t)||new e(t)},e.refreshAll=function(){for(var t in n)n[t].refresh()},e.findByElement=function(t){return n[t.waypointContextKey]},window.onload=function(){r&&r(),e.refreshAll()},o.requestAnimationFrame=function(e){var i=window.requestAnimationFrame||window.mozRequestAnimationFrame||window.webkitRequestAnimationFrame||t;i.call(window,e)},o.Context=e}(),function(){"use strict";function t(t,e){return t.triggerPoint-e.triggerPoint}function e(t,e){return e.triggerPoint-t.triggerPoint}function i(t){this.name=t.name,this.axis=t.axis,this.id=this.name+"-"+this.axis,this.waypoints=[],this.clearTriggerQueues(),n[this.axis][this.name]=this}var n={vertical:{},horizontal:{}},o=window.Waypoint;i.prototype.add=function(t){this.waypoints.push(t)},i.prototype.clearTriggerQueues=function(){this.triggerQueues={up:[],down:[],left:[],right:[]}},i.prototype.flushTriggers=function(){for(var i in this.triggerQueues){var n=this.triggerQueues[i],o="up"===i||"left"===i;n.sort(o?e:t);for(var r=0,s=n.length;s>r;r+=1){var l=n[r];(l.options.continuous||r===n.length-1)&&l.trigger([i])}}this.clearTriggerQueues()},i.prototype.next=function(e){this.waypoints.sort(t);var i=o.Adapter.inArray(e,this.waypoints),n=i===this.waypoints.length-1;return n?null:this.waypoints[i+1]},i.prototype.previous=function(e){this.waypoints.sort(t);var i=o.Adapter.inArray(e,this.waypoints);return i?this.waypoints[i-1]:null},i.prototype.queueTrigger=function(t,e){this.triggerQueues[e].push(t)},i.prototype.remove=function(t){var e=o.Adapter.inArray(t,this.waypoints);e>-1&&this.waypoints.splice(e,1)},i.prototype.first=function(){return this.waypoints[0]},i.prototype.last=function(){return this.waypoints[this.waypoints.length-1]},i.findOrCreate=function(t){return n[t.axis][t.name]||new i(t)},o.Group=i}(),function(){"use strict";function t(t){return t===t.window}function e(e){return t(e)?e:e.defaultView}function i(t){this.element=t,this.handlers={}}var n=window.Waypoint;i.prototype.innerHeight=function(){var e=t(this.element);return e?this.element.innerHeight:this.element.clientHeight},i.prototype.innerWidth=function(){var e=t(this.element);return e?this.element.innerWidth:this.element.clientWidth},i.prototype.off=function(t,e){function i(t,e,i){for(var n=0,o=e.length-1;o>n;n++){var r=e[n];i&&i!==r||t.removeEventListener(r)}}var n=t.split("."),o=n[0],r=n[1],s=this.element;if(r&&this.handlers[r]&&o)i(s,this.handlers[r][o],e),this.handlers[r][o]=[];else if(o)for(var l in this.handlers)i(s,this.handlers[l][o]||[],e),this.handlers[l][o]=[];else if(r&&this.handlers[r]){for(var a in this.handlers[r])i(s,this.handlers[r][a],e);this.handlers[r]={}}},i.prototype.offset=function(){if(!this.element.ownerDocument)return null;var t=this.element.ownerDocument.documentElement,i=e(this.element.ownerDocument),n={top:0,left:0};return this.element.getBoundingClientRect&&(n=this.element.getBoundingClientRect()),{top:n.top+i.pageYOffset-t.clientTop,left:n.left+i.pageXOffset-t.clientLeft}},i.prototype.on=function(t,e){var i=t.split("."),n=i[0],o=i[1]||"__default",r=this.handlers[o]=this.handlers[o]||{},s=r[n]=r[n]||[];s.push(e),this.element.addEventListener(n,e)},i.prototype.outerHeight=function(e){var i,n=this.innerHeight();return e&&!t(this.element)&&(i=window.getComputedStyle(this.element),n+=parseInt(i.marginTop,10),n+=parseInt(i.marginBottom,10)),n},i.prototype.outerWidth=function(e){var i,n=this.innerWidth();return e&&!t(this.element)&&(i=window.getComputedStyle(this.element),n+=parseInt(i.marginLeft,10),n+=parseInt(i.marginRight,10)),n},i.prototype.scrollLeft=function(){var t=e(this.element);return t?t.pageXOffset:this.element.scrollLeft},i.prototype.scrollTop=function(){var t=e(this.element);return t?t.pageYOffset:this.element.scrollTop},i.extend=function(){function t(t,e){if("object"==typeof t&&"object"==typeof e)for(var i in e)e.hasOwnProperty(i)&&(t[i]=e[i]);return t}for(var e=Array.prototype.slice.call(arguments),i=1,n=e.length;n>i;i++)t(e[0],e[i]);return e[0]},i.inArray=function(t,e,i){return null==e?-1:e.indexOf(t,i)},i.isEmptyObject=function(t){for(var e in t)return!1;return!0},n.adapters.push({name:"noframework",Adapter:i}),n.Adapter=i}();
},{}],2:[function(require,module,exports){
// Documentation build state

module.exports = {
    Build: Build
};

function Build (config) {
    this.config = config;

    // Crappy heuristic, but people change the theme name on us.  So we have to
    // do some duck typing.
    if (this.config['theme'] != 'sphinx_rtd_theme') {
        if ($('div.rst-other-versions').length == 1) {
            this.config['theme'] = 'sphinx_rtd_theme';
        }
    }

    if (this.config['api_host'] == undefined) {
        this.config['api_host'] = 'https://readthedocs.org';
    }
}

Build.prototype.is_rtd_theme = function () {
    return (this.config['theme'] == 'sphinx_rtd_theme');
};

Build.prototype.show_promo = function () {
    // TODO don't do this.
    return (this.config['api_host'] != 'https://readthedocs.com');
};

},{}],3:[function(require,module,exports){
var sponsorship = require('./sponsorship'),
    doc = require('./doc');

$(document).ready(function () {

    var build = new doc.Build(READTHEDOCS_DATA);

    get_data = {
        project: READTHEDOCS_DATA['project'],
        version: READTHEDOCS_DATA['version'],
        page: READTHEDOCS_DATA['page'],
        theme: READTHEDOCS_DATA['theme'],
        format: "jsonp",
    };


    // Crappy heuristic, but people change the theme name on us.
    // So we have to do some duck typing.
    if ("docroot" in READTHEDOCS_DATA) {
      get_data['docroot'] = READTHEDOCS_DATA['docroot'];
    }

    if ("source_suffix" in READTHEDOCS_DATA) {
      get_data['source_suffix'] = READTHEDOCS_DATA['source_suffix'];
    }

    var API_HOST = READTHEDOCS_DATA['api_host'];
    if (API_HOST === undefined) {
      API_HOST = 'https://readthedocs.org';
    }

    if (window.location.pathname.indexOf('/projects/') === 0) {
      get_data['subproject'] = true;
    }

    // Theme popout code
    $.ajax({
      url: API_HOST + "/api/v2/footer_html/",
      crossDomain: true,
      xhrFields: {
        withCredentials: true,
      },
      dataType: "jsonp",
      data: get_data,
      success: function (data) {
            // If the theme looks like ours, update the existing badge
            // otherwise throw a a full one into the page.
            if (build.is_rtd_theme()) {
              $("div.rst-other-versions").html(data['html']);
            } else {
              $("body").append(data['html']);
            }

            if (!data['version_active']) {
                $('.rst-current-version').addClass('rst-out-of-date');
            } else if (!data['version_supported']) {
                //$('.rst-current-version').addClass('rst-active-old-version')
            }

            // using jQuery
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

              function csrfSafeMethod(method) {
                  // these HTTP methods do not require CSRF protection
                  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
              }
              $.ajaxSetup({
                  beforeSend: function(xhr, settings) {
                      if (!csrfSafeMethod(settings.type)) {
                          xhr.setRequestHeader("X-CSRFToken", $('a.bookmark[token]').attr('token'));
                      }
                  }
              });

            // Bookmark Handling
            data = {
                project: READTHEDOCS_DATA['project'],
                version: READTHEDOCS_DATA['version'],
                page: READTHEDOCS_DATA['page'],
                url: document.location.origin + document.location.pathname
            };

            // ask the server if a bookmark exists for this page so we can show the proper icon
            $.ajax({
                    type: 'POST',
                    url: API_HOST + "/bookmarks/exists/",
                    crossDomain: true,
                    xhrFields: {
                      withCredentials: true,
                    },
                    data: JSON.stringify(data),
                    success: function (data) {
                      $(".bookmark-active").show();
                    },
                    error: function(data) {
                      $(".bookmark-inactive").show();
                    },
                    dataType: 'json'
            });

            $(".bookmark-icon").on('click', function (event) {
              var bookmarked = $('.bookmark-active').is(':visible');
              $('div.bookmark-active').toggle();
              $('div.bookmark-inactive').toggle();

              if (bookmarked) {
                  $.ajax({
                    type: "POST",
                    crossDomain: true,
                    xhrFields: {
                      withCredentials: true,
                    },
                    url: API_HOST + "/bookmarks/remove/",
                    data: JSON.stringify(data),
                    });
                  //$(".bookmark-added-msg").hide();
              } else {
                  $.ajax({
                    type: "POST",
                    crossDomain: true,
                    xhrFields: {
                      withCredentials: true,
                    },
                    url: API_HOST + "/bookmarks/add/",
                    data: JSON.stringify(data),
                    });
                    //$(".bookmark-added-msg").html("<p><a href='/bookmarks'>Bookmark</a> added</p>");
                    //$(".bookmark-added-msg").show();
              }
            });
      },
      error: function () {
          console.log('Error loading Read the Docs footer');
      }
    });


    /// Read the Docs Sphinx theme code
    if (!("builder" in READTHEDOCS_DATA) || "builder" in READTHEDOCS_DATA && READTHEDOCS_DATA["builder"] != "mkdocs") {
      // Shift nav in mobile when clicking the menu.
      $(document).on('click', "[data-toggle='wy-nav-top']", function() {
        $("[data-toggle='wy-nav-shift']").toggleClass("shift");
        $("[data-toggle='rst-versions']").toggleClass("shift");
      });
      // Close menu when you click a link.
      $(document).on('click', ".wy-menu-vertical .current ul li a", function() {
        $("[data-toggle='wy-nav-shift']").removeClass("shift");
        $("[data-toggle='rst-versions']").toggleClass("shift");
      });
      $(document).on('click', "[data-toggle='rst-current-version']", function() {
        $("[data-toggle='rst-versions']").toggleClass("shift-up");
      });
      // Make tables responsive
      $("table.docutils:not(.field-list)").wrap("<div class='wy-table-responsive'></div>");

      // Promos
      // TODO don't hardcode this promo and remove the util function to hide the
      // ad
      var promo = null;
      if (build.is_rtd_theme() && build.show_promo()) {
          var promo = sponsorship.Promo.from_variants([
              {
                  id: 'wtdna2015-v1',
                  text: 'Come join us at Write the Docs, a community conference about documentation.',
                  link: 'http://writethedocs.org/conf/na/2015/'
              }
              //'Enjoy reading the docs? Join fellow developers and tech writers at Write the Docs!',
              //'Love docs as much as we do? Come join the community at the Write The Docs conference',
              //'Tickets are now on sale for Write the Docs, a community conference about documentation!',
          ]);
          promo.display();
      }

      window.SphinxRtdTheme = (function (jquery) {
          var stickyNav = (function () {
              var navBar,
                  win,
                  stickyNavCssClass = 'stickynav',
                  applyStickNav = function () {
                      if (navBar.height() <= win.height()) {
                          navBar.addClass(stickyNavCssClass);
                      } else {
                          navBar.removeClass(stickyNavCssClass);
                      }
                      promo.waypoint.refresh();
                  },
                  enable = function () {
                      init();
                      applyStickNav();
                      win.on('resize', applyStickNav);
                  },
                  init = function () {
                      navBar = jquery('nav.wy-nav-side:first');
                      win    = jquery(window);
                  };
              jquery(init);
              return {
                  enable : enable
              };
          }());
          return {
              StickyNav : stickyNav
          };
      }($));
    }


    // Add Grok the Docs Client
    $.ajax({
        url: "https://api.grokthedocs.com/static/javascript/bundle-client.js",
        crossDomain: true,
        dataType: "script",
    });


    /// Out of date message

      var versionURL = [API_HOST + "/api/v1/version/", READTHEDOCS_DATA['project'],
                        "/highest/", READTHEDOCS_DATA['version'], "/?callback=?"].join("");

      $.getJSON(versionURL, onData);

      function onData (data) {
        if (data.is_highest) {
          return;
        }

        var currentURL = window.location.pathname.replace(READTHEDOCS_DATA['version'], data.slug),
            warning = $('<div class="admonition warning"> <p class="first \
                         admonition-title">Note</p> <p class="last"> \
                         You are not using the most up to date version \
                         of the library. <a href="#"></a> is the newest version.</p>\
                         </div>');

        warning
          .find('a')
          .attr('href', currentURL)
          .text(data.version);

        body = $("div.body");
        if (!body.length) {
          body = $("div.document");
        }
        body.prepend(warning);
      }


    // Override MkDocs styles
    if ("builder" in READTHEDOCS_DATA && READTHEDOCS_DATA["builder"] == "mkdocs") {
      $('<input>').attr({
          type: 'hidden',
          name: 'project',
          value: READTHEDOCS_DATA["project"]
      }).appendTo('#rtd-search-form');
      $('<input>').attr({
          type: 'hidden',
          name: 'version',
          value: READTHEDOCS_DATA["version"]
      }).appendTo('#rtd-search-form');
      $('<input>').attr({
          type: 'hidden',
          name: 'type',
          value: 'file'
      }).appendTo('#rtd-search-form');

      $("#rtd-search-form").prop("action", API_HOST + "/elasticsearch/");

      // Apply stickynav to mkdocs builds
      var nav_bar = $('nav.wy-nav-side:first'),
          win = $(window),
          sticky_nav_class = 'stickynav',
          apply_stickynav = function () {
              if (nav_bar.height() <= win.height()) {
                  nav_bar.addClass(sticky_nav_class);
              } else {
                  nav_bar.removeClass(sticky_nav_class);
              }
          };
      win.on('resize', apply_stickynav);
      apply_stickynav();
    }


    /// Search
    /// Here be dragons, this is beta quality code. Beware.

    if (build.is_rtd_theme()) {
      searchLanding();
    }

    $(document).on({
      mouseenter: function(ev) {
          var tooltip = $(ev.target).next();
          tooltip.show();
      },
      mouseleave: function(ev) {
          var tooltip = $(ev.target).next();
          tooltip.hide();
      }
    }, '.result-count');

    $(document).on('submit', '#rtd-search-form', function (ev) {
      //ev.preventDefault();
      clearSearch();
      var query = $("#rtd-search-form input[name='q']").val();
      getSearch(query, true);
    });

    $(document).on('click', '.search-result', function (ev) {
      ev.preventDefault();
      //console.log(ev.target)
      html = $(ev.target).next().html();
      displayContent(html);
    });

    function searchLanding() {
      // Highlight based on highlight GET arg
      var params = $.getQueryParameters();
      var query = (params.q) ? params.q[0].split(/\s+/) : [];
      var clear = true;
      /* Don't "search" on highlight phrases
      if (!query.length) {
        // Only clear on q
        clear = false
        var query = (params.highlight) ? params.highlight[0].split(/\s+/) : [];
      }
      */
      if (query.length) {
        query = query.join(" ");
        console.log("Searching based on GET arg for: " + query);
        $("#rtd-search-form input[name='q']").val(query);
        getSearch(query, clear);
      }
    }

    function getSearch(query, clear) {
      var get_data = {
        project: READTHEDOCS_DATA['project'],
        version: READTHEDOCS_DATA['version'],
        format: "jsonp",
        q: query
      };

      // Search results
      $.ajax({
        url: API_HOST + "/api/v2/search/section/",
        crossDomain: true,
        xhrFields: {
          withCredentials: true,
        },
        dataType: "jsonp",
        data: get_data,
        success: function (data) {
          clearSearch(clear);
          hits = data.results.hits.hits;
          if (!hits.length) {
            resetState();
          } else {
            displaySearch(hits, query);
          }
        },
        error: function () {
            console.log('Error searching');
        }
      });
    }

    function displayContent(html) {
        var content = $('.rst-content');
        content.html(html);
    }

    function displaySearch(hits, query) {
      FIRSTRUN = {};
      current = $(".toctree-l1.current > a");
      for (var index in hits) {
        var hit = hits[index];
        var path = hit.fields.path;
        var pageId = hit.fields.page_id;
        var title = hit.fields.title;
        var content = hit.fields.content;
        var highlight = hit.highlight.content;
        var score = hit._score;

        var li = $(".toctree-l1 > a[href^='" + path + "']");

        /*
        // This doesn't work :)
        if (!li.length && $(current.next().children()[0]).text() == title) {
            li = current
            console.log("Current page: " + title)
        } else {
          console.log("Not: " + title)
        }
        */

        var ul = li.next();

        console.log(path);

        // Display content for first result
        if (index === 0) {
          // Don't display content for now, so we show sphinx results
          //displayContent(content)
        }

        // Clear out subheading with result content
        if (!FIRSTRUN[path]) {
          li.show();
          li.attr("href", li.attr('href') + "?highlight=" + query);
          li.parent().addClass("current");
          li.append("<i style='position:absolute;right:30px;top:6px;' class='fa fa-search result-icon'></i>");
          ul.empty();
          FIRSTRUN[path] = true;
        }

        // Dedupe
        if (!FIRSTRUN[path+title]) {
          ul.append('<li class="toctree-l2">' + '<a class="reference internal search-result" pageId="' + pageId + '">' + title + '</a>' + '<span style="display: none;" class="data">' + content + '</span>' + '</li>');
          if (score > 1) {
            $(".toctree-l2 ");
            inserted = $('.toctree-l2 > [pageId="' + pageId + '"]');
            inserted.append("<i style='position:absolute;right:30px;top:6px;' class='fa fa-fire'></i>");
          }
          FIRSTRUN[path+title] = true;
        }
      }
      // Hide non-showing bits
      $.each($(".toctree-l1 > a"), function (index, el) {
          hide = true;
          if ($(el).attr('href') === "") {
              // Current page
              hide = false;
          }
          for (var key in FIRSTRUN) {
              if ($(el).attr('href').indexOf(key) === 0) {
                hide = false;
              }
          }
          if (hide) {
            $(el).hide();
          }

      });

    }

    function resetState() {
      $.each($(".toctree-l1 > a"), function (index, el) {
        var el = $(el);
        el.show();
        el.parent().show();
      });

    }
    function clearSearch(empty) {
      $('.result-icon').remove();
      $.each($(".toctree-l1 > a"), function (index, el) {
        var el = $(el);
        if (empty) {
          el.parent().removeClass('current');
          el.next().empty();
        }
      });
    }
});

},{"./doc":2,"./sponsorship":4}],4:[function(require,module,exports){
/* Read the Docs - Documentation promotions */

var $ = window.$,
    waypoint = require("./../../../../../bower_components/waypoints/lib/noframework.waypoints.min.js"),
    Waypoint = window.Waypoint;

module.exports = {
    Promo: Promo
};

function Promo (text, link) {
    this.text = text;
    this.link = link;
    this.promo = null;
    this.waypoint = null;
}

Promo.prototype.create = function () {
    var self = this,
        nav_side = $('nav.wy-nav-side');

    if (nav_side.length) {
        // Add elements
        promo = $('<div />')
            .attr('class', 'wy-menu rst-pro');

        // Create link with callback
        var promo_link = $('<a />')
            .attr('class', 'rst-pro-link')
            .attr('href', this.link)
            .attr('target', '_blank')
            .on('click', function (ev) {
                if (_gaq) {
                    _gaq.push(
                        ['rtfd._setAccount', 'UA-17997319-1'],
                        ['rtfd._trackEvent', 'Promo', 'Click', self.variant]
                    );
                }
            })
            .html(this.text)
            .appendTo(promo);

        // Promo info
        var promo_about = $('<div />')
            .attr('class', 'rst-pro-about');
        var promo_about_link = $('<a />')
            .attr('href', 'http://docs.readthedocs.org/en/latest/sponsors.html#sponsorship-information')
            .appendTo(promo_about);
        var promo_about_icon = $('<i />')
            .attr('class', 'fa fa-info-circle')
            .appendTo(promo_about_link);
        promo_about.appendTo(promo);

        promo.appendTo(nav_side);

        promo.wrapper = $('<div />')
            .attr('class', 'rst-pro-wrapper')
            .appendTo(nav_side);

        return promo;
    }
}

// Position promo
Promo.prototype.display = function () {
    var promo = this.promo,
        self = this;

    if (! promo) {
        promo = this.promo = this.create();
    }

    Waypoint.destroyAll();
    this.waypoint = new Waypoint({
        element: promo.wrapper.get(0),
        offset: function () {
            console.log($(window).height() - promo.height() - 80);
            return ($(window).height() - promo.height() - 80);
        },
        handler: function (direction) {
            if (direction == 'down') {
                self.promo.fadeIn(50);
            }
            else if (direction == 'up') {
                self.promo.fadeOut(50);
            }
        }
    });
}

Promo.prototype.disable = function () {
    Waypoint.destroyAll();
}

// Variant factory method
Promo.from_variants = function (variants) {
    var chosen = Math.floor(Math.random() * variants.length),
        variant = variants[chosen],
        text = variant.text,
        link = variant.link,
        id = variant.id,
        promo = new Promo(text, link);
    promo.variant = id
    return promo;
};

},{"./../../../../../bower_components/waypoints/lib/noframework.waypoints.min.js":1}]},{},[3])