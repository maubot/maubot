# maubot
A plugin-based [Matrix](https://matrix.org) bot system written in Python.

### [Wiki](https://github.com/maubot/maubot/wiki)

### Usage
In order to create a bot from a basic configuration, clone this repository.
Cloning is only required to reuse some necessary configuration files. It is not necessary to clone the repository
in order to install maubot.
This can be done via `pip install maubot`.
From now on we refer to the directory where this repository has been cloned to as `maubot`.

The new bot will have its own directory, which can be created anywhere on the local filesystem with
`mkdir <bot_dir>` where `<bot_dir>` is a name of your choice.

Copy `maubot/example-config.yaml` to `<bot_dir>`.

Keep file `example-config.yaml` and copy it to `<bot_dir>/config.yaml`. At this point `<bot_dir>` will contain
both `example-config.yaml` and `config.yaml`.
In the same directory `<bot_dir>` create three directories that will be used by the bot later. Type

```
cd <bot_dir>

mkdir logs plugins trash
```

Before running the bot, edit `config.yaml` in all its sections.
In particular in section `plugin_directories` make sure that the bot will use the directories created before (`./trash` and `./plugins`).

Section `server` is self explanatory in its default.
Make sure it looks like below
```
server:
    # The IP and port to listen to.
    hostname: 0.0.0.0
    port: 29316
```
In any case, use the same `port` when you will point the browser later.

Section `admins` should be configured with the username and password that will login to the bot manager page.
If `username` needs to login with password `1234`, this section will look like below

```
admins:
    username: "1234"
```

At this point launch the bot manager.
From directory `<bot_dir>` launch  

```
python -m maubot
```

and point the browser to `http://localhost:29316/_matrix/maubot/#/login`

After login, it is possible to create a new bot instance (clicking the + Instances button) via the screen like the one below ![alt text](https://github.com/maubot/maubot/blob/master/maubot/img/screenshot_new_instance.png "New instance")


### [Management API spec](https://github.com/maubot/maubot/blob/master/maubot/management/api/spec.md)

## Discussion
Matrix room: [#maubot:maunium.net](https://matrix.to/#/#maubot:maunium.net)

## Plugins
* [jesaribot](https://github.com/maubot/jesaribot) - A simple bot that replies with an image when you say "jesari".
* [sed](https://github.com/maubot/sed) - A bot to do sed-like replacements.
* [factorial](https://github.com/maubot/factorial) - A bot to calculate unexpected factorials.
* [media](https://github.com/maubot/media) - A bot that replies with the MXC URI of images you send it.
* [dice](https://github.com/maubot/dice) - A combined dice rolling and calculator bot.
* [karma](https://github.com/maubot/karma) - A user karma tracker bot.
* [xkcd](https://github.com/maubot/xkcd) - A bot to view xkcd comics.
* [echo](https://github.com/maubot/echo) - A bot that echoes pings and other stuff.
* [rss](https://github.com/maubot/rss) - A bot that posts RSS feed updates to Matrix.

### Upcoming
* dictionary - A bot to get the dictionary definitions of words.
* poll - A simple poll bot.
* reminder - A bot to ping you about something after a certain amount of time.
* github - A GitHub client and webhook receiver bot.
* wolfram - A Wolfram Alpha bot
* gitlab - A GitLab client and webhook receiver bot.
