#  Qt 4 based frontend to software-properties
#
#  Copyright (c) 2007 Canonical Ltd.
#
#  Author: Jonathan Riddell <jriddell@ubuntu.com>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

from gettext import gettext as _

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic

from aptsources.sourceslist import SourceEntry

from I18nHelper import *

UIDIR = '/home/jr/src/software-properties/deneutral'

class DialogAdd(QDialog):

  def __init__(self, parent, sourceslist, datadir, distro):
    QDialog.__init__(self, parent)
    self.sourceslist = sourceslist
    self.distro = distro
    uic.loadUi("%s/designer/dialog_add.ui" % datadir, self)

    self.button_edit_ok = self.buttonBox.button(QDialogButtonBox.Ok)
    self.button_edit_ok.setEnabled(False)

    if self.distro:
        example = "%s %s %s %s" % (self.distro.binary_type,
                                   self.distro.source_template.base_uri,
                                   self.distro.codename,
                                   self.distro.source_template.components[0].name)
    else:
        example = "deb http://ftp.debian.org sarge main"
    # L10N: the example is of the format: deb http://ftp.debian.org sarge main
    head = utf8(_('<big><b>Enter the complete APT line of the repository that '
             'you want to add as source</b></big>'))
    msg =  utf8(_("The APT line includes the type, location and components of a "
            "repository, for example  '%s'.")) % ("<i>%s</i>" % example)
    self.label_example_line.setWordWrap(True)
    self.label_example_line.setText(head + '<p>' + msg)

    translate_widget(self)

    self.connect(self.entry, SIGNAL("textChanged(const QString&)"), self.check_line)

  def check_line(self, text):
    """Check for a valid apt line and set the enabled value of the
       button 'add' accordingly"""
    line = unicode(self.entry.text())
    if line.startswith("ppa:"):
      self.button_edit_ok.setEnabled(True)
      return
    source_entry = SourceEntry(line)
    if source_entry.invalid == True or source_entry.disabled == True:
      self.button_edit_ok.setEnabled(False)
    else:
      self.button_edit_ok.setEnabled(True)

  def run(self):
    result = self.exec_()
    if result == QDialog.Accepted:
        line = unicode(self.entry.text())
    else:
        line = None
    return line
