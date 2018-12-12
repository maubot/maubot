FROM node:10 AS frontend-builder

COPY ./maubot/management/frontend /frontend
RUN cd /frontend && yarn --prod && yarn build

FROM alpine:3.8

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
      ca-certificates \
      su-exec \
 && pip3 install -r requirements.txt

VOLUME /data

CMD ["/opt/maubot/docker/run.sh"]
