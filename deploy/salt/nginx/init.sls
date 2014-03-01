# Nginx

nginx:
  pkg:
    - installed
  service.running:
    - enable: True
    - require:
      - pkg: nginx
    - watch:
      - file: /etc/nginx/sites-enabled/readthedocs

/etc/nginx/nginx.conf:
  file.managed:
    - source: salt://nginx/nginx.conf
    - mode: 0640

/etc/nginx/sites-enabled/default:
  file:
    - absent
