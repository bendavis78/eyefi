#!/usr/bin/python

# EyeFi Python Server
#
# Copyright (C) 2010 Robert Jordens
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os

from eyefi.google_loc import google_loc
from eyefi.exif_gps import write_gps


def mac_fmt(mac):
    return ":".join(mac[2*i:2*i+2] for i in range(6))


def eyefi_parse(logfile):
    photos, aps = {}, {}
    for line in open(logfile):
        power_secs, secs, event = line.strip().split(",", 2)
        event = event.split(",")
        event, args = event[0], event[1:]
        if event == "POWERON":
            yield photos, aps
            photos, aps = {}, {}
        elif event in ("AP", "NEWAP"):
            mac, strength, data = args
            aps.setdefault(mac, []).append({
                "power_secs": int(power_secs),
                "secs": int(secs),
                "signal_to_noise": int(strength),
                "data": int(data, 16),
                })
        elif event == "NEWPHOTO":
            filename, size = args
            photos[filename] = {
                "power_secs": int(power_secs),
                "secs": int(secs),
                "size": int(size),
                }
        else:
            raise ValueError, "unknown event %s" % line
        yield photos, aps


def photo_macs(photo, aps):
    t = photo["power_secs"]
    macs = []
    for mac in aps:
        seen = min([(abs(m["power_secs"] - t), m["signal_to_noise"])
            for m in aps[mac]], key=lambda a: a[0])
        if seen[0] <= 3600:
            macs.append({"mac_address": mac_fmt(mac),
                         "age": seen[0]*1000,
                         "signal_to_noise": seen[1]})
    return macs


def write_loc(loc, photo):
    loc = loc["location"]
    write_gps(photo,
        loc["latitude"], loc["longitude"], loc.get("altitude",
            None), "WGS-84", loc.get("accuracy", None))
    return loc, photo


def tag_photo(photoname, log):
    dir, name = os.path.split(photoname)
    data = list(eyefi_parse(log))
    for photos, aps in data[::-1]: # take newest first
        if name in photos:
            macs = photo_macs(photos[name], aps)
            loc = google_loc(wifi_towers=macs)
            loc.addCallback(write_loc, photoname)
            return photos[name], loc


def main():
    import sys
    from twisted.internet import reactor
    from twisted.python import log

    log.startLogging(sys.stdout)
    photo, d = tag_photo(*sys.argv[1:])
    d.addBoth(log.msg).addBoth(lambda e: reactor.callLater(0,
        reactor.stop))
    reactor.run()

if __name__ == '__main__':
    main()
