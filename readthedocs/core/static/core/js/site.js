require=(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({"core/site":[function(require,module,exports){
/* Site-specific javascript */

// Notifications that can both dismiss and point to a separate URL
module.exports.handle_notification_dismiss = function () {
  $(document).ready(function () {
    $('ul.notifications li.notification > a').click(function (ev) {
      var url = $(this).attr('href');
      var dismiss_url = $(this).parent().attr('data-dismiss-url');
      if (dismiss_url) {
        ev.preventDefault();
        $.get(dismiss_url, function (data, text_status, xhr) {
          window.location.href = url;
        });
      }
      else {
        $(this).hide();
      }
    });
  });
}

},{}]},{},[]);
