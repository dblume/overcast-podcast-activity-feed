[![License](https://img.shields.io/badge/license-MIT_license-blue.svg)](https://raw.githubusercontent.com/dblume/overcast-podcast-activity-feed/main/LICENSE.txt)
![python3.x](https://img.shields.io/badge/python-3.x-green.svg)

## Overcast Podcast Activity Feed

You can create a podcast activity feed with this script. Activity feeds are
records of the things you've done. In this case, it's a list of podcast episodes
you've listened to.  It is similar to a last.fm Scrobble feed.

Activity feeds can be used to collect data for lifestreaming and for the Quantified
Self projects.

Many thanks to [Overcast.fm](https://overcast.fm/) for granting its users access
to their data.

## Getting Started

1. Install the required module(s):  `python3 -m pip install -r requirements.txt`
2. Rename overcast.cfg.sample to overcast.cfg.
3. Customize the variables in overcast.cfg. (More on this below.)
4. Set up a cronjob that runs overcast.py once every day.

You can specify an output file for logs with the -o flag, like so:

    ./overcast.py -o overcast.log

The feed will be written to the filename specified in overcast.cfg, in this
example, it'd be an RSS feed named "podcast-activity.xml"

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

### Protect your password

If overcast.cfg is present on your server that's serving the RSS feed, be sure
to deny access to it. If you have a .htaccess file, you can do so with

    <Files ~ "\.cfg$">
    Order allow,deny
    Deny from all
    </Files>


## An example feed

Here's [an example feed](http://feed.dlma.com/overcast.xml). It [meets RSS validation requirements](https://validator.w3.org/feed/check.cgi?url=http%3A//feed.dlma.com/overcast.xml). &check;

## Is it any good?

[Yes](https://news.ycombinator.com/item?id=3067434).

## Licence

This software uses the [MIT license](https://raw.githubusercontent.com/dblume/overcast-podcast-activity-feed/master/LICENSE.txt)
