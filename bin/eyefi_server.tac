#!/usr/bin/twistd -ny

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

from twisted.application import internet, service

from eyefi.config import glue_config
from eyefi.server import eyefi_site

application = service.Application("eyefi")
cfg, cards = glue_config()
site = eyefi_site(cards)
server = internet.TCPServer(cfg.get("__main__", "port"), site)
server.setServiceParent(application)

# vim: ai sts=4 sw=4 expandtab syntax=python
