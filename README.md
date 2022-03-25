# maubot
![Languages](https://img.shields.io/github/languages/top/maubot/maubot.svg)
[![License](https://img.shields.io/github/license/maubot/maubot.svg)](LICENSE)
[![Release](https://img.shields.io/github/release/maubot/maubot/all.svg)](https://github.com/maubot/maubot/releases)
[![GitLab CI](https://mau.dev/maubot/maubot/badges/master/pipeline.svg)](https://mau.dev/maubot/maubot/container_registry)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

A plugin-based [Matrix](https://matrix.org) bot system written in Python.

## Documentation

All setup and usage instructions are located on
[docs.mau.fi](https://docs.mau.fi/maubot/index.html). Some quick links:

* [Setup](https://docs.mau.fi/maubot/usage/setup/index.html)
  (or [with Docker](https://docs.mau.fi/maubot/usage/setup/docker.html))
* [Basic usage](https://docs.mau.fi/maubot/usage/basic.html)
* [Encryption](https://docs.mau.fi/maubot/usage/encryption.html)

## Discussion
Matrix room: [#maubot:maunium.net](https://matrix.to/#/#maubot:maunium.net)

## Plugins
Open a pull request or join the Matrix room linked above to get your plugin listed here.

The plugin wishlist lives at <https://github.com/maubot/plugin-wishlist/issues>.

### Official plugins
* [sed](https://github.com/maubot/sed) - A bot to do sed-like replacements.
* [factorial](https://github.com/maubot/factorial) - A bot to calculate unexpected factorials.
* [media](https://github.com/maubot/media) - A bot that replies with the MXC URI of images you send it.
* [dice](https://github.com/maubot/dice) - A combined dice rolling and calculator bot.
* [karma](https://github.com/maubot/karma) - A user karma tracker bot.
* [xkcd](https://github.com/maubot/xkcd) - A bot to view xkcd comics.
* [echo](https://github.com/maubot/echo) - A bot that echoes pings and other stuff.
* [rss](https://github.com/maubot/rss) - A bot that posts RSS feed updates to Matrix.
* [reminder](https://github.com/maubot/reminder) - A bot to remind you about things.
* [translate](https://github.com/maubot/translate) - A bot to translate words.
* [reactbot](https://github.com/maubot/reactbot) - A bot that responds to messages that match predefined rules.
* [exec](https://github.com/maubot/exec) - A bot that executes code.
* [commitstrip](https://github.com/maubot/commitstrip) - A bot to view CommitStrips.
* [supportportal](https://github.com/maubot/supportportal) - A bot to manage customer support on Matrix.
* †[gitlab](https://github.com/maubot/gitlab) - A GitLab client and webhook receiver.
* [github](https://github.com/maubot/github) - A GitHub client and webhook receiver.
* [tex](https://github.com/maubot/tex) - A bot that renders LaTeX.
* [altalias](https://github.com/maubot/altalias) - A bot that lets users publish alternate aliases in rooms.
* [satwcomic](https://github.com/maubot/satwcomic) - A bot to view SatWComics.
* [songwhip](https://github.com/maubot/songwhip) - A bot to post Songwhip links.
* [manhole](https://github.com/maubot/manhole) - A plugin that lets you access a Python shell inside maubot.

### 3rd party plugins
* [subreddit linkifier](https://github.com/TomCasavant/RedditMaubot) - A bot that condescendingly corrects a user when they enter an r/subreddit without providing a link to that subreddit
* [giphy](https://github.com/TomCasavant/GiphyMaubot) - A bot that generates a gif (from giphy) given search terms
* [trump](https://github.com/jeffcasavant/MaubotTrumpTweet) - A bot that generates a Trump tweet with the given content
* [poll](https://github.com/TomCasavant/PollMaubot) - A bot that will create a simple poll for users in a room
* [urban](https://github.com/dvdgsng/UrbanMaubot) - A bot that fetches definitions from [Urban Dictionary](https://www.urbandictionary.com/).
* [twilio](https://github.com/jeffcasavant/MaubotTwilio) - Maubot-based SMS bridge
* [tmdb](https://codeberg.org/lomion/tmdb-bot) - A bot that posts information about movies fetched from TheMovieDB.org.
* [invite](https://github.com/williamkray/maubot-invite) - A bot to generate invitation tokens from [matrix-registration](https://github.com/ZerataX/matrix-registration)
* [wolframalpha](https://github.com/ggogel/WolframAlphaMaubot) - A bot that allows requesting information from [WolframAlpha](https://www.wolframalpha.com/).
* †[pingcheck](https://edugit.org/nik/maubot-pingcheck) - A bot to ping the echo bot and send rtt to Icinga passive check
* [ticker](https://github.com/williamkray/maubot-ticker) - A bot to return financial data about a stock or cryptocurrency.
* [weather](https://github.com/kellya/maubot-weather) - A bot to get the weather from wttr.in and return a single line of text for the location specified
* †[youtube previewer](https://github.com/ggogel/YoutubePreviewMaubot) - A bot that responds to a YouTube link with the video title and thumbnail.
* †[reddit previewer](https://github.com/ggogel/RedditPreviewMaubot) - A bot that responds to a link of a reddit post with the sub name and title. If available, uploads the image or video.
* [pocket](https://github.com/jaywink/maubot-pocket) - A bot integrating with Pocket to fetch articles and archive them.
* [alternatingcaps](https://github.com/rom4nik/maubot-alternatingcaps) - A bot repeating last message using aLtErNaTiNg cApS.
* [metric](https://github.com/edwardsdean/maubot_metric_bot) - A bot that will reply to a message that contains imperial units and replace them with metric units.
* [urlpreview](https://github.com/coffeebank/coffee-maubot/tree/master/urlpreview) - A bot that responds to links with a link preview embed, using Matrix API to fetch meta tags

† Uses a synchronous library which can block the whole maubot process (e.g. requests instead of aiohttp)

### Deprecated/unmaintained plugins
* [jesaribot](https://github.com/maubot/jesaribot) - A simple bot that replies with an image when you say "jesari".
  * Superseded by reactbot
* [gitea](https://github.com/saces/maugitea) - A Gitea client and webhook receiver.
