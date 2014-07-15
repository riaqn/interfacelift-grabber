interfacelift-grabber
=====================

Grab selected wallpapers from interfacelift

# Quick Start
```
interfacelift-grabber.py http://interfacelift.com/wallpaper/downloads/date/wide_16:9/1920x1080/
```
Wallpapers will be download into `InterfaceLIFT_1920x1080/author - title.jpg`


# Perform this command regularly to update
```
interfacelift-grabber.py http://interfacelift.com/wallpaper/downloads/date/wide_16:9/1920x1080/ -q
```
-q(--quick) means quit on first skip, saving lots of meaningless skip


# Help
```
usage: interfacelift-grabber.py [-h] [-o OUTPUT] [-f] [-q] [-r RES] [-d] [url]

Grab wallpapers from InterfaceLIFT

positional arguments:
  url                   page to start parsing (default: http://interfacelift.com/wallpaper/downloads/date/any/)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        path template to save wallpaper (default: InterfaceLIFT_{res}/{author} - {title}.jpg)
                        title="Decay"
                        author="picturbex"
                        year=2014
                        month=7
                        day=14
                        base="decay"
                        id=3641
  -f, --force           overwrite exist file even it's right (default: False)
  -q, --quick           quit on first skip (default: False)
  -r RES, --res RES     resolution you want, e.g. 1920x1080
  -d, --debug           print debug message
```
