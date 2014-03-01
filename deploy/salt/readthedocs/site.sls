# RtD env setup

# Virtualenv and checkout
{% set site_path = '/home/docs/sites/readthedocs.org' %}

{{ site_path }}:
  file.directory:
    - user: docs
    - group: docs
    - makedirs: True
    - require:
      - user: docs
  virtualenv.managed:
    - user: docs
    - require:
      - pip: python-virtualenv
      - file: {{ site_path }}
    - reload_modules: True

{% for path in ['run', 'checkouts'] %}
{{ site_path }}/{{ path }}:
  file.directory:
    - user: docs
    - group: docs
    - require:
      - user: docs
      - file: {{ site_path }}
{% endfor %}

{{ site_path }}/checkouts/readthedocs.org:
  file.directory:
    - require:
      - user: docs
      - file: {{ site_path }}/checkouts
      - pkg: rtd-vcs-pkgs

# Use a command here, instead of pip.installed -- pip 1.5 uses additional flags
# for external dependencies and pip.installed doesn't respect the cwd, making
# requirements such as -r pip_requirements.txt fail
rtd-deps:
  cmd.wait:
    - name:
        {{ site_path }}/bin/pip install
        --timeout 120
        --allow-all-external
        --allow-unverified bzr
        --allow-unverified launchpadlib
        --allow-unverified lazr.authentication
        -r deploy_requirements.txt
    - cwd: {{ site_path }}/checkouts/readthedocs.org
    - watch:
      - file: {{ site_path }}/checkouts/readthedocs.org
      - pkg: rtd-build-pkgs
    - require:
      - virtualenv: {{ site_path }}

# Site data, load once on successful pip install
{% set venv_python = site_path + '/bin/python' %}
{% set local_settings = site_path + '/checkouts/readthedocs.org/readthedocs/settings/local_settings.py' %}

{{ local_settings }}:
  file.managed:
    - source: salt://readthedocs/site/local_settings.py
    - template: jinja
    - user: docs
    - group: docs
    - require:
      - file: {{ site_path }}/checkouts/readthedocs.org

rtd-db-sync:
  cmd.wait:
    - name:
        {{ venv_python }} manage.py syncdb
        --settings=readthedocs.settings.postgres
        --noinput
    - cwd: {{ site_path }}/checkouts/readthedocs.org
    - user: docs
    - watch:
      - cmd: rtd-deps
    - require:
      - postgres_database: postgresql-docs
      - file: {{ local_settings }}

rtd-db-migrate:
  cmd.wait:
    - name:
        {{ venv_python }} manage.py migrate
        --settings=readthedocs.settings.postgres
    - cwd: {{ site_path }}/checkouts/readthedocs.org
    - user: docs
    - watch:
      - cmd: rtd-db-sync
    - require:
      - postgres_database: postgresql-docs
      - file: {{ local_settings }}

{% if grains['id'] == 'vagrant' %}
rtd-db-loaduser:
  cmd.wait:
    - name:
        {{ venv_python }} manage.py loaddata test_auth
        --settings=readthedocs.settings.postgres
    - cwd: {{ site_path }}/checkouts/readthedocs.org
    - user: docs
    - watch:
      - cmd: rtd-db-migrate

rtd-db-loaddata:
  cmd.wait:
    - name:
        {{ venv_python }} manage.py loaddata test_data
        --settings=readthedocs.settings.postgres
    - cwd: {{ site_path }}/checkouts/readthedocs.org
    - user: docs
    - watch:
      - cmd: rtd-db-loaduser
{% endif %}

# Site build requirements
rtd-vcs-pkgs:
  pkg.installed:
    - pkgs:
      - git-core
      - subversion
      - bzr
    - require:
      - pkg: python-dev

rtd-build-pkgs:
  pkg.installed:
    - pkgs:
      - ipython
      - graphviz
      - libpq-dev
      - libxml2-dev
      - libxslt1-dev

# Services
{% for service in ['gunicorn', 'celery'] %}
/etc/init/readthedocs-{{ service }}.conf:
  file.managed:
    - source: salt://upstart/readthedocs-{{ service }}.conf
    - reload_modules: True
    - require:
      - cmd: rtd-deps
    - watch:
      - cmd: rtd-db-migrate

readthedocs-{{ service }}:
  service.running:
    - enable: True
    - watch:
      - file: /etc/init/readthedocs-{{ service }}.conf
    - require:
      - file: {{ site_path }}/run
      - service: redis-server
{% endfor %}

/etc/nginx/sites-enabled/readthedocs:
  file.managed:
    - source: salt://nginx/sites/readthedocs
    - mode: 0640
    - template: jinja
    - watch_in:
      - service: nginx
    - require:
      - file: /etc/nginx/nginx.conf
      - service: readthedocs-gunicorn
