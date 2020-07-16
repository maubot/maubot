#!/bin/sh

function fixperms {
    chown -R $UID:$GID /var/log /data /opt/maubot
}

cd /opt/maubot

mkdir -p /var/log/maubot /data/plugins /data/trash /data/dbs /data/crypto

if [ ! -f /data/config.yaml ]; then
	cp docker/example-config.yaml /data/config.yaml
	echo "Config file not found. Example config copied to /data/config.yaml"
	echo "Please modify the config file to your liking and restart the container."
	fixperms
	exit
fi

alembic -x config=/data/config.yaml upgrade head
fixperms
exec su-exec $UID:$GID python3 -m maubot -c /data/config.yaml -b docker/example-config.yaml
