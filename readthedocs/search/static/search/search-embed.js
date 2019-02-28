
  $(document).ready(function () {
  var config = {api_host: 'http://localhost:8000'}
  var embed = new Embed(config);
    $('.fragment').one("click mouseover",
      function(elem) {
            embed.section(
                elem.currentTarget.getAttribute('project'),
                elem.currentTarget.getAttribute('version'),
                elem.currentTarget.getAttribute('doc_name').replace('.html', ''),
                elem.currentTarget.getAttribute('anchor'),
                function (section) {
                    section.insertContent(elem.currentTarget);
                }
            )
      }
    )
  })
