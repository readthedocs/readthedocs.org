FROM python:3.6.7-alpine

WORKDIR /usr/src/app

COPY requirements ./requirements

RUN apk update && \
  apk add --no-cache git build-base libxml2 libxml2-dev libxslt-dev \
  openjpeg-dev tiff-dev musl-dev postgresql-dev && \
  pip install --no-cache-dir -r requirements/deploy.txt

COPY . .

CMD ["./web-entrypoint.sh"]
