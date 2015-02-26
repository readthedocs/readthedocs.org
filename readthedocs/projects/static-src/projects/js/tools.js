var rtd = require('readthedocs-client');

      function clearAll() {
        $('#results').contents().find('html').html('')
        $('#id_section').empty()
        $('#results_raw').empty()
      }

      function showHelp() {
        ReadTheDocs.embed.into('docs', 'versions', 'How we envision versions working', function (data) {
          $("#id_help").html(data['content'])
          $('#id_help').toggle()
        })
      }

      function reloadSection(project, doc) {
        clearAll()
        var options = $("#id_section");
        options.append($("<option />").val('Loading..').text('Loading..'));
              $.ajax({
                type: 'GET',
                url: 'http://localhost:5555/api/v1/embed/',
                //url: 'https://api.grokthedocs.com/api/v1/content/',
                crossDomain: true,
                data: {
                  project: project,
                  doc: doc,
                },
                success: function(data, textStatus, request) {
                  options.empty()
                  options.append($("<option />").val('').text('Select a Section'));
                  $.each(data['headers'], function(index) {

                    $.each(data['headers'][index], function (key, val) {
                      if (val != '#') {
                        options.append($("<option />").val(key).text(key));
                      }
                    })

                  })

                },
              });
      }

      function clearIframe(text) {
        $('#results').contents().find('html').html(text)
        $('#id_url').html('')
      }

        $(document).ready(function() {
              var project = '{{ project.slug }}';

            $('#id_file').bind('change', function(ev) {
              var file = $('#id_file').val()
              reloadSection(project, file)
              clearIframe()
            })

            $('#id_section').bind('change', function(ev) {
                var file = $('#id_file').val()
                var section = $('#id_section').val()
                clearIframe('Loading...')

                $.ajax({
                  type: 'GET',
                  url: 'http://localhost:5555/api/v1/embed/',
                  //url: 'https://api.grokthedocs.com/api/v1/content/',
                  crossDomain: true,
                  xhrFields: {
                    withCredentials: true,
                  },
                  data: {
                    project: project,
                    doc: file,
                    section: section
                  },
                  success: function(data, textStatus, request) {
                    console.log("Sent Click data")
                    if (data['content'][0] == null)
                      $('#results').contents().find('html').html('<h1>Section Not Found</h1>')
                    else {
                      $('#results').contents().find('html').html(data['content'])
                      $('#results').contents().find('html').prepend('<link rel="stylesheet" href="http://localhost:5555/static/css/public.css">')
                      $('#results').contents().find('html').prepend('<link rel="stylesheet" href="http://mkdocs.readthedocs.org/en/latest/css/theme.css">')
                      $('#results_raw').text(data['content'])
                    }
                    var link = $('<a>', {
                      text: this.url,
                      href: this.url,
                    })
                    $('#id_url').html(link)
                  },
                  error: function(request, textStatus, error) {
                    $('#results').contents().find('html').html('<h1>Section Not Found</h1>')
                    console.log(error)
                  }
                });
          });
        });


