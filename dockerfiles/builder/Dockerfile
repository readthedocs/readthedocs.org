

# TODO: It would be nice to have a separate code repo for the task workers, or
# a common base image for python dependencies
FROM    rtd_webapp

# For some reason the task running runs virtualenv-2.7
RUN     ln -s /usr/bin/virtualenv /usr/bin/virtualenv-2.7

# Dependencies for building documentation
RUN     apt-get update && apt-get install -y \
            texlive-latex-base \
            texlive-latex-extra \
            texlive-latex-recommended \
            texlive-fonts-recommended

CMD     ../venv/bin/python manage.py celery worker -l INFO
