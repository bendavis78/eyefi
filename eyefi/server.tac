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

from twisted.application import service, internet
from eyefi.server import eyefi_site

application = service.Application("EyeFi Server")
site = eyefi_site(
    key={"0018564167f0": "31208d34561045b53e60a70f16c0eb9c"},
    output="pictures", macfolder=False, run=None, geotag=True)
service = internet.TCPServer(59278, site)
service.setServiceParent(application)

# vim: ai sts=4 sw=4 expandtab syntax=python
