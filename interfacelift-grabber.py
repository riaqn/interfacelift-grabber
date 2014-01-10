#! /usr/bin/env python3
import argparse
from urllib import parse
from urllib import request
from urllib import response
import datetime
import os
import re

UA = 'Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20140108 Firefox/24.0'
prefix = 'http://interfacelift.com'

class Page:
    def __init__(self, url):
        self.url = url

    pattern = re.compile('<a href="(.*?\.jpg)">')
    def parse(self):
        self.req = request.Request(self.url)
        self.req.add_header('User-Agent', UA)
        self.res = request.urlopen(self.req)
        for match in re.finditer(Page.pattern, self.res.read().decode('utf-8')):
            yield parse.urljoin(self.url, match.group(1))

class NotModifiedHandler(request.BaseHandler):
    def http_error_304(self, req, fp, code, msg, hdrs):
        addinfourl = response.addinfourl(fp, hdrs, req.get_full_url())
        addinfourl.code = code
        return addinfourl

class Wallpaper:
    def __init__(self, url):
        self.url = url;

    def save(self, path):
        self.req = request.Request(self.url)
        self.req.add_header('User-Agent', UA)

        try:
            self.localtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(path))
            self.req.add_header('If-Modified-Since', self.localtime.strftime('%a, %d %b %Y %H:%M:%S GMT'))
        except os.error:
            pass
        opener = request.build_opener(NotModifiedHandler())

        self.res = opener.open(self.req)
        if hasattr(self.res, 'code') and self.res.code == 304:
            print('Skipped')
        else:
            self.remotetime = datetime.datetime.strptime(self.res.getheader('Last-Modified'), '%a, %d %b %Y %H:%M:%S GMT')
            self.contents = self.res.read()
            with open(path, 'wb') as f:
                f.write(self.contents)
            mtime = round((self.remotetime - datetime.datetime(1970, 1, 1)).total_seconds())
            os.utime(path, (mtime, mtime))
            print('Saved')
        
parser = argparse.ArgumentParser(description='Download interfacelift Wallpaper')
parser.add_argument('resolution', help='The resolution of wallpapers')
parser.add_argument('directory', help='Directory to save wallpapers')
parser.add_argument('-l', '--limit', default=-1, type=int, help='Number of wallpapers to download')
parser.add_argument('--date', dest='sort', action='store_const', const="date", default='date', help='sort by date')
parser.add_argument('--downloads', dest='sort', action='store_const', const="downloads", default='date', help='sort by downloads')
parser.add_argument('--rating', dest='sort', action='store_const', const="rating", default='date', help='sort by rating')
parser.add_argument('--comments', dest='sort', action='store_const', const="comments", default='date', help='sort by comments')
parser.add_argument('--random', dest='sort', action='store_const', const="random", default='date', help='sort by random')

args = parser.parse_args()
page_number = 1
count = 0
while True:
    if count == args.limit:
        break
    page = Page("%s/wallpaper/downloads/%s/%s/index%d.html" % (prefix, args.sort, args.resolution, page_number));
    page_number += 1
    stop = True
    for url in page.parse():
        stop = False
        if count == args.limit:
            break
        count += 1
        wallpaper = Wallpaper(url)
        while True:
            print(count, end='\t')
            path = os.path.join(args.directory, os.path.basename(wallpaper.url))
            print(path, end='\t')
            try:
                wallpaper.save(path)
                break
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except:
                print('Failed')
    if stop:
        break
