#!/usr/bin/python

# EyeFi Python Server v3.0
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



import math
import os

from xml.etree import cElementTree as ET

import pyexiv2
assert pyexiv2.version_info[1] >= 2, "need at least pyexiv 0.2.2"


__x = ET.Element("x:xmpmeta")
__x.set("xmlns:x", "adobe:ns:meta/")
__x.set("x:xmptk", "XMP Core 4.4.0-Exiv2")
__sidecar_template = ET.ElementTree(__x)


def xmp_sidecar(filename, sidecar=None):
    """
    returns an xmp sidecar for 'filename', either called 'sidecar' or 
    filename.xmp. copies known exif and iptc tags there, but not xmp
    (does not overwrite existing xmp sidecar data).
    
    returns the sidecar dirty (needs to be written)
    """
    if sidecar is None:
        sidecar = filename+".xmp"
    if not os.access(sidecar, os.R_OK):
        __sidecar_template.write(sidecar)
    i = pyexiv2.metadata.ImageMetadata(filename)
    i.read()
    j = pyexiv2.metadata.ImageMetadata(sidecar)
    j.read()
    i.copy(j, exif=True, iptc=True, xmp=False, comment=False)
    # j.write()
    return j


def write_gps(filename, lat, lon, alt=None, datum="WGS-84",
        dop=None, sidecar=True):
    if sidecar:
        i = xmp_sidecar(filename)
    else:
        i = pyexiv2.metadata.ImageMetadata(filename)
        i.read()
    i["Xmp.exif.GPSVersionID"] = "2 0 0 0"
    i["Xmp.exif.GPSMapDatum"] = datum
    if alt is None:
        i["Xmp.exif.GPSAltitudeRef"] = 0
        i["Xmp.exif.GPSMeasureMode"] = "2"

    else:
        i["Xmp.exif.GPSAltitudeRef"] = 1
        i["Xmp.exif.GPSAltitude"] = pyexiv2.Rational(int(alt*100), 100)
        i["Xmp.exif.GPSMeasureMode"] = "3"

    if dop is not None:
        i["Xmp.exif.GPSDOP"] = pyexiv2.Rational(int(dop*10), 10)

    if lat < 0:
        r = "S";
        lat *= -1
    else:
        r = "N";
    b, a = math.modf(lat)
    c, b = math.modf(b*60)
    c = int(c*60)
    i["Xmp.exif.GPSLatitude"] = pyexiv2.utils.GPSCoordinate(a, b, c, r)
 
    if lon < 0:
        r = "W";
        lon *= -1
    else:
        r = "E";
    b, a = math.modf(lon)
    c, b = math.modf(b*60)
    c = int(c*60)
    i["Xmp.exif.GPSLongitude"] = pyexiv2.utils.GPSCoordinate(a, b, c, r)
    
    i.write()


if __name__ == "__main__":
    write_gps("pictures/DSC_9766.NEF",
            47.999999, 8.111111, None, "WGS-84", 150.)
