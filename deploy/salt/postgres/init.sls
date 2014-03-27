# PostgreSQL

postgresql:
  pkg:
    - installed
  service.running:
    - enable: True
    - require:
      - pkg: postgresql
      - file: /etc/postgresql/9.1/main/pg_hba.conf

/etc/postgresql/9.1/main/pg_hba.conf:
  file.managed:
    - source: salt://postgres/pg_hba.conf
    - mode: 0755

postgresql-docs:
  postgres_user.present:
    - name: docs
    - password: docs
    - login: True
    - require:
      - service: postgresql
  postgres_database.present:
    - name: docs
    - owner: docs
    - require:
      - postgres_user: postgresql-docs
