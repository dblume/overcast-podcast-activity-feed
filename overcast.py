#!/usr/bin/env python3
"""Generates an RSS activity feed from your Overcast podcast listening history."""

from __future__ import annotations
import os
import sys
import requests
from argparse import ArgumentParser
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import cfgreader
import logging
import time
from typing import List

__author__ = "David Blume"
__copyright__ = "Copyright 2019-2022, David Blume"
__license__ = "MIT"
__version__ = "1.0"

class Episode:
    def __init__(self, podcast, title, url, guid, date, partial):
        self.podcast = podcast
        self.title = title
        self.url = url
        self.guid = guid
        self.date = date
        self.partial = partial

    def __lt__(self, other: Episode) -> bool:
        return self.date < other.date

    def __str__(self) -> str:
        return f"podcast={self.podcast}, title:{self.title}, date:{self.date}"

    def std_date(self) -> str:
        """If necessary convert %z timezone from '-04:00' to '-0400'."""
        if self.date[-6] in ('-', '+') and self.date[-3] == ':':
            return self.date[:-3] + self.date[-2:]
        return self.date

    def rss(self) -> str:
        date = self.std_date()
        t = time.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
        date = time.strftime("%a, %d %b %Y %H:%M:%S " + date[-5:], t)
        return (f"<item>"
                f"<title>{escape(self.podcast)}: {escape(self.title)}</title>"
                f"<pubDate>{date}</pubDate>"
                f"<link>{escape(self.url)}</link>"
                f"<guid isPermaLink=\"true\">{self.guid}</guid>"
                f"<description><![CDATA[{self.podcast}: {self.title} on {date}]]></description>"
                f"</item>\n")


def reconcile_with_feed(episodes: List[Episode], feed: str) -> List[Episode]:
    """An episode might've already been published in the feed, and then
    have a later timestamp in this list of episodes. When that happens,
    retain the already published information."""
    r = requests.get(feed)
    if not r.ok:
        return episodes
    root = ET.fromstring(r.text)
    dates = dict()  # guid to pubDate
    for i in root.findall('./channel/item'):
        pubDate = i.findtext('pubDate')
        date = time.strptime(pubDate[5:-6], "%d %b %Y %H:%M:%S")
        guid = i.findtext('guid')
        dates[guid] = time.strftime("%Y-%m-%dT%H:%M:%S" + pubDate[-5:], date)

    episode_changed = False
    for episode in episodes:
        if episode.guid in dates and dates[episode.guid] != episode.std_date():
            episode.date = dates[episode.guid]
            episode_changed = True
    if episode_changed:
        episodes.sort(reverse=True)
    return episodes


def download(cfg: cfgreader.CfgReader) -> str:
    """Downloads a custom OPML file from overcast.fm"""
    payload = {
        "email": cfg.main.username,
        "password": cfg.main.password,
        "then": "account"}
    url_base = "https://overcast.fm/"
    with requests.Session() as session:
        r = session.post(url_base + "login", data=payload)
        if not r.ok:
            raise Exception("Could not login. " + r.reason)
        opml = session.get(url_base + "account/export_opml/extended")
        if not opml.ok:
            raise Exception("Could not get opml. " + opml.reason)
    return opml.text


def write_feed(episodes: List[Episode], cfg) -> str:
    update_status = "OK"
    now = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    with open(cfg.feed.filename, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n'
                '<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">\n')
        f.write(f'<channel>\n'
                f'<atom:link href="{cfg.feed.href}" rel="self" type="application/rss+xml" />'
                f'<title>{cfg.feed.title}</title>'
                f'<link>https://overcast.fm</link><pubDate>{now}</pubDate>'
                f'<description>{cfg.feed.title}</description><language>en-us</language>\n')
        for e in episodes:
            f.write(e.rss())
        f.write("</channel></rss>\n")
    return update_status


def rate_limited(fname: str) -> bool:
    """Returns true if we wrote to the file too recently."""
    try:
        mtime_sec = os.path.getmtime(fname)
        return (time.time() - mtime_sec) < 60 * 60 * 11
    except FileNotFoundError as e:
        logging.debug(f"Could not find {fname} {e}.")
        return False


def add_episode(ep: ET.Element) -> bool:
    """Returns True if the episode should be added to the list."""
    if 'played' in ep.attrib:
        return True
    elif 'progress' in ep.attrib:
        # progress is number of seconds played. Let's say 7min counts.
        return int(ep.attrib['progress']) > 60 * 7
    elif 'userDeleted' in ep.attrib:
        return False
    # Neither played nor deleted nor any progress? Let's not add this one yet.
    logging.warning(f"{ep.attrib['overcastId']}: \"{ep.attrib['title']}\" was neither played nor had progress.")
    logging.warning(f'Attributes were: {",".join(ep.attrib.keys())}')
    return False


def main(do_download: bool) -> None:
    """The main function, does the whole thing."""
    start_time = time.time()
    cfg = cfgreader.CfgReader(__file__.replace('.py', '.cfg'))
    cache = __file__.replace('.py', '.opml')
    if do_download and not rate_limited(cache):
        opml = download(cfg)
        logging.debug("Downloaded latest episode activity.")
        with open(cache, "w", encoding="utf-8") as f:
            f.write(opml)
        root = ET.fromstring(bytes(opml, encoding="utf-8"))
    else:
        logging.debug("Using cached episode activity.")
        root = ET.parse(cache)

    episodes: List[Episode] = list()
    for rss in root.findall('.//outline[@type="rss"]'):
        rss_title = rss.attrib['title']
        for ep in rss.findall('outline[@type="podcast-episode"]'):
            if add_episode(ep):
                episodes.append(Episode(rss_title, ep.attrib['title'], ep.attrib['url'],
                    ep.attrib['overcastUrl'], ep.attrib['userUpdatedDate'],
                    'progress' in ep.attrib))
    episodes.sort(reverse=True)

    # I'm seeing too many duplicate partial posts. Experiment: Try not listing
    # the most recent episode if it has only been partially heard.
    # It'll likely get listed later.
    if episodes[0].partial:
        episodes.pop(0)

    episodes = reconcile_with_feed(episodes[:20], cfg.feed.href)

    update_status = write_feed(episodes, cfg)
    logging.info(f"{time.time() - start_time:2.0f}s {update_status}")


if __name__ == '__main__':
    parser = ArgumentParser(description="Make a podcast activity feed.")
    parser.add_argument('-n', '--nodownload', action='store_true')
    parser.add_argument('-o', '--outfile')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    if args.outfile is None:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(args.outfile)
    logging.basicConfig(handlers=(handler,),
                        format='%(asctime)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M',
                        level=logging.DEBUG if args.verbose else logging.INFO)
    main(not args.nodownload)
