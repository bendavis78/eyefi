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

from twisted.python import log
from twisted.internet import utils
from twisted.internet.defer import DeferredList

from eyefi.maclog import tag_photo
from eyefi.twisted_flickrapi import TwistedFlickrAPI
import pyexiv2
assert pyexiv2.version_info[1] >= 2, "need at least pyexiv 0.2.2"



class Action(object):
    name = "action_name"

    def __init__(self, cfg, card):
        pass

    @classmethod
    def active_on_card(cls, card):
        return bool(card.get(cls.name, False))

    def handle_photo(self, card, files):
        pass

    def __call__(self, args):
        return self.handle_photo(*args)


_actions = []
def _register_action(action):
    _actions.append(action)
    return action


def build_actions(cfg, cards):
    actions = {}
    for macaddress, card in cards.items():
        h = []
        for action in _actions:
            if action.active_on_card(card):
                h.append(action(cfg, card))
        actions[macaddress] = h
    return actions


@_register_action
class ExtractPreview(Action):
    name = "extract_preview"

    def handle_photo(self, card, files):
        for file in files:
            base, ext = os.path.splitext(file)[1]
            if ext.lower() in (".nef",):
                i = pyexiv2.metadata.ImageMetadata(file)
                i.read()
                i.previews[-1].write_to_file(base)
                log.msg("wrote preview", base, i.previews[-1].extension)
        return card, files


@_register_action
class Geotag(Action):
    name = "geotag"

    def handle_photo(self, card, files):
        photo, d = tag_photo(*files)
        d.addCallback(log.msg)
        d.addCallback(lambda _: (card, files))
        return d


@_register_action
class Run(Action):
    name = "run"

    def handle_photo(self, card, files):
        d = utils.getProcessOutput(
            card["run"], names)
        d.addCallback(log.msg)
        d.addCallback(lambda _: (card, files))
        return d



@_register_action
class FlickrUpload(Action):
    name = "flickr_upload"

    def __init__(self, cfg, card):
        key, secret = cfg.get("__main__", "flickr_key").split(":")
        self.flickr = TwistedFlickrAPI(key, secret)
        self.flickr.authenticate_console("write"
            ).addCallback(log.msg, "<- got flickr token")
        
    def handle_photo(self, card, files):
        ds = []
        for file in files:
            if os.path.splitext(file)[1].lower() in (".jpg",):
                ds.append(self.flickr.upload(file, is_public="0"
                    ).addCallback(log.msg, "upload to flickr"))
        d = DeferredList(ds)
        d.addCallback(lambda _: (card, files))
        return d
