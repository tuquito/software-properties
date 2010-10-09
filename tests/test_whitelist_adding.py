#!/usr/bin/python

import unittest
import sys
sys.path.insert(0, "../")

from softwareproperties.SoftwareProperties import SoftwareProperties

class TestWhitelist(unittest.TestCase):
    def testCheckAndAddKey(self):
        sp = SoftwareProperties()
        line = "deb http://xxx/cial jaunty main"
        self.assert_(sp._is_line_in_whitelisted_channel(line) is None)
        line = "deb http://archive.canonical.com/ubuntu jaunty partner"
        self.assert_(sp._is_line_in_whitelisted_channel(line) is not None)
        line = "deb http://archive.canonical.com/ubuntu jaunty partner"
        sp.check_and_add_key_for_whitelisted_channels(line)

if __name__ == "__main__":
    unittest.main()
