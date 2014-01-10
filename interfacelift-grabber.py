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

        while True:
            self.res = opener.open(self.req)
            if hasattr(self.res, 'code') and self.res.code == 304:
                print('Skipped')
                break
            else:
                self.contents = self.res.read()
                try:
                    self.remotetime = datetime.datetime.strptime(self.res.getheader('Last-Modified'), '%a, %d %b %Y %H:%M:%S GMT')
                except TypeError:
                    continue
                
                print('Saved')
                with open(path, 'wb') as f:
                    f.write(self.contents)
                mtime = round((self.remotetime - datetime.datetime(1970, 1, 1)).total_seconds())
                os.utime(path, (mtime, mtime))
                break
        
parser = argparse.ArgumentParser(description='Download interfacelift Wallpaper')
parser.add_argument('resolution', help='The resolution of wallpapers')
parser.add_argument('directory', help='Directory to save wallpapers')
parser.add_argument('-l', '--limit', default=-1, type=int, help='Number of wallpapers to download')
args = parser.parse_args()
page_number = 1
count = 0
while True:
    if count == args.limit:
        break
    page = Page("%s/wallpaper/downloads/date/%s/index%d.html" % (prefix, args.resolution, page_number));
    page_number += 1
    for url in page.parse():
        if count == args.limit:
            break
        count += 1
        wallpaper = Wallpaper(url)
        print(count, end='\t')
        path = os.path.basename(wallpaper.url)
        print(path, end='\t')
        wallpaper.save(path)
