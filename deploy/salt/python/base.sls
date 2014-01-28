# Python environment requires

python-dev:
  pkg:
    - installed

python-setuptools:
  pkg:
    - installed

# Install pip, virtualenv
python-pip:
  cmd.run:
    - cwd: /
    - name: easy_install --script-dir=/usr/bin -U pip==1.5.1
    - unless: which pip && pip --version | grep -oP 'pip 1.5.1'
    - require:
      - pkg: python-setuptools
    # Required to rehash fresh pip
    - reload_modules: True

python-virtualenv:
  pip.installed:
    - name: virtualenv==1.11.1
    - require:
      - cmd: python-pip
