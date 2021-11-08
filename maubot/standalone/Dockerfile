FROM docker.io/alpine:3.14

RUN apk add --no-cache \
      python3 py3-pip py3-setuptools py3-wheel \
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
      py3-markdown

COPY requirements.txt /opt/maubot/requirements.txt
RUN cd /opt/maubot \
  && apk add --no-cache --virtual .build-deps \
      python3-dev \
      libffi-dev \
      build-base \
  && pip3 install -r requirements.txt \
  && apk del .build-deps

COPY . /opt/maubot
RUN cd /opt/maubot && pip3 install .
