# Nginx

nginx:
  pkg.installed:
    - name: nginx-extras
  service.running:
    - enable: True
    - require:
      - pkg: nginx

/etc/nginx/nginx.conf:
  file.managed:
    - source: salt://nginx/conf/nginx.all.conf
    - mode: 0640

/etc/nginx/sites-enabled/default:
  file:
    - absent

/usr/share/nginx/perl:
  file.directory:
    - require:
      - pkg: nginx
