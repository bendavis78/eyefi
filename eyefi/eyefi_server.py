#!/usr/bin/python

# EyeFi Python Server v3.0
#
# Copyright (C) 2009 Jeffrey Tchang
#               2010 Robert Jordens
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
import cgi
import hashlib
import binascii
import tarfile
import random
import cStringIO as StringIO
import array
import struct

from xml.etree import ElementTree as ET

import SOAPpy

from twisted.python import log
from twisted.web import soap
from twisted.internet import utils
from twisted.internet import reactor

from eyefilog import tag_photo



def checksum(data, key):
    data += "\0" * (-len(data) % 512)
    s = array.array("H")
    for i in range(0, len(data), 512):
        a = sum(struct.unpack("<256H", data[i:i + 512]))
        while a >> 16:
            a = (a >> 16) + (a & 0xffff)
        s.append(a ^ 0xffff)
    s.fromstring(binascii.unhexlify(key))
    m = hashlib.md5()
    m.update(s.tostring())
    return m.hexdigest()


class EyeFiServer(soap.SOAPPublisher):
    def __init__(self, key, output, macfolder=False, run=None,
            geotag=False):
        soap.SOAPPublisher.__init__(self)
        self.key = key
        self.output = output
        self.macfolder = macfolder
        self.run = run
        self.geotag = geotag
        self.snonces = {}

    def render(self, request):
        # the upload request is multipart/form-data with file and SOAP:
        # handle separately
        if request.postpath == ["upload"]:
            return self.render_upload(request)
        else:
            return soap.SOAPPublisher.render(self, request)

    def _gotResult(self, result, request, methodName):
        # hack twisted.web.soap here:
        # do not wrap result in a <Result> element
        response = SOAPpy.buildSOAP(kw={'%sResponse' % methodName: result},
                                  encoding=self.encoding)
        self._sendResponse(request, response)

    def soap_StartSession(self, transfermode, macaddress, cnonce,
            transfermodetimestamp):
        log.msg("StartSession", macaddress)
        m = hashlib.md5()
        m.update(binascii.unhexlify(macaddress + cnonce +
            self.key[macaddress])) # fails with keyerror if unknown mac
        credential = m.hexdigest()
        self.snonces[macaddress] = "%x" % random.getrandbits(128)
        return {"credential": credential,
                "snonce": self.snonces[macaddress],
                "transfermode": transfermode,
                "transfermodetimestamp": transfermodetimestamp,
                "upsyncallowed": "false"}
    soap_StartSession.useKeywords = True

    def soap_GetPhotoStatus(self, macaddress, credential, filesignature,
            flags, filesize, filename):
        log.msg("GetPhotoStatus", macaddress, filename)
        m = hashlib.md5()
        m.update(binascii.unhexlify(macaddress + self.key[macaddress] +
            self.snonces[macaddress]))
        want = m.hexdigest()
        assert credential == want, (credential, want)
        return {"fileid": 1, "offset": 0}
    soap_GetPhotoStatus.useKeywords = True
   
    def render_upload(self, request):
        typ, pdict = cgi.parse_header(
                request.requestHeaders.getRawHeaders("content-type")[0])
        form = cgi.parse_multipart(request.content, pdict)
        p, header, body, attrs = SOAPpy.parseSOAPRPC(
            form['SOAPENVELOPE'][0], 1, 1, 1)
        req_params = p._asdict()
        macaddress = req_params["macaddress"]
        got = checksum(form['FILENAME'][0], self.key[macaddress])
        want = form['INTEGRITYDIGEST'][0]
        if got == want:
            tar = StringIO.StringIO(form['FILENAME'][0])
            tarfi = tarfile.open(fileobj=tar)
            output = self.output
            if self.macfolder:
                output = os.path.join(output, macaddress)
                if not os.access(output, os.R_OK):
                    os.mkdir(output)
            tarfi.extractall(output)
            names = [os.path.join(output, name) for name
                    in tarfi.getnames()]
            reactor.callLater(0, self.handle_upload, names)
            success = "true"
            log.msg("successful upload", names)
        else:
            success = "false"
            log.msg("upload verification failed", got, want)
        resp = SOAPpy.buildSOAP(kw={"UploadPhotoResponse":
                    {"success": success}})
        return resp

    def handle_upload(self, names):
        if self.geotag:
            photo, d = tag_photo(*names)
            d.addBoth(log.msg)
        if self.run:
            for r in self.run:
                utils.getProcessOutput(r, names).addBoth(log.msg)

    def soap_MarkLastPhotoInRoll(self, macaddress, mergedelta):
        log.msg("MarkLastPhotoInRoll", macaddress, mergedelta)
        return {}
    soap_MarkLastPhotoInRoll.useKeywords = True

    # other soap methods (probably center2server) seen in logs
    # def soap_GetConnectedCards(self, **k): pass
    # def soap_GetSummary(self, **k): pass
    # def soap_GetScannedNetworks(self, **k): pass
    # def soap_TestNetwork(self, **k): pass
    # def soap_GetConfiguredNetworks(self, **k): pass
    # def soap_GetWirlessNetworkKey(self, **k): pass
    # def soap_PhotoSearch(self, **k): pass
    # def soap_GetFolderConfig(self, **k): pass
    # def soap_GetDesktopSync(self, **k): pass
    # def soap_GetEndlessMemoryConfig(self, **k): pass
    # def soap_GetUploadPolicy(self, **k): pass
    # def soap_GetRegistrationParam(self, **k): pass
    # def soap_UnmountCard(self, **k): pass
    # def soap_UpdateFirmware(self, **k): pass


def eyefi_site(*a, **k):
    from twisted.web import server, resource
    root = resource.Resource()
    api = resource.Resource()
    root.putChild("api", api)
    soap = resource.Resource()
    api.putChild("soap", soap)
    eyefilm = resource.Resource()
    soap.putChild("eyefilm", eyefilm)
    v1 = EyeFiServer(*a, **k)
    eyefilm.putChild("v1", v1)
    return server.Site(root)


def main():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("-p", "--port",
            help="listen port [%default]")
    parser.add_option("-k", "--key", action="append",
            help="mac:key per card [%default]")
    parser.add_option("-o", "--output",
            help="output directory [%default]")
    parser.add_option("-m", "--macfolder", action="store_true",
            help="use subfolders per card mac [%default]")
    parser.add_option("-g", "--geotag", action="store_true",
            help="geotag in xmp sidecar [%default]")
    parser.add_option("-r", "--run", action="append",
            help="execute command with files as arguments [%default]")
    parser.add_option("-v", "--verbose", action="store_true",
            help="be verbose, log to stdout [%default]")

    parser.set_defaults(
            key=["0018564167f0:31208d34561045b53e60a70f16c0eb9c"],
            port=59278, verbose=False, output="pictures", run=[],
            geotag=False, macfolder=False)
    opts, args = parser.parse_args()

    if opts.verbose:
        import sys
        log.startLogging(sys.stdout)
    
    site = eyefi_site(dict(v.split(":") for v in opts.key),
            opts.output, opts.macfolder, opts.run, opts.geotag)
    reactor.listenTCP(opts.port, site)
    reactor.run()

if __name__ == '__main__':
    main()
