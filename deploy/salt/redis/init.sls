# Redis

redis-server:
  pkg:
    - installed
  service.running:
    - enable: True
    - require:
      - pkg: redis-server
