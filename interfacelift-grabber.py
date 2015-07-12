#!/usr/bin/env python3
from urllib.request import Request, urlopen

UserAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:30.0) Gecko/20100101 Firefox/30.0';
headers = {'User-Agent':UserAgent};

def date_parse(str):
    import re
    from datetime import datetime
    date_stripped = re.sub(r'(\d)(st|nd|rd|th)', r'\1', str);
    date = datetime.strptime(date_stripped, '%B %d, %Y');
    return {'year': date.year,
            'month': date.month,
            'day': date.day};

def InterfaceLIFT(url):
    while True:
        req = Request(url, headers=headers);
        res = urlopen(req);
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res);


        from urllib.parse import urljoin
        for item in soup.select('html > body > div#main_page_frame > div#container > div#page > div#wallpaper > div > div.item'):
            info = {};
            details = item.select('div.details')[0];
            preview = item.select('div.preview')[0];
            info['title'] = details.select('div > h1 > a')[0].string;
            info['author'] = details.select('div > div > a')[0].string;

            date = details.select('div > div[style*="#444444"]')[0].string;
            info.update(date_parse(date));

            try:
                info['description'] = details.select('div > div > p')[0].string;
            except IndexError:
                info['description'] = None;

            try:
                info['download'] = urljoin(url, preview.select('div.download > div > a > img')[0].parent['href']);
            except IndexError:
                info['download'] = None;
                
            info['downloads'] = {};

            select = preview.select('div.download > select.select')[0];
            import re
            match = re.finditer(r"'(.+?)'", select['onchange']);
            info['base'] = next(match).group(1);
            info['id'] = int(next(match).group(1));

            for option in preview.select('div.download > select.select > optgroup > option'):
                info['downloads'][option['value']] = urljoin(url, '/wallpaper/7yz4ma1/{:>05}_{}_{}.jpg'.format(info['id'], info['base'], option['value']));
            
            info['preview'] = urljoin(url, preview.select('div > a > img')[0]['src']);
            info['refer'] = url;
            yield info;


        try:
            url = urljoin(url, soup.select('a[class^="selector"]')[-1]['href']);
        except KeyError:
            break;

class FailException(Exception):
    pass

class SkipException(Exception):
    pass

def save(req, path, force):
    import os
    res = urlopen(req);

    try:
        localtime = os.path.getmtime(path);
    except os.error:
        localtime = -1;

    try:
        localsize = os.path.getsize(path);
    except os.error:
        localsize = -1;

    time = res.getheader('Last-Modified');
    if time is None:
        print('Failed');
        raise FailException;

    from datetime import datetime
    time = datetime.strptime(time, '%a, %d %b %Y %H:%M:%S GMT').timestamp();

    size = res.getheader('Content-Length');
    if size is None:
        print('Failed');
        raise FailException;
    size = int(size);

    if not force and time == localtime and size == localsize:
        print('Skipped');
        raise SkipException;
        
    try:
        os.makedirs(os.path.dirname(path))
    except os.error:
        pass

    with open(path, 'wb') as file:

        offset = 0;

        for percent in range(100):
            print('{:>2}%'.format(percent), end='\r');
            buffer = res.read(int(round(size / 100 * (percent + 1) - offset)));
            offset += len(buffer);
            file.write(buffer);

    if not len(res.read()) == 0:
        print('Failed');
        raise FailException;
        
    os.utime(path, (time, time));
    
    if time == localtime and size == localsize:
        print('Forced');
    else:
        print('Saved');

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Grab wallpapers from InterfaceLIFT', formatter_class=argparse.RawTextHelpFormatter);

    parser.add_argument('-o', '--output', default='InterfaceLIFT_{res}/{author} - {title}.jpg', help='path template to save wallpaper (default: %(default)s)\ntitle="Decay"\nauthor="picturbex"\nyear=2014\nmonth=7\nday=14\nbase="decay"\nid=3641');
    parser.add_argument('-f', '--force', action='store_true', default=False, help='overwrite exist file even it\'s right (default: %(default)s)');
    parser.add_argument('-q', '--quick', action='store_true', default=False, help='quit on first skip (default: %(default)s)');
    parser.add_argument('-r', '--res', help='resolution you want, e.g. 1920x1080');
    parser.add_argument('url', nargs='?', default='http://interfacelift.com/wallpaper/downloads/date/any/', help='page to start parsing (default: %(default)s)');

    args = parser.parse_args();

    miss = 0;
    try:
        for item in InterfaceLIFT(args.url):
            if args.res is None:
                for res, download in item['downloads'].items():
                    if item['download'] == download:
                        item['res'] = res;
                        break;
            else:
                item['res'] = args.res;
                item['download'] = item['downloads'].get(item['res'], None);

            if item['download'] == None:
                miss += 1;
                if miss % 10 == 0:
                    print('missed {} wallpapers, consider changing --res and url argument'.format(miss));
                continue;
            miss = 0;

            path = args.output.format(**item);
            print(' \t{}'.format(path), end='\r');

            req = Request(item['download'], headers=headers);
            skip = False
            while True:
                try:
                    save(req, path, args.force);
                    break;
                except FailException:
                    pass
                except SkipException:
                    skip = True;
                    break;

            if skip:
                if args.quick:
                    break;
                else:
                    continue;
    except KeyboardInterrupt:
        pass
    finally:
        try:
            print('Last page: {}'.format(item['refer']))
        except:
            pass 

if __name__ == '__main__':
    main();
