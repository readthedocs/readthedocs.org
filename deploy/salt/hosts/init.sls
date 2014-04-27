/etc/hosts:
  file.managed:
    - source: salt://hosts/hosts.conf
    - mode: 0640
    - owner: root

