/etc/hosts:
  file.managed:
    - source: salt://hosts/hosts.conf
    - mode: 0640
    - owner: root

/root/.ssh/authorized_keys:
  file.managed:
    - source: salt://hosts/authorized_keys.conf
    - mode: 0600
    - owner: root

