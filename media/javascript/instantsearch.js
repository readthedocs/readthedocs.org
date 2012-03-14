//     Read the Docs
//     http://readthedocs.org/

// Searching as the user types.
(function(){

  // Save a reference to the global object.
  var root = this;

  // Global Search object on which public functions can be added
  var Search;
  Search = root.Search = {};

  // for instituting a delay between keypresses and searches 
  var timer = null; 
  var delay = 250;
  var lastQuery = null;

  // Check if the browser supports history manipulation so
  // we can change the URL upon instant searches
  var replaceStateSupported = (typeof history.replaceState === "function");

  // queue of current requests
  var xhr = []; 

  var $input, $button, $results, $title, $selected_facets = null;

  function init() {
    $input = $('#id_site_search_2');
    $button = $('#id_search_button');
    $results = $("#id_search_result");
    $title = $("#id_search_title");
    $selected_facets = $("#id_selected_facets");
    // minimum requirements for this script to kick in...
    if(!$input.length || !$results.length) {
      return false;
    } else {
      lastQuery = queryString()
      bind();
    }
  }
  Search.init = init;
   
  // Setup the bindings for clicking search or keypresses
  function bind() {

    // Set a delay so not _every_ keystroke sends a search
    $input.keyup(function(ev) {

      // Don't do anything unless the query has changed
      if(lastQuery == queryString()) {
        return;
      }

      if(timer) {
        clearTimeout(timer);
      }
      timer = setTimeout("Search.run()", delay);
    }); 

    $button.click(run);
  }

  // Abort all existing XHR requests, since a new search is starting
  function abortCurrentXHR() {
    var request = xhr.pop();
    while(request) {
      request.abort();
      request = xhr.pop();
    }
  }

  // Replace the search results HTML with `html` (string)
  function replaceResults(html) {
    $results.empty();
    $results.append(html);
    $title.html(getTitle());
    $results.show();
  }
 
  // Construct the results HTML 
  // TODO: Use a template!
  function buildHTML(results) {
    var html = [];
    for (var i=0; i<results.length; i++) {
      html.push([
        '<li class="module-item">',
          '<p class="module-item-title">',
              'File: <a href="', results[i].absolute_url, 
                    '?highlight=', $("#id_site_search_2").val(), '">', 
                    results[i].project.name,
                    " - ", results[i].name, "</a>",
          "</p>",
          "<p>", results[i].text, "</p>",
        "</li>"].join('')
      );
    }   
    return html.join('');
  }
 
  // Pop the last search off the queue and render the `results`
  function onResultsReceived(results) {
    // remove the request from the queue
    xhr.pop();
    lastQuery = queryString()
    replaceResults(buildHTML(results));
    replaceState();
    $("#id_remove_facets").attr('href', removeFacetsUrl());
  }

  // Replace the URL with the one corresponding to the current search
  function replaceState() {
    if(!replaceStateSupported) {
      return;
    }
    var url = "/search/project/?" + queryString();
    var title = getTitle() + ' | Read the Docs';
    window.history.replaceState({}, title, url);
  }

  // Page title
  function getTitle() {
    return "Results for " + $("#id_site_search_2").val();
  }

  // Params used in the search
  function getSearchData() {
    var data = {
      q: getKeywords(),
    }
    var selected_facets = $selected_facets.val() || ''
    if(selected_facets) {
      data['selected_facets'] = selected_facets;
    }
    return data;
  }

  // e.g. q=my+search&selected_facets=project_exact:Read%20The%20Docs
  function queryString() {
    return jQuery.param(getSearchData());
  }

  // The active query value
  function getKeywords() {
   return $input.val()
  }

  // Url for the current query with any facet filters removed
  function removeFacetsUrl() {
    return '?' + jQuery.param({q: getKeywords()});
  }

  // Perform the ajax request to get the search results from the API
  function run(ev) {
    if(ev) {
        ev.preventDefault();
    }
    abortCurrentXHR();

    // Don't do anything if there is no query
    if(getKeywords() == '') {
      $results.empty();
      $results.hide();
      $title.html("No search term entered");
      return;
    }

    var data = getSearchData();
    xhr.push(jQuery.ajax({
      type: 'GET',
      url: "/api/v1/file/search/",
      data: data,
      dataType: 'jsonp',
      success: function(res, text, xhqr) {
        onResultsReceived(res.objects);
      }
    }));

  }
  Search.run = run;

}).call(this);
