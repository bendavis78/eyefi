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


# FIXME: bad, bad, bad: we are overriding private methods here
# the actual changes are some 10 lines only, the rest is duplicated code
# The original code has the following license/copyright:
# 
# This code is subject to the Python licence, as can be read on
# http://www.python.org/download/releases/2.5.2/license/
#
# For those without an internet connection, here is a summary. When this
# summary clashes with the Python licence, the latter will be applied.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from twisted.web.client import getPage
from twisted.internet.defer import succeed

from flickrapi import FlickrAPI, rest_parsers, LOG

class TwistedFlickrAPI(FlickrAPI):
    def _FlickrAPI__flickr_call(self, **kwargs):
        LOG.debug("Calling %s" % kwargs)
        post_data = self.encode_and_sign(kwargs)
        if self.cache and self.cache.get(post_data):
            return defer.succeed(self.cache.get(post_data))
        url = "http://" + FlickrAPI.flickr_host + FlickrAPI.flickr_rest_form
        reply = getPage(url, method="POST", postdata=post_data, headers={
            "Content-Type": "application/x-www-form-urlencoded"})
        if self.cache is not None:
            reply.addCallback(self._add_to_cache, post_data)
        return reply

    def _add_to_cache(self, reply, post_data):
        self.cache.set(post_data, reply)
        return reply

    def _FlickrAPI__wrap_in_parser(self, wrapped_method,
            parse_format, *args, **kwargs):
        if parse_format in rest_parsers and 'format' in kwargs:
            kwargs['format'] = 'rest'
        LOG.debug('Wrapping call %s(self, %s, %s)' % (wrapped_method, args,
            kwargs))
        data = wrapped_method(*args, **kwargs)
        if parse_format not in rest_parsers:
            return data
        parser = rest_parsers[parse_format]
        return data.addCallback(lambda resp: parser(self, resp))

    def _FlickrAPI__send_multipart(self, url, body, progress_callback=None):
        assert not progress_callback, \
            "twisted upload/replace does not support progress callbacks yet"
        LOG.debug("Uploading to %s" % url)
        reply = getPage(url, method="POST", postdata=str(body),
                headers=dict([body.header()]))
        return reply


def main():
    from twisted.internet import reactor
    from twisted.python import log
    import sys
    log.startLogging(sys.stdout)

    api_key = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    api_secret = "XXXXXXXXXXXX"
    
    flickr = TwistedFlickrAPI(api_key, api_secret)
    # flickr.upload("pic", is_public="0"
    #       ).addBoth(log.msg)
    flickr.photos_search(user_id='73509078@N00', per_page='10'
            ).addBoth(log.msg
            ).addBoth(lambda e: reactor.callLater(0, reactor.stop))
    reactor.run()


if __name__ == '__main__':
    main()
