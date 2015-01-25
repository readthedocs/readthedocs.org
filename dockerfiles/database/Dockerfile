#
# readthedocs.org - database image
#

FROM    readthedocs/base

RUN     apt-get update && apt-get install -y \
            postgresql-9.4 \
            postgresql-contrib-9.4

ADD     local_settings.py /rtd/readthedocs/local_settings.py
ADD     create_superuser.py /rtd/readthedocs/create_superuser.py

USER    postgres

# See https://github.com/rtfd/readthedocs.org/issues/773
# for the reason behind `migrate projects 0001` line
RUN     /etc/init.d/postgresql start && \
        psql --command "CREATE USER docs WITH SUPERUSER PASSWORD 'password';" && \
        createdb docs && \
        ../venv/bin/python ./manage.py syncdb --noinput && \
        ../venv/bin/python ./manage.py migrate projects 0001 && \
        ../venv/bin/python ./manage.py migrate && \
        ../venv/bin/python ./create_superuser.py && \
        ../venv/bin/python ./manage.py loaddata test_data && \
        /etc/init.d/postgresql stop

ADD     etc/pg_hba.conf /etc/postgresql/9.4/main/pg_hba.conf
RUN     echo "listen_addresses='*'" >> /etc/postgresql/9.4/main/postgresql.conf

# Add VOLUMEs to allow backup of config, logs and databases
VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]

EXPOSE  5432
CMD ["/usr/lib/postgresql/9.4/bin/postgres", "-D", "/var/lib/postgresql/9.4/main", "-c", "config_file=/etc/postgresql/9.4/main/postgresql.conf"]

