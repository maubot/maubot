FROM docker.io/alpine:3.15

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
      py3-markdown \
      py3-cffi \
      py3-olm \
      py3-pycryptodome \
      py3-unpaddedbase64

COPY requirements.txt /opt/maubot/requirements.txt
COPY optional-requirements.txt /opt/maubot/optional-requirements.txt
RUN cd /opt/maubot \
  && apk add --no-cache --virtual .build-deps \
      python3-dev \
      libffi-dev \
      build-base \
  && pip3 install -r requirements.txt -r optional-requirements.txt \
  && apk del .build-deps

COPY . /opt/maubot
RUN cd /opt/maubot && pip3 install .
