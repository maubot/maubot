FROM docker.io/alpine:3.10

RUN apk add --no-cache --virtual .build-deps \
      python3-dev \
      libffi-dev \
      build-base \
  && apk add --no-cache \
      py3-aiohttp \
      py3-sqlalchemy \
      py3-attrs \
      py3-bcrypt \
      ca-certificates \
      su-exec \
      py3-psycopg2 \
      py3-ruamel.yaml \
      py3-jinja2 \
      py3-packaging \
      py3-markdown \
  && pip3 install maubot \
  && apk del .build-deps
