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

from flickrapi import FlickrAPI, rest_parsers, LOG, FlickrError


# FIXME: bad, bad, bad: we are overriding private methods here
# FIXME: the actual changes are some 20 lines only, the rest is
# duplicated code

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
        # would be like
        # http://twistedmatrix.com/pipermail/twisted-web/2007-January/003253.html
        LOG.debug("Uploading to %s" % url)
        reply = getPage(url, method="POST", postdata=str(body),
                headers=dict([body.header()]))
        return reply

    def trait_names(self):
        """
        ipython introspection needs to be synchornous, disable it
        """
        return None

    def get_token_part_one(self, perms="read"):
        token = succeed(self.token_cache.token)
        @token.addCallback
        def check(token):
            if not token:
                return None # need new one
            LOG.debug("Trying cached token '%s'" % token)
            rsp = self.auth_checkToken(auth_token=token, format='xmlnode')
            @rsp.addCallback
            def check_get(rsp):
                tokenPerms = rsp.auth[0].perms[0].text
                if tokenPerms == "read" and perms != "read":
                    return None # need new
                elif tokenPerms == "write" and perms == "delete":
                    return None # need new
                return token # is good
            @rsp.addErrback
            def check_err(err):
                err.trap(FlickrError)
                LOG.debug("Cached token invalid")
                self.token_cache.forget()
                return None # need new
            return rsp # automatic deferred chaining
        @token.addCallback
        def need_new(token):
            if token:
                return token, None # good token, no new frob
            LOG.debug("Getting frob for new token")
            rsp = self.auth_getFrob(auth_token=None, format='xmlnode')
            @rsp.addCallback
            def valid_frob(rsp):
                frob = rsp.frob[0].text
                self.validate_frob(frob, perms)
                return token, frob
            return rsp # automatic deferred chaining
        return token

    def get_token(self, frob):
        rsp = self.auth_getToken(frob=frob, auth_token=None, format='xmlnode')
        @rsp.addCallback
        def extract_token(rsp):
            token = rsp.auth[0].token[0].text
            LOG.debug("get_token: new token '%s'" % token)
            # store the auth info for next time
            self.token_cache.token = token
            return token
        return rsp

    def authenticate_console(self, perms='read'):
        d = self.get_token_part_one(perms)
        @d.addCallback
        def wait(arg):
            token, frob = arg
            if not token:
                # raw_inputs message gets swallowed by log
                print "Press ENTER after you authorized this program" 
                raw_input()
            return token, frob
        d.addCallback(self.get_token_part_two)
        return d


def main():
    from twisted.internet import reactor
    from twisted.python import log
    import logging
    log.PythonLoggingObserver().start()
    logging.getLogger().setLevel(level=logging.DEBUG)
    LOG.setLevel(level=logging.DEBUG)

    api_key = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    api_secret = "XXXXXXXXXXXX"

    flickr = TwistedFlickrAPI(api_key, api_secret)

    #flickr.authenticate_console("write"
    #    ).addCallback(log.msg, "<- got token"
    #    ).addBoth(lambda _: reactor.callLater(0, reactor.stop)
    #    )

    #flickr.upload("test.jpg", is_public="0"
    #    ).addBoth(log.msg
    #    ).addBoth(lambda _: reactor.callLater(0, reactor.stop)
    #    )

    flickr.photos_search(user_id='73509078@N00', per_page='10'
        ).addBoth(log.msg
        ).addBoth(lambda _: reactor.callLater(0, reactor.stop)
        )
    
    reactor.run()


if __name__ == '__main__':
    main()
