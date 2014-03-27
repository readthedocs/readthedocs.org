# User setup

docs:
  user.present:
    - fullname: Docs User
    - uid: 1005
    - gid: 205
    - home: /home/docs
    - shell: /bin/bash
    - createhome: True
    - require:
      - group: docs
  group.present:
    - gid: 205

/home/docs/.bash_profile:
  file.managed:
    - source: salt://readthedocs/user/bash_profile
    - user: docs
    - group: docs
    - require:
      - user: docs

/home/docs/.ssh:
  file.directory:
    - user: docs
    - group: docs
    - mode: 0700
    - require:
      - user: docs

# TODO configure key based on host name
/home/docs/.ssh/id_rsa:
  file.managed:
    - source: salt://readthedocs/user/private_key
    - user: docs
    - group: docs
    - mode: 0400
    - require:
      - user: docs
