function instantSearch() {
  $("#id_search_button").click(function() {
    if ($("#id_site_search_2").val() == '') {
      $("#id_search_result").empty();
      $("#id_search_result").hide();
      $("#id_search_title").html("No search term entered");
    } else {
      jQuery.ajax({
        type: 'GET',
        url: "/api/v1/file/search/",
        data: {format: 'jsonp', q: $("#id_site_search_2").val()},
        success: function(searchres, text, xhqr) {
          strstart = this.url.indexOf("&q=") + 3;
          strend = this.url.indexOf("&", strstart);
          if (strend == -1) orig_query = this.url.substring(strstart);
          else orig_query = this.url.substring(strstart, strend);
          orig_query2 = unescape(orig_query.replace(/\+/g, " "));
          // Block any old queries that come through after the latest one
          if (orig_query2 != $("#id_site_search_2").val()) return false;
          $("#id_search_result").empty();
          for (var i=0; i<searchres.objects.length; i++) {
            $("#id_search_result").append("<li class=\"module-item\">\n" +
            "<p class=\"module-item-title\">\n" +
            "  File: <a href=" + searchres.objects[i].absolute_url + "?highlight=" +
            $("#id_site_search_2").val() + ">" + searchres.objects[i].project.name +
            " - " + searchres.objects[i].name + "</a>\n" +
            "</p>\n" +
            "<p>\n" +
            "  " + searchres.objects[i].text + "\n" +
            "</p>\n" +
            "</li>\n");
          }
        },
        dataType: 'jsonp'
      });
      $("#id_search_title").html("Results for " + $("#id_site_search_2").val());
      $("#id_search_result").show();
    }
    return false;
  });
  
  $("#id_site_search_2").keyup(function() {
    $("#id_search_button").click();
  });
}

// Code for showing projects. Not used.
/*
          "  <li class=\"module-item\">\n" +
          "      <p class=\"module-item-title\">\n" +
          "          Project:\n" +
          "      <a href=\"" + searchres.objects[i].project.project_url + "\">" + 
          searchres.objects[i].project.name + i + " - " +
          searchres.objects[i].project.copyright + "</a>\n" +
          "    </p>\n" +
          "  </li>\n");
*/
