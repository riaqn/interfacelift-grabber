#! /usr/bin/env python3
import argparse
from http import client
from urllib.parse import urlparse
import datetime
import os
import sys
import re
from string import Template

headers = {'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20140108 Firefox/24.0'}
host = 'interfacelift.com'

class SkipException(Exception):
    pass

class ForceException(Exception):
    pass

class FailException(Exception):
    pass

class QuitException(Exception):
    pass

class Page:
    def __init__(self, url):
        self.url = url

    pattern = re.compile(r'<select class="select" .*? onChange="javascript:imgload\(\'(?P<base>.*?)\', this,\'(?P<id>\d+)\'\)">\s*(?P<resolution>.*?)\s*</select>.*?</div>\s*</div>\s*</div>\s*<div class="details">\s*<div>\s*<h1 .*?><a .*?>(?P<title>.*?)</a></h1>\s*<div .*?>By <a .*?>(?P<artist>.*?)</a></div>\s*<div .*?>(?P<date>.*?)</div>', re.DOTALL)
    
    def parse(self):
        self.conn = client.HTTPConnection(host)
        self.conn.request('GET', self.url, headers=headers)
        self.res = self.conn.getresponse()
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
        self.conn = client.HTTPConnection(host)
        self.conn.request('GET', self.url, headers=headers)
        self.res = self.conn.getresponse()
        self.url = urlparse(self.res.getheader('Location')).path
        self.res.read()
        self.conn.request('GET', self.url, headers=headers)
        self.res = self.conn.getresponse()
        
        try:
            self.localtime = round(os.path.getmtime(path))
            self.localsize = round(os.path.getsize(path))
        except os.error:
            self.localtime = 0
            self.localsize = 0

        try:
            time = datetime.datetime.strptime(self.res.getheader('Last-Modified'), '%a, %d %b %Y %H:%M:%S GMT')
            self.size = int(self.res.getheader('Content-Length'))
        except TypeError:
            raise FailException
        else:
            self.time = round((time - datetime.datetime(1970, 1, 1)).total_seconds())


        if (not args.force and self.localtime == self.time and self.localsize == self.size):
            self.conn.close()
            raise SkipException
            
        try:
            os.makedirs(os.path.dirname(path))
        except os.error:
            pass

        self.lsize = 0;
        with open(path, 'wb') as f:
            while self.lsize < self.size:
                buffer = self.res.read(int(self.size / 100))
                f.write(buffer)
                self.lsize += len(buffer)
                print('{0:6d}%'.format(int(self.lsize * 100 / self.size)), end='\r')
        os.utime(path, (self.time, self.time))
        if (args.force and self.localtime == self.time and self.localsize == self.size):
            raise ForceException
        
parser = argparse.ArgumentParser(description='Download wallpaper from interfacelift', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('width', type=int, help='The width of wallpapers')
parser.add_argument('height', type=int, help='The height of wallpapers')
parser.add_argument('-t', '--template', default='$base', help='Format of saved path\n${base}=northerncastle\n${title}=Northern Castle\n${id}=03467\n${artist}=Nicolas Kamp\n${year}=2014\n${month}=01\n${MONTH}=Jan\n${day}=09')
parser.add_argument('-l', '--limit', default=-1, type=int, help='Number of wallpapers to download(default: %(default)s)')
parser.add_argument('-f', '--force', action='store_const', const=True, default=False, help='Do not skip, overwrite existed wallpapers even if timestamp and size is correct')
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
pattern0 = re.compile('value="%dx%d"' % (args.width, args.height))
paths = []
try:
    while True:
        if count == args.limit:
            break
        page = Page("/wallpaper/downloads/%s/any/index%d.html" % (args.sort, page_number));
        page_number += 1
        empty = True
        for item in page.parse():
            empty = False
            if count == args.limit:
                break
            if re.search(pattern0, item['resolution']):
                del item['resolution']
                item['width'] = int(args.width)
                item['height'] = int(args.height)
                path = template.substitute(item)
                url = '/wallpaper/7yz4ma1/%s_%s_%dx%d.jpg' % (item['id'], item['base'], args.width, args.height)
                if path + url in paths:
                    continue
                else:
                    paths.append(path + url)
                wallpaper = Wallpaper(url)
                count += 1
                while True:
                    print(''.rjust(7), repr(count).rjust(5), path, end='\r')
                    try:
                        wallpaper.save(path)
                        print('Saved'.rjust(7))
                        break
                    except SkipException:
                        print('Skipped'.rjust(7))
                        if args.quick:
                            raise QuitException
                        break
                    except ForceException:
                        print('Forced'.rjust(7))
                        break
                    except FailException:
                        print('Failed'.rjust(7))
        if empty:
            raise QuitException
except QuitException:
    pass
finally:
    print()

