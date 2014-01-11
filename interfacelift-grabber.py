#! /usr/bin/env python3
import argparse
from urllib import parse
from urllib import request
from urllib import response
import datetime
import os
import sys
import re
from string import Template

class NotModifiedHandler(request.BaseHandler):
    def http_error_304(self, req, fp, code, msg, hdrs):
        addinfourl = response.addinfourl(fp, hdrs, req.get_full_url())
        addinfourl.code = code
        return addinfourl

opener = request.build_opener(NotModifiedHandler())
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20140108 Firefox/24.0')]

class SkipException(Exception):
    pass

class ForceException(Exception):
    pass

class QuitException(Exception):
    pass

class Page:
    def __init__(self, url):
        self.url = url

    pattern = re.compile(r'<select class="select" .*? onChange="javascript:imgload\(\'(?P<base>.*?)\', this,\'(?P<id>\d+)\'\)">\s*(?P<resolution>.*?)\s*</select>.*?</div>\s*</div>\s*</div>\s*<div class="details">\s*<div>\s*<h1 .*?><a .*?>(?P<title>.*?)</a></h1>\s*<div .*?>By <a .*?>(?P<artist>.*?)</a></div>\s*<div .*?>(?P<date>.*?)</div>', re.DOTALL)
    
    def parse(self):
        self.res = opener.open(self.url)
        for match in re.finditer(Page.pattern, self.res.read().decode('utf-8')):
            date = datetime.datetime.strptime(re.sub(r'(st|nd|rd|th),', ',', match.group('date')), '%B %d, %Y')
            yield {'base':match.group('base'),
                   'id':match.group('id').zfill(5),
                   'resolution':match.group('resolution'),
                   'title':match.group('title'),
                   'artist':match.group('artist'),
                   'year':date.strftime('%Y'),
                   'month':date.strftime('%m'),
                   'day':date.strftime('%d'),
                   'MONTH':date.strftime('%b'),
                    }


class Wallpaper:
    def __init__(self, url):
        self.url = url;

    def save(self, path):
        self.req = request.Request(self.url)
        try:
            ltime = round(os.path.getmtime(path))
            self.localtime = datetime.datetime.utcfromtimestamp(ltime)
            if not args.force:
                self.req.add_header('If-Modified-Since', self.localtime.strftime('%a, %d %b %Y %H:%M:%S GMT'))
        except os.error:
            pass

        self.res = opener.open(self.req)
        
        if hasattr(self.res, 'code') and self.res.code == 304:
            raise SkipException
        else:
            self.remotetime = datetime.datetime.strptime(self.res.getheader('Last-Modified'), '%a, %d %b %Y %H:%M:%S GMT')
            mtime = round((self.remotetime - datetime.datetime(1970, 1, 1)).total_seconds())
            self.contents = self.res.read()

            #make directory if needed
            try:
                os.makedirs(os.path.dirname(path))
            except os.error:
                pass
            
            with open(path, 'wb') as f:
                f.write(self.contents)
            #set modified time
            os.utime(path, (mtime, mtime))
            if 'ltime' in locals():
                raise ForceException
        
parser = argparse.ArgumentParser(description='Download wallpaper from interfacelift',
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('width', type=int, help='The width of wallpapers')
parser.add_argument('height', type=int, help='The height of wallpapers')
parser.add_argument('-t', '--template', default='$base', help='Format of saved path\n${base}=northerncastle\n${title}=Northern Castle\n${id}=03467\n${artist}=Nicolas Kamp\n${year}=2014\n${month}=01\n${MONTH}=Jan\n${day}=09')
parser.add_argument('-l', '--limit', default=-1, type=int, help='Number of wallpapers to download(default: %(default)s)')
parser.add_argument('-f', '--force', action='store_const', const=True, default=False, help='Overwrite existed wallpapers')
parser.add_argument('-q', '--quick', action='store_const', const=True, default=False, help='Quit on first skip')
parser.add_argument('--date', dest='sort', action='store_const', const="date", default='date', help='Sort by date(default)')
parser.add_argument('--downloads', dest='sort', action='store_const', const="downloads", default='date', help='Sort by downloads')
parser.add_argument('--rating', dest='sort', action='store_const', const="rating", default='date', help='Sort by rating')
parser.add_argument('--comments', dest='sort', action='store_const', const="comments", default='date', help='Sort by comments')
parser.add_argument('--random', dest='sort', action='store_const', const="random", default='date', help='Sort by random')

args = parser.parse_args()
template = Template(args.template)
page_number = 1
count = 0
empty = True
pattern0 = re.compile('value="%dx%d"' % (args.width, args.height))
paths = []
try:
    while True:
        if count == args.limit:
            break
        page = Page("http://interfacelift.com/wallpaper/downloads/%s/any/index%d.html" % (args.sort, page_number));
        page_number += 1
        for item in page.parse():
            empty = False
            if count == args.limit:
                break
            if re.search(pattern0, item['resolution']):
                del item['resolution']
                item['width'] = int(args.width)
                item['height'] = int(args.height)
                path = template.substitute(item)
                if path in paths:
                    continue
                else:
                    paths.append(path)
                url = parse.urljoin(page.url, '/wallpaper/7yz4ma1/%s_%s_%dx%d.jpg' % (item['id'], item['base'], args.width, args.height))
                wallpaper = Wallpaper(url)
                count += 1
                while True:
                    print('\t%d\t%s' % (count, path), end='\r')
                    try:
                        wallpaper.save(path)
                        print('Saved')
                        break
                    except SkipException:
                        print('Skipped')
                        if args.quick:
                            raise QuitException
                        break
                    except ForceException:
                        print('Forced')
                        break
                    except:
                        print('Failed')
        if empty:
            raise QuitException
except QuitException:
    pass
