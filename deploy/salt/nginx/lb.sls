# Load Balancer Config

# Nginx

lb.nginx:
  pkg.installed:
    - name: nginx-extras
  service.running:
    - enable: True
    - require:
      - pkg: nginx

/etc/nginx/nginx.conf:
  file.managed:
    - source: salt://nginx/conf/nginx.lb.conf
    - mode: 0644

/etc/logrotate.d/nginx:
  file.managed:
    - source: salt://nginx/logrotate.conf
    - mode: 0640

/etc/nginx/sites-enabled/default:
  file:
    - absent

/usr/share/nginx/perl:
  file.directory:
    - require:
      - pkg: nginx

/etc/nginx/sites-enabled/lb:
  file.managed:
    - source: salt://nginx/sites/lb
    - mode: 0640
