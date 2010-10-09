#!/usr/bin/env python

from distutils.core import setup
import glob
import os
from DistUtilsExtra.command import *

setup(name='software-properties',
      version='0.60',
      packages=[
                'softwareproperties',
                'softwareproperties.gtk',
                'softwareproperties.kde',
                ],
      scripts=[
               'software-properties-gtk',
               'software-properties-kde',
               'add-apt-repository',
               ],
      data_files=[
                  ('share/software-properties/designer',
                   glob.glob("data/designer/*.ui")
                  ),
                  ('share/software-properties/gtkbuilder',
                   glob.glob("data/gtkbuilder/*.ui")
                  ),
                  ],
      cmdclass = { "build" : build_extra.build_extra,
                   "build_i18n" :  build_i18n.build_i18n,
#                   "build_help" :  build_help.build_help,
                   "build_icons" :  build_icons.build_icons }
     )
