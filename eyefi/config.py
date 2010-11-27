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

from configglue.pyschema import schemaconfigglue, ini2schema
from pkg_resources import Requirement, resource_filename

base = resource_filename(Requirement.parse("eyefi"), "conf/base.conf")

def glue_config(
        confs=("/etc/eyefi.conf", "~/.eyefi.conf", "eyefi.conf"),
        base=base):
    config_parser = ini2schema(open(base))
    # op, opts, args = schemaconfigglue(config_parser)
    config_parser.read(confs)
    cards = {}
    for sec in config_parser.sections():
        if sec == "__main__":
            continue
        d = {"name": sec}
        d.update(config_parser.values("card"))
        for k, v in config_parser.items(sec):
            d[k] = config_parser.parse("card", k, v)
        if not d["active"]:
            continue
        cards[d["macaddress"]] = d
        # del d["active"], d["macaddress"]
    return config_parser, cards

if __name__ == "__main__":
    print glue_config("eyefi.conf")
