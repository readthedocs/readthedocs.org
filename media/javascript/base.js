$(function() {
  $('body')
    .on('click', '.dropdown > span > a:last-child', open_dropdown)
    .on('keyup', '.dropdown input[type=search]', filter_dropdown_results)
    .click(hide_dropdown) 

  $('select.dropdown').each(function(i, e) { build_dropdown_from_select($(e)) })

  function open_dropdown(ev) {
    console.log('open_dropdown')
    ev.preventDefault()
    $('.dropdown > ul').removeClass('js-open')
    var el = $(ev.target)
      , dropdown = el.parents('.dropdown')

    dropdown.find('li').show()
    dropdown.find('ul').addClass('js-open')
    dropdown.find('input[type=search]').val('').focus()
  }

  function filter_dropdown_results(ev) {
    console.log('is this getting called')

    var el = $(ev.target)
      , dropdown = el.parents('.dropdown')
      , value = this.value

    dropdown.find('li').show()
   
    if(value.length) {
      dropdown.find('li').hide()
      dropdown.find('li').filter(function(i, el) {
        return ($(el).text().indexOf(value) === 0)
      }).show()
      el.parent().show()
    }

    if(ev.keyCode === 13) {
      ev.preventDefault()
      var anchor = dropdown.find('li:visible > a').eq(0)

      setTimeout(function() {
        anchor.click()
      })
    } else if(ev.keyCode === 27) {
      el.val('')
      dropdown.find('li').show()
    }
  } 

  function hide_dropdown(ev) {
    if(!$(ev.target).parents('.dropdown').length) {
      $('.dropdown > ul').removeClass('js-open')
    }
  }


  function build_dropdown_from_select(select) {
    var options = {}
      , selected = null
      , option_ul
      , framing


    framing = $('<span class="dropdown"><span>'+
      '<a href="#"></a><a href="#">&#x25BC;</a></span>'+
      '<ul></ul></span>'
    )
    option_ul = framing.find('ul')

    select.find('option').each(function(idx, el) {
      el = $(el)
      var value = el.attr('value')

      options[value] = el.text()
      selected = selected === null ? value : selected

      option_ul.append(
        $('<li></li>').append(
          $('<a href="#"></a>')
            .text(options[value])
            .attr('data-value', value)
          )
      )

    })

    console.log('norp', select, select.find('option'), options, selected)
    selected = options[select.val() || selected]


    framing.find('span > a:first-child').text(selected)

    framing.on('click', '[data-value]', function(ev) {
      ev.preventDefault()
      framing.find('span > a:first-child').text($(this).text())
      select.val($(this).attr('data-value'))

      option_ul.removeClass('js-open')
    })

    select.after(framing)

  }

  // Install events handlers user menu button the window, to open the menu and
  // close it if it loses click focus.
  (function () {
    var menu = $('.menu-user'),
        menu_button = menu.find('div.menu-button'),
        menu_dropdown = menu.find('div.menu-dropdown');

    menu_button.on('click', function (ev) {
      ev.stopPropagation();
      if (menu_dropdown.hasClass('menu-dropped')) {
        menu_dropdown.removeClass('menu-dropped');
      }
      else {
        $('html').on('click', function () {
          menu_dropdown.removeClass('menu-dropped');
        });
        menu_dropdown.on('click', function (ev) {
          ev.stopPropagation();
        });
        menu_dropdown.addClass('menu-dropped');
      }
    });
  })();
})
