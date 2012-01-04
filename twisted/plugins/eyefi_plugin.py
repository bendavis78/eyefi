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


from zope.interface import implements

from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet

from eyefi.config import glue_config, get_cards, twisted_schemaconfigglue
from eyefi.server import build_site
from eyefi.actions import build_actions


cfg = glue_config()
Options = twisted_schemaconfigglue(cfg)


class EyefiServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "eyefi"
    description = "EyeFi SDHC+WiFi card server"
    options = Options

    def makeService(self, options):
        # options have been postprocessed into cfg...
        cards = get_cards(cfg)
        actions = build_actions(cfg, cards)
        site = build_site(cfg, cards, actions)
        server = internet.TCPServer(cfg.get("__main__", "port"), site)
        return server

serviceMaker = EyefiServiceMaker()
