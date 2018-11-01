#!/bin/sh

cd /opt/maubot

# Replace database path in config.
sed -i "s#sqlite:///maubot.db#sqlite:////data/maubot.db#" /data/config.yaml
sed -i "s#- ./plugins#- /data/plugins#" /data/config.yaml
sed -i "s#upload: ./plugins#upload: /data/plugins#" /data/config.yaml
sed -i "s#trash: ./trash#trash: /data/trash#" /data/config.yaml
sed -i "s#db: ./plugins#trash: /data/dbs#" /data/config.yaml
sed -i "s#./logs/maubot.log#/var/log/maubot/maubot.log#" /data/config.yaml

mkdir -p /var/log/maubot /data/plugins /data/trash /data/dbs

# Check that database is in the right state
alembic -x config=/data/config.yaml upgrade head

if [ ! -f /data/config.yaml ]; then
	cp example-config.yaml /data/config.yaml
	echo "Config file not found. Example config copied to /data/config.yaml"
	echo "Please modify the config file to your liking and restart the container."
	exit
fi

python3 -m maubot -c /data/config.yaml
