$( document ).ready(function() {
  // Shift nav in mobile when clicking the menu.
  $("[data-toggle='wy-nav-top']").click(function() {
    $("[data-toggle='wy-nav-shift']").toggleClass("shift");
    $("[data-toggle='rst-versions']").toggleClass("shift");
  });
  // Close menu when you click a link.
  $(".wy-menu-vertical .current ul li a").click(function() {
    $("[data-toggle='wy-nav-shift']").removeClass("shift");
    $("[data-toggle='rst-versions']").toggleClass("shift");
  });
  $("[data-toggle='rst-current-version']").click(function() {
    $("[data-toggle='rst-versions']").toggleClass("shift-up");
  });
  $("table.docutils:not(.field-list").wrap("<div class='wy-table-responsive'></div>");
});

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
            },

            enable = function () {

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