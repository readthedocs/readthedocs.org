/*
 * Expands a specific tab of sphinx-tabs.
 * Usage:
 * 1) docs.readthedocs.io/?tab=Name
 * 2) docs.readthedocs.io/?tab=Name#section
 * 3) docs.readthedocs.io/page#sphinx-label
 * In 1) and 2), 'Name' is the title of the tab (case sensitive).
 *
 * In 3), you need to add a sphinx reference inside the tab.
 * It mimics how sections are referenced and can be refactored.
*/
$( document ).ready(function() {
  const urlParams = new URLSearchParams(window.location.search);
  const tabName = urlParams.get('tab');
  if (tabName !== null) {
    const tab = $('button.sphinx-tabs-tab:contains("' + tabName + '")');
    if (tab.length > 0) {
      tab.click();
    }
  }

  // Uses a hash referencing a Sphinx label from the URL page#sphinx-label
  var hash = window.location.hash.substr(1);
    if (hash) {
    hash = hash.replace(/[^0-9a-z\-_]/gi, '');
    // If the hash is inside a tab panel
    var tab_with_reference = $(".sphinx-tabs-panel #" + hash).parents(".sphinx-tabs-panel");

    if (tab_with_reference.length > 0) {
      // Use the panel's ID to guess the tab's ID
      var panel_id = tab_with_reference.first().attr("id");
      var tab_id = panel_id.replace("panel-", "tab-");
      // Invoke the tab buttons click() method to display it
      $("button#" + tab_id).click();
      // Scroll the tab widget into view
      $('html, body').animate({ scrollTop: tab_with_reference.parents(".sphinx-tabs").first().offset().top}, 1000);
    }
  }
});
