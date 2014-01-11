interfacelift-grabber
=====================

Grab selected wallpapers from interfacelift

Download wallpapers into different directories according to year and month, directories will be created automatically.
```
interfacelift-grabber.py -t 'interfacelift_${width}x${height}/${year}/${month}/${artist}-${title}.jpg' 1280 800
```
Note the single quotes, which avoid the placeholders being explaind by shell


Daily job that you can add to your crontab
```
interfacelift-grabber.py -q -t 'interfacelift/${base}.jpg' 1280 800
```
-q(--quick) means quit on first skip, saving lots of meaningless skip

```
usage: interfacelift-grabber.py [-h] [-t TEMPLATE] [-l LIMIT] [-f] [-q]
                                [--date] [--downloads] [--rating] [--comments]
                                [--random]
                                width height

Download wallpaper from interfacelift

positional arguments:
  width                 The width of wallpapers
  height                The height of wallpapers

optional arguments:
  -h, --help            show this help message and exit
  -t TEMPLATE, --template TEMPLATE
                        Format of saved path
                        ${base}=northerncastle
                        ${title}=Northern Castle
                        ${id}=03467
                        ${artist}=Nicolas Kamp
                        ${year}=2014
                        ${month}=01
                        ${MONTH}=Jan
                        ${day}=09
  -l LIMIT, --limit LIMIT
                        Number of wallpapers to download(default: -1)
  -f, --force           Do not skip, overwrite existed wallpapers even if timestamp and size is correct
  -q, --quick           Quit on first skip
  --date                Sort by date(default)
  --downloads           Sort by downloads
  --rating              Sort by rating
  --comments            Sort by comments
  --random              Sort by random
```