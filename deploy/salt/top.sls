base:
  'vagrant':
    - postgres
    - memcached
    - nginx
    - redis
    - python.base
    - readthedocs.user
    - readthedocs.site
  'valhalla':
    - nginx.lb
    - hosts
