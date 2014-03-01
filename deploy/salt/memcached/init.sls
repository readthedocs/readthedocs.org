# Memcached config

memcached:
  pkg:
    - installed
  service.running:
    - enable: True
    - require:
      - pkg: memcached
    - watch:
      - file: /etc/memcached.conf

/etc/memcached.conf:
  file.managed:
    - source: salt://memcached/memcached.conf
    - mode: 0640
