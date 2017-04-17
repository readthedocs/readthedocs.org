require=(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({"core/autocomplete":[function(require,module,exports){
var $ = require('jquery'),
    jqueryui = require('jquery-ui');

module.exports = function (selector, url) {
  $(selector).autocomplete({
    source: url,
    minLength: 2,
    open: function(event, ui) {
      ac_top = $('.ui-autocomplete').css('top');
      $('.ui-autocomplete').css({'width': '233px', 'top': ac_top + 10 });
    }
  });
}

},{"jquery":"jquery","jquery-ui":"jquery-ui"}]},{},[]);
