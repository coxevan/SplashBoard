r"""
SplashBoard Version 0.2

Created by Evan Cox - http://www.evancox.net/ - coxevan90@gmail.com - @evanpcox

**** CURRENTLY DOES NOT WORK WITHOUT PIL/PILLOW ****

* Please do not claim as your own / use for commercial use without first at least telling me. I'm a nice guy, I'll let
you, I just want to keep track of what the script is being used for.


HELP INFORMATION -
SplashBoard is made to help in the creation of inspiration boards and reference boards for projects.
Using Google Image Search and Python with PyMEL, the script allows the user to search the web from within Maya and
manipulate images in the following ways:
    - Apply to object as texture
    - Create Reference Image Planes
    - Create Reference Polygon Planes

**Now includes the ability to insert custom images from the harddrive into the interface and manipulate them in the same
ways!

This is an early version, so if there are any ideas for future features, I'd love to hear them and would be more than
happy to have partners for this project. Contact me for more information or with ideas.


PLANNED FEATURES -
* Integration with Pinterest
    Flag images/add them to a new Pinterest board on the users account.
"""

__author__ = 'evancox | @evanpcox | coxevan90@gmail.com'
HELP_URL = 'http://www.evancox.net/'
BUG_REPORT = 'http://www.evancox.net/'

import maya.cmds as mc
import pymel.core as py
import definitions
import gui

import urllib2
import urllib
import simplejson
import socket
import os

reload(gui)
reload(definitions)
splash_instance = gui.SplashBoard()
splash_instance.gui()