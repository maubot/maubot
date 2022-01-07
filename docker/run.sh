#!/bin/sh

function fixperms {
	chown -R $UID:$GID /var/log /data /opt/maubot
}

function fixdefault {
	_value=$(yq e "$1" /data/config.yaml)
	if [[ "$_value" == "$2" ]]; then
		yq e -i "$1 = "'"'"$3"'"' /data/config.yaml
	fi
}

function fixconfig {
	# Change relative default paths to absolute paths in /data
	fixdefault '.database' 'sqlite:///maubot.db' 'sqlite:////data/maubot.db'
	fixdefault '.plugin_directories.upload' './plugins' '/data/plugins'
	fixdefault '.plugin_directories.load[0]' './plugins' '/data/plugins'
	fixdefault '.plugin_directories.trash' './trash' '/data/trash'
	fixdefault '.plugin_directories.db' './plugins' '/data/dbs'
	fixdefault '.plugin_directories.db' './dbs' '/data/dbs'
	fixdefault '.logging.handlers.file.filename' './maubot.log' '/var/log/maubot.log'
	# This doesn't need to be configurable
	yq e -i '.server.override_resource_path = "/opt/maubot/frontend"' /data/config.yaml
}

cd /opt/maubot

mkdir -p /var/log/maubot /data/plugins /data/trash /data/dbs

if [ ! -f /data/config.yaml ]; then
	cp example-config.yaml /data/config.yaml
	# Apply some docker-specific adjustments to the config
	echo "Config file not found. Example config copied to /data/config.yaml"
	echo "Please modify the config file to your liking and restart the container."
	fixperms
	fixconfig
	exit
fi

alembic -x config=/data/config.yaml upgrade head
fixperms
fixconfig
if ls /data/plugins/*.db > /dev/null 2>&1; then
	mv -n /data/plugins/*.db /data/dbs/
fi

exec su-exec $UID:$GID python3 -m maubot -c /data/config.yaml
