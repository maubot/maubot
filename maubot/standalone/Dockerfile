FROM docker.io/alpine:3.10

COPY . /opt/maubot
RUN cd /opt/maubot \
  && apk add --no-cache --virtual .build-deps \
      python3-dev \
      libffi-dev \
      build-base \
  && apk add --no-cache \
      py3-aiohttp \
      py3-sqlalchemy \
      py3-attrs \
      py3-bcrypt \
      py3-cffi \
      ca-certificates \
      su-exec \
      py3-psycopg2 \
      py3-ruamel.yaml \
      py3-jinja2 \
      py3-packaging \
      py3-markdown \
  && pip3 install . \
  && apk del .build-deps
