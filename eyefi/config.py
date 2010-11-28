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

from configglue.pyschema import schemaconfigglue, ini2schema
from twisted.python import usage
from pkg_resources import Requirement, resource_filename

base = resource_filename(Requirement.parse("eyefi"), "conf/base.conf")

confs = ("/etc/eyefi.conf",
         os.path.expanduser("~/.eyefi.conf"),
         "eyefi.conf")

def glue_config(confs=confs, base=base):
    config_parser = ini2schema(open(base))
    # op, opts, args = schemaconfigglue(config_parser)
    config_parser.read(confs)
    return config_parser

def get_cards(config_parser):
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
    return cards


def twisted_schemaconfigglue(parser, argv=None):
    """Populate an usage.Options subclass with options and defaults
    taken from a fully loaded SchemaConfigParser. After the Options
    instance has parse the options, the SchemaConfigParser is updated.
    """

    def long_name(option):
        if option.section.name == '__main__':
            return option.name
        return option.section.name + '_' + option.name

    def opt_name(option):
        return long_name(option).replace('-', '_')

    schema = parser.schema

    params = []
    for section in schema.sections():
        for option in section.options():
            # TODO: option.action
            params.append([long_name(option), None, 
                parser.get(section.name, option.name), option.help])

    class Options(usage.Options):
        optParameters = params
        def postOptions(self):
            for section in schema.sections():
                for option in section.options():
                    value = self[opt_name(option)]
                    if parser.get(section.name, option.name) != value:
                        # the value has been overridden by an argument;
                        # update it.
                        parser.set(section.name, option.name, value)
    return Options
