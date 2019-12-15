[![License](https://img.shields.io/badge/license-MIT_license-blue.svg)](https://raw.githubusercontent.com/dblume/md-reader/master/LICENSE.txt)
![python3.x](https://img.shields.io/badge/python-3.x-green.svg)

## Overcast Podcast Activity Feed

You can create a podcast activity feed with this script. Activity feeds are 
records of the things you've done. In this case, it's a list of podcast episodes
you've listened to.  It is similar to a last.fm Scrobble feed.

Activity feeds can be used to collect data for lifestreaming and the Quantified
Self. You can do whatever you want with it, it's your life and your data.

## Getting Started

1. Rename overcast.cfg.sample to overcast.cfg.
2. Customize the variables in overcast.cfg. (More on this below.)
3. Set up a cronjob that runs overcast.py once every day.

## How it works

It downloads your entire user activity history from Overcast, and then makes
an activity feed of the last few podcasts you listened to.

Overcast doesn't have a web API yet, so the script rate-limits itself to about
once or twice a day.

When Overcast provides the API, we'll deprecate this script.

## Customizing overcast.cfg

The configuration file looks like this:

    [main]
    username = user@example.org
    password = correcthorsebatterystaple
    [feed]
    filename = podcast-activity.xml
    href = http://domain.org/%(filename)s
    title = My Overcast Podcast Activity Feed

Replace username and password with your Overcast username and password. Set the
feed filename, location, and title as you like.

## Is it any good?

[Yes](https://news.ycombinator.com/item?id=3067434).

## Licence

This software uses the [MIT license](https://raw.githubusercontent.com/dblume/overcast-podcast-activity-feed/master/LICENSE.txt)
