(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
comm = require('./lib/comm')
events = require('./lib/events')
display = require('./lib/display')

$(document).ready(function () {
	events.initEvents();
	comm.initOptions();
	comm.initMetaData();
	display.initDisplay();
})


},{"./lib/comm":2,"./lib/display":3,"./lib/events":5}],2:[function(require,module,exports){
module.exports = {
  initMetaData: initMetaData,
  addComment: addComment,
  attachComment: attachComment,
  getServerData: getServerData,
  initOptions: initOptions
}

settings = require('./settings')
docpage = require('./docpage')
display = require('./display')

function getServerData(format) {
  return {
    "project": docpage.project,
    "version":  docpage.version,
    "document_page": docpage.page,
    "page": docpage.page,
    "commit": docpage.commit
  }
}

function initOptions() {
  var get_data = getServerData()

  $.ajax({
   type: 'GET',
   url: settings.opts.optionsURL,
   data: get_data,
   crossDomain: true,
   xhrFields: {
     withCredentials: true,
   },
   success: function(data, textStatus, request) {
    settings.opts = jQuery.extend(settings.opts, data);
   },
   error: function(request, textStatus, error) {
     display.showError('Oops, there was a problem retrieving the comment options.');
   },
  });
}


function initMetaData() {
  var get_data = getServerData()

  $.ajax({
   type: 'GET',
   url: settings.opts.metadataURL,
   data: get_data,
   crossDomain: true,
   xhrFields: {
     withCredentials: true,
   },
   success: function(data) {
      settings.metadata = jQuery.extend(settings.metadata, data);
      displayCommentIcon()
   },
   error: function(request, textStatus, error) {
     display.showError('Oops, there was a problem retrieving comment metadata.');
   },
  });
}

function displayCommentIcon() {
  // Only show data on the toc trees
  for (id in settings.metadata) {
      count = settings.metadata[id]
      console.log(id + ": " + count)
      var title = count + ' comment' + (count == 1 ? '' : 's');
      var image = count > 0 ? settings.opts.commentBrightImage : settings.opts.commentImage;
      var addcls = count == 0 ? ' nocomment' : '';
      addCommentIcon(id, title, image, addcls)
  }
  $.each($('.sphinx-has-comment'), function () {
    count = 0
    id = $(this).attr('id')
    if (!(id in settings.metadata)) {
      var title = count + ' comment' + (count == 1 ? '' : 's');
      var image = count > 0 ? settings.opts.commentBrightImage : settings.opts.commentImage;
      var addcls = count == 0 ? ' nocomment' : '';
      addCommentIcon(id, title, image, addcls)
    }
  })
}

function addCommentIcon(id, title, image, addcls) {
  $("#" + id)
      .append(
        $(document.createElement('a')).attr({
          href: '#',
          'class': 'sphinx-comment-open' + addcls,
          id: 'comment-open-' + id
        })
        .append($(document.createElement('img')).attr({
          src: image,
          alt: 'comment',
          title: title
        }))

      )
      .append(
        $(document.createElement('a')).attr({
          href: '#',
          'class': 'sphinx-comment-close hidden',
          id: 'comment-close-' + id
        })
        .append($(document.createElement('img')).attr({
          src: settings.opts.closeCommentImage,
          alt: 'close',
          title: 'close'
        }))
      );
}


function addComment(form) {
  var node_id = form.find('input[name="node"]').val();
  var text = form.find('textarea[name="comment"]').val();

  if (text == '') {
    display.showError('Please enter a comment.');
    return;
  }

  // Disable the form that is being submitted.
  form.find('textarea,input').attr('disabled', 'disabled');


  var server_data = getServerData();
  var comment_data = {
      node: node_id,
      text: text,
    };
  var post_data = $.extend(server_data, comment_data)


  // Send the comment to the server.
  $.ajax({
    type: "POST",
    url: settings.opts.addCommentURL,
    dataType: 'json',
    data: post_data,
    success: function(data, textStatus, error) {
      form.find('textarea')
        .val('')
        .add(form.find('input'))
        .removeAttr('disabled');
      display.showOneComment($(".comment-list"), data)
      var comment_element = $('#' + node_id);
      comment_element.find('img').attr({'src': settings.opts.commentBrightImage});
      comment_element.find('a').removeClass('nocomment');
    },
    error: function(request, textStatus, error) {
      form.find('textarea,input').removeAttr('disabled');
      display.showError('Oops, there was a problem adding the comment.');
    }
  });
}


function attachComment(form) {
  var node_id = form.find('input[name="node"]').val();
  var comment_id = form.find('input[name="comment"]').val();

  var server_data = getServerData();
  var comment_data = {
      node: node_id,
      comment: comment_id
    };
  var post_data = $.extend(server_data, comment_data)


  // Send the comment to the server.
  $.ajax({
    type: "POST",
    url: settings.opts.attachCommentURL,
    dataType: 'json',
    data: post_data,
    success: function(data, textStatus, error) {
      form.find('textarea')
        .val('')
        .add(form.find('input'))
        .removeAttr('disabled');
      display.showOneComment($(".comment-list"), data)
      var comment_element = $('#' + node_id);
      comment_element.find('img').attr({'src': settings.opts.commentBrightImage});
      comment_element.find('a').removeClass('nocomment');
    },
    error: function(request, textStatus, error) {
      form.find('textarea,input').removeAttr('disabled');
      display.showError('Oops, there was a problem adding the comment.');
    }
  });
}



},{"./display":3,"./docpage":4,"./settings":6}],3:[function(require,module,exports){
module.exports = {
    initDisplay: initDisplay,
    displayComments: displayComments,
    showOneComment: showOneComment,
    closeComments: closeComments
}

comm = require('./comm')

function initDisplay() {
    $('body').append("<div id='current-comment'></div>");
    $('body').append("<div id='pageslide'></div>");
}

function closeComments() {
  $.pageslide.close()
}

function displayComments(id) {
  server_data = comm.getServerData()
  get_data = {
    'node': id
  }
  var post_data = $.extend(get_data, server_data)
  delete post_data['page']

  $.ajax({
   type: 'GET',
   url: settings.opts.getCommentsURL,
   data: post_data,
   crossDomain: true,
   xhrFields: {
     withCredentials: true,
   },
   success: function(data) {
       handleComments(id, data)

   },
   error: function(request, textStatus, error) {
     showError('Oops, there was a problem retrieving the comments.');
   },
   dataType: 'json'
  });
}


function handleComments(id, data) {
    showComments(id, data.results)
}


function showComments(id, comment_data) {
  element = $('#current-comment').html("<h1> Comments </h1>")
  element.append("<div class='comment-list' id='current-comment-list'>")
  for (index in comment_data) {
      obj = comment_data[index]
      showOneComment($(".comment-list"), obj)
  }
  element.append("</div>")
  var reply = '\
      <div class="reply-div" id="comment-reply-' + id + '>">\
        <form class= "comment-reply-form" id="comment-reply-form-' + id + '">\
          <textarea name="comment" cols="40"></textarea>\
          <input type="submit" value="Add Comment" />\
          <input type="hidden" name="node" value="' + id + '" />\
        </form>\
      </div>'

  element.append("<div class='comment-div' id='current-comment-reply'>")
  $(".comment-div").append(reply)
  element.append("</div>")

  element.append("<br><br><br>")
  element.append("<hr>")
  element.append("<br><br><br>")
  element.append("<h1>Floating Comments</h1>")
    element.append("<div class='floating-comment-list' id='floating-comment-list'>")
    for (index in comment_data) {
        obj = comment_data[index]
        showOneComment($(".floating-comment-list"), obj)
        var attach = '\
            <div class="attach-div" id="comment-attach-' + id + '>">\
              <form class= "comment-attach-form" id="comment-attach-form' + id + '">\
                <input type="submit" value="Attach" />\
                <input type="hidden" name="node" value="' + id + '" />\
                <input type="hidden" name="comment" value="' + obj['pk'] + '" />\
              </form>\
            </div>'

    }
  element.append("<div class='floating-comment-div' id='floating-comment-reply'>")
  $(".floating-comment-div").append(attach)
  element.append("</div>")

    element.append("</div>")
  element.append("</div>")

  $.pageslide({direction: 'left', href:'#current-comment' })
}

function showOneComment(element, comment) {
    console.log("Displaying")
    console.log(comment)
      to_append = "<span class='comment'>"
      to_append += comment['date'] + "<br>"
      to_append += comment['text']
      to_append += "</span>"
      element.append(to_append)
}

  function showError(message) {
    $(document.createElement('div')).attr({'class': 'popup-error'})
      .append($(document.createElement('div'))
               .attr({'class': 'error-message'}).text(message))
      .appendTo('body')
      .fadeIn("slow")
      .delay(2000)
      .fadeOut("slow");
  }

// Don't need this since its in the page.

/*
function setUpPageslide() {
    $.ajax({
        url: "https://api.grokthedocs.com/static/javascript/pageslide/jquery.pageslide.js",
        crossDomain: true,
        dataType: "script",
        cache: true,
        success: function () {
            console.log("Loaded pageslide")
            $('head').append('<link rel="stylesheet" href="https://api.grokthedocs.com/static/css/top.css" type="text/css" />');
            $('body').append("<div id='gtd-top'></div>");
        },
        error: function (e) {
            console.log("OMG FAIL:" + e)
        }

    });
}
*/
},{"./comm":2}],4:[function(require,module,exports){
// Module exporting page-level variables for easy use
module.exports = {
	project: READTHEDOCS_DATA['project'],
	version: READTHEDOCS_DATA['version'],
	page: getPageName(),
	commit: getCommit()
}

function getPageName() {
	if ('page' in READTHEDOCS_DATA) {
	  return READTHEDOCS_DATA['page']
	} else {
	  stripped = window.location.pathname.substring(1)
	  stripped = stripped.replace(".html", "")
	  stripped = stripped.replace(/\/$/, "")
	  return stripped
	}
}

function getCommit() {
	if ('commit' in READTHEDOCS_DATA) {
	  return READTHEDOCS_DATA['commit']
	} else {
		return "unknown-commit"
	}
}

},{}],5:[function(require,module,exports){
module.exports = {
	initEvents: initEvents
}

display = require('./display')

function initEvents() {
	$(document).on("click", "a.sphinx-comment-open", function(event) {
		event.preventDefault();
		display.displayComments($(this).attr('id').substring('comment-open-'.length));
	})
	$(document).on("click", "a.sphinx-comment-close", function(event) {
		event.preventDefault();
		display.closeComments($(this).attr('id').substring('comment-close-'.length));
	})

	$(document).on("submit", ".comment-reply-form", function(event) {
		event.preventDefault();
		comm.addComment($(this));
	})

	$(document).on("submit", ".comment-attach-form", function(event) {
		event.preventDefault();
		comm.attachComment($(this));
	})
}


},{"./display":3}],6:[function(require,module,exports){
var baseURL = "{{ websupport2_base_url }}";
var staticURL = "{{ websupport2_static_url }}";

// Template rendering failed
if (baseURL.lastIndexOf("{{", 0) === 0) {
  var rootURL = "http://localhost:8000";
  var baseURL = "http://localhost:8000/websupport";
  var staticURL = "http://localhost:8000/static";
}

var metadata = {}

var opts = {
  // Dynamic Content
  processVoteURL: baseURL + '/_process_vote',
  addCommentURL: rootURL + '/api/v2/comments/',
  attachCommentURL: baseURL + '/_attach_comment',
  getCommentsURL: rootURL + '/api/v2/comments/',
  acceptCommentURL: baseURL + '/_accept_comment',
  deleteCommentURL: baseURL + '/_delete_comment',
  metadataURL: baseURL + '/_get_metadata',
  optionsURL: baseURL + '/_get_options',

  // Static Content
  commentImage: staticURL + '/_static/comment.png',
  closeCommentImage: staticURL + '/_static/comment-close.png',
  loadingImage: staticURL + '/_static/ajax-loader.gif',
  commentBrightImage: staticURL + '/_static/comment-bright.png',
  upArrow: staticURL + '/_static/up.png',
  downArrow: staticURL + '/_static/down.png',
  upArrowPressed: staticURL + '/_static/up-pressed.png',
  downArrowPressed: staticURL + '/_static/down-pressed.png',

  voting: false,
  moderator: false
};


module.exports = {
  metadata: metadata,
  opts: opts,
  staticURL: staticURL,
  baseURL: baseURL
}


},{}]},{},[1]);
