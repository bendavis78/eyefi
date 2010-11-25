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

from setuptools import setup, find_packages

setup(
    name = "eyefi",
    version = "0.1",
    packages = find_packages(),
    install_requires = [
        "docutils>=0.3",
        "Twisted-Web", "Twisted-Core",
        "SOAPpy",
        "pyexiv2>=0.2",
        "simplejson",
        # "Sphinx",
        "configobj",
    ],
    dependency_links = [
        "http://tilloy.net/dev/pyexiv2/download.html",
    ],
    package_data = {
        'eyefi': ['*.tac'],
    },
    entry_points = {
        'console_scripts': [
            'eyefi_server = eyefi.server:main',
            'google_loc = eyefi.google_loc:main',
            'eyefi_geotag = eyefi.maclog:main',
        ],
    },
    author = "Robert Jordens",
    author_email = "jordens@phys.ethz.ch",
    description = "Eye-Fi SDHC+WiFi card tools",
    long_description = """
        The EyeFi cards include both some 2-8GB of SDHC storage and an
        embedded microprocessor with WiFi (802.11bgn) that can upload
        images as soon as they have been captured. While the software
        bundled with the cards is closed and Win/OSX only, the protocol
        is decently clean SOAP (like XML RPC via HTTP) and can be
        implemented with twisted and soappy.
        
        After associating with one of the configured wireless networks,
        the card authenticates a session with the server. The shared
        secret needs to be obtained from the settings of the Win/OSX
        application. The server can cope with multiple cards that are
        identified by their MAC address. After authentication, the card
        pushes the images that have not yet been posted to the server.
        The server unpacks the tarred bundle (optionally in a directory
        per MAC address). It then resolves the wireless networks that were
        logged by the card at the time the picture was taken into a
        geolocation using the Google API. The geolocation data is stored
        in an XMP sidecar. Finally, you can trigger your own scripts
        on complete upload, extraction and tagging.
    """,
    license = "GPL",
    keywords = "eyefi twisted wifi photo cameras",
    url = "http://launchpad.net/eyefi",
)
