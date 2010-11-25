#!/usr/bin/twistd -ny

from twisted.application import service, internet
from eyefi.eyefi_server import eyefi_site

application = service.Application("EyeFi Server")
site = eyefi_site(
    key={"0018564167f0": "31208d34561045b53e60a70f16c0eb9c"},
    output="pictures", macfolder=False, run=None, geotag=True)
service = internet.TCPServer(59278, site)
service.setServiceParent(application)
