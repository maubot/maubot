FROM node:10 AS frontend-builder

COPY ./maubot/management/frontend /frontend
RUN cd /frontend && yarn --prod && yarn build

FROM alpine:3.9

ENV UID=1337 \
    GID=1337

COPY . /opt/maubot
COPY --from=frontend-builder /frontend/build /opt/maubot/frontend
WORKDIR /opt/maubot
RUN apk add --no-cache \
      py3-aiohttp \
      py3-sqlalchemy \
      py3-attrs \
      py3-bcrypt \
      py3-cffi \
      build-base \
      python3-dev \
      ca-certificates \
      su-exec \
      py3-pillow \
      py3-magic \
      py3-psycopg2 \
 && pip3 install -r requirements.txt feedparser dateparser
# TODO remove pillow, magic and feedparser when maubot supports installing dependencies

VOLUME /data

CMD ["/opt/maubot/docker/run.sh"]
