#!/usr/bin/env python3
import os
import sys
import requests
from argparse import ArgumentParser
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import cfgreader
import logging
import time


class Episode:
    def __init__(self, podcast, title, url, guid, date):
        self.podcast = podcast
        self.title = title
        self.url = url
        self.guid = guid
        self.date = date

    def __lt__(self, other):
        return self.date < other.date

    def __str__(self):
        return f"podcast={self.podcast}, title:{self.title}, date:{self.date}"

    def rss(self):
        date = self.date
        # Convert %z timezone from "-04:00" to "-0400"
        if date[-6] in ('-', '+') and date[-3] == ':':
            date = date[:-3] + date[-2:]
        t = time.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
        date = time.strftime("%a, %d %b %Y %H:%M:%S " + date[-5:], t)
        return (f"<item>"
                f"<title>{escape(self.podcast)}: {escape(self.title)}</title>"
                f"<pubDate>{date}</pubDate>"
                f"<link>{self.url}</link>"
                f"<guid isPermaLink=\"true\">{self.guid}</guid>"
                f"<description><![CDATA[{self.podcast}: {self.title} on {date}]]></description>"
                f"</item>\n")


def download(cfg):
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


def write_feed(episodes, cfg):
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
        for e in episodes[:20]:
            f.write(e.rss())
        f.write("</channel></rss>\n")
    return update_status


def rate_limited(fname):
    """Returns true if we wrote to the file too recently."""
    try:
        mtime_sec = os.path.getmtime(fname)
        return (time.time() - mtime_sec) < 60 * 60 * 11
    except FileNotFoundError as e:
        logging.debug(f"Could not find {fname} {e}.")
        return False


def add_episode(ep):
    """Returns True if the episode should be added to the list."""
    if 'played' in ep.attrib:
        return True
    else:
        # progress is number of seconds played. Let's say 5min counts.
        return int(ep.attrib['progress']) > 60 * 5


def main(do_download):
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

    episodes = list()
    for rss in root.findall('.//outline[@type="rss"]'):
        rss_title = rss.attrib['title']
        for ep in rss.findall('outline[@type="podcast-episode"]'):
            if add_episode(ep):
                episodes.append(Episode(rss_title, ep.attrib['title'], ep.attrib['url'],
                    ep.attrib['overcastUrl'], ep.attrib['userUpdatedDate']))
    episodes.sort(reverse=True)
    update_status = write_feed(episodes, cfg)
    logging.info(f"{time.time() - start_time:2.0f}s {update_status}")


if __name__ == '__main__':
    parser = ArgumentParser(description="Make a podcast activity feed.")
    parser.add_argument('-n', '--nodownload', action='store_true')
    parser.add_argument('-o', '--outfile')
    args = parser.parse_args()
    if args.outfile is None:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(args.outfile)
    logging.basicConfig(handlers=(handler,),
                        format='%(asctime)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M',
                        level=logging.INFO)
    main(not args.nodownload)
