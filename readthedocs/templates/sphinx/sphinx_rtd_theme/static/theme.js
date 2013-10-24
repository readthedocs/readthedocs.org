$(document).ready(function() {
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
});

