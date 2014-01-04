backend chimera {
    .host = "10.177.72.204";
    .port = "8000";
    .probe = {
        .request =
            "OPTIONS * HTTP/1.1"
            "Host: readthedocs.org"
            "Connection: close";
    }
}

backend ladon {
    .host = "10.177.73.65";
    .port = "8000";
    .probe = {
        .request =
            "OPTIONS * HTTP/1.1"
            "Host: readthedocs.org"
            "Connection: close";
    }
}

director doubleteam round-robin {
      {
              .backend = chimera;
      }
      # server2
      {
              .backend = ladon;
      }
}

acl purge {
        "localhost";
        "192.0.2.14";
	"10.177.72.204";
}

sub vcl_recv {
    set req.backend = doubleteam;
	if (req.request == "PURGE") {
		if (!client.ip ~ purge) {
			error 405 "Not allowed.";
		}
		purge("req.url ~ " req.url " && req.http.host == " req.http.host);
		error 200 "Purged.";
	}
  set req.grace = 2m;
  if (req.http.host != "readthedocs.org") {
    unset req.http.Cookie;
    unset req.http.cache-control;
    return(lookup);
  }

  // Remove has_js and Google Analytics cookies.
  set req.http.Cookie = regsuball(req.http.Cookie, "(^|;\s*)(__[a-z]+|has_js)=[^;]*", "");
  // Remove a ";" prefix, if present.
  set req.http.Cookie = regsub(req.http.Cookie, "^;\s*", "");
  // Remove empty cookies.
  if (req.http.Cookie ~ "^\s*$") {
    unset req.http.Cookie;
  }
  if (req.url ~ "\.(png|gif|jpg|swf|css|js|ico)$") {
    unset req.http.cookie;
  }
}

sub vcl_fetch {
  set beresp.ttl = 1m;
  set req.grace = 5m;
  if (req.http.host != "readthedocs.org") {
    set beresp.ttl = 7d;
  }
  if (req.http.host ~ "(.+).rtfd.org") {
    set beresp.ttl = 10s;
  }
}
