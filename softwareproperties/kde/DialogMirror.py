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

import apt
import apt_pkg
import tempfile
from gettext import gettext as _
import os
import re
import threading

from softwareproperties.MirrorTest import MirrorTest
from I18nHelper import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic

from softwareproperties.CountryInformation import CountryInformation

class DialogMirror(QDialog):

  def __init__(self, parent, datadir, distro, custom_mirrors):
    """
    Initialize the dialog that allows to choose a custom or official mirror
    """
    QDialog.__init__(self, parent)
    uic.loadUi("%s/designer/dialog_mirror.ui" % datadir, self)
    self.parent = parent

    self.custom_mirrors = custom_mirrors

    self.country_info = CountryInformation()

    self.button_choose = self.buttonBox.button(QDialogButtonBox.Ok)
    self.button_choose.setEnabled(False)
    self.button_cancel = self.buttonBox.button(QDialogButtonBox.Cancel)
    self.distro = distro

    self.treeview.setColumnCount(1)
    self.treeview.setHeaderLabels([utf8(_("Mirror"))])

    translate_widget(self)
    # used to find the corresponding iter of a location
    map_loc = {}
    patriot = None
    """ no custom yet
    # at first add all custom mirrors and a separator
    if len(self.custom_mirrors) > 0:
        for mirror in self.custom_mirrors:

            model.append(None, [mirror, False, True, None])
            self.column_mirror.add_attribute(self.renderer_mirror, 
                                             "editable", 
                                             COLUMN_CUSTOM)
        model.append(None, [None, True, False, None])
    """
    self.mirror_map = {}
    # secondly add all official mirrors
    for hostname in self.distro.source_template.mirror_set.keys():
        mirror = self.distro.source_template.mirror_set[hostname]
        if map_loc.has_key(mirror.location):  # a mirror in a country
            QTreeWidgetItem(map_loc[mirror.location], [hostname])
            self.mirror_map[hostname] = mirror
        elif mirror.location != None:  # a country new to the list
            country = utf8(self.country_info.get_country_name(mirror.location))
            parent = QTreeWidgetItem([country])
            self.mirror_map[country] = None
            self.treeview.addTopLevelItem(parent)
            QTreeWidgetItem(parent, [hostname])
            self.mirror_map[hostname] = mirror
            if mirror.location == self.country_info.code and patriot == None:
                patriot = parent
            map_loc[mirror.location] = parent
        else:  # a mirror without country
            item = QTreeWidgetItem([hostname])
            self.treeview.addTopLevelItem(item)
    self.treeview.sortItems(0, Qt.AscendingOrder)
    # Scroll to the local mirror set
    if patriot != None:
        self.select_mirror(patriot.text(0))
    self.connect(self.treeview, SIGNAL("itemClicked(QTreeWidgetItem*, int)"), self.on_treeview_mirrors_cursor_changed)
    self.connect(self.button_find_server, SIGNAL("clicked()"), self.on_button_test_clicked)
    self.edit_buttons_frame.hide()  ##FIXME not yet implemented

  def on_treeview_mirrors_cursor_changed(self, item, column):
    """ Check if the currently selected row in the mirror list
        contains a mirror and or is editable """
    # Update the list of available protocolls
    hostname = unicode(self.treeview.currentItem().text(0))
    mirror = self.mirror_map[hostname]
    self.combobox.clear()
    if mirror != None:
        self.combobox.setEnabled(True)
        seen_protos = []
        self.protocol_paths = {}
        for repo in mirror.repositories:
            # Only add a repository for a protocoll once
            if repo.proto in seen_protos:
                continue
            seen_protos.append(repo.proto)
            self.protocol_paths[repo.get_info()[0]] = repo.get_info()[1]
            self.combobox.addItem(repo.get_info()[0])
        self.button_choose.setEnabled(True)
    else:
        self.button_choose.setEnabled(False)
    """
        # Allow to edit and remove custom mirrors
        self.button_remove.set_sensitive(model.get_value(iter, COLUMN_CUSTOM))
        self.button_edit.set_sensitive(model.get_value(iter, COLUMN_CUSTOM))
        self.button_choose.set_sensitive(self.is_valid_mirror(model.get_value(iter, COLUMN_URI)))
        self.combobox.set_sensitive(False)

    """

  def run(self):
    """ Run the chooser dialog and return the chosen mirror or None """
    res = self.exec_()

    # FIXME: we should also return the list of custom servers
    if res == QDialog.Accepted:
        hostname = unicode(self.treeview.currentItem().text(0))
        mirror = self.mirror_map[hostname]

        if mirror == None:
            # Return the URL of the selected custom mirror
            print "Error, unknown mirror"
            return None
            ##FIXME return model.get_value(iter, COLUMN_URI)
        else:
            # Return a URL created from the hostname and the selected
            # repository
            proto = unicode(self.combobox.currentText())

            directory = self.protocol_paths[proto]
            return "%s://%s/%s" % (proto, mirror.hostname, directory)
    else:
        return None

  def on_button_test_clicked(self):
    ''' Perform a test to find the best mirror and select it 
        afterwards in the treeview '''
    class MirrorTestKDE(MirrorTest):
        def __init__(self, mirrors, test_file, running, dialog, parent):
            MirrorTest.__init__(self, mirrors, test_file, running)
            self.dialog = dialog
            self.parent = parent

        def report_action(self, text):
            if self.running.isSet():
                self.parent.emit(SIGNAL("report_action(QString*)"), text)

        def report_progress(self, current, max, borders=(0,1), mod=(0,0)):
            if self.running.isSet():
                self.parent.emit(SIGNAL("report_progress(int, int, PyQt_PyObject, PyQt_PyObject)"),
                                   current, max, borders, mod)

        def run(self):
            self.parent.emit(SIGNAL("test_start()"))
            rocker = self.run_full_test()
            self.parent.emit(SIGNAL("test_end(QString*)"), rocker)

    self.dialog = QProgressDialog(utf8(_("Testing Mirrors")), utf8(_("Cancel")), 0, 100, self)
    self.dialog.setWindowTitle(utf8(_("Testing Mirrors")))
    self.dialog.setWindowModality(Qt.WindowModal)
    self.button_cancel_test = QPushButton(utf8(_("Cancel")), self.dialog)
    self.dialog.setCancelButton(self.button_cancel_test)
    self.connect(self.button_cancel_test, SIGNAL("clicked()"), self.on_button_cancel_test_clicked);
    # the following signals are connected across threads
    self.connect(self, SIGNAL("test_start()"), self.on_test_start, Qt.BlockingQueuedConnection)
    self.connect(self, SIGNAL("test_end(QString*)"), self.on_test_end, Qt.BlockingQueuedConnection)
    self.connect(self, SIGNAL("report_progress(int, int, PyQt_PyObject, PyQt_PyObject)"), self.on_report_progress, Qt.BlockingQueuedConnection)
    self.connect(self, SIGNAL("report_action(QString*)"), self.on_report_action, Qt.BlockingQueuedConnection)

    self.running = threading.Event()
    self.running.set()
    pipe = os.popen("dpkg --print-architecture")
    arch = pipe.read().strip()
    test_file = "dists/%s/%s/binary-%s/Packages.gz" % \
                 (self.distro.source_template.name,
                  self.distro.source_template.components[0].name,
                  arch)
    test = MirrorTestKDE(self.distro.source_template.mirror_set.values(),
                         test_file, self.running, self.dialog, self)
    test.start() # test starts in a separate thread

  def on_test_start(self):
      self.dialog.show()

  def on_test_end(self, mirror):
      self.dialog.hide()
      if not self.running.isSet():
          return # canceled by user
      if mirror != None:
          self.select_mirror(mirror)
      else:
          QMessageBox.warning(self.dialog, utf8(_("Testing Mirrors")),
                                  utf8(_("No suitable download server was found")) + "\n" +
                                  utf8(_("Please check your Internet connection.")))

  def on_report_action(self, text):
      self.dialog.setLabelText(str("<i>%s</i>" % text))

  def on_report_progress(self, current, max, borders=(0,1), mod=(0,0)):
      #self.dialog.setLabelText(utf8(_("Completed %s of %s tests")) % \
      #                       (current + mod[0], max + mod[1]))
      frac = borders[0] + (borders[1] - borders[0]) / max * current
      self.dialog.setValue(frac*100)

  def on_button_cancel_test_clicked(self):
    ''' Abort the mirror performance test '''
    self.running.clear()
    self.dialog.show()
    self.dialog.setLabelText("<i>%s</i>" % utf8(_("Canceling...")))
    self.button_cancel_test.setEnabled(False)
    self.dialog.setValue(100)

  def select_mirror(self, mirror):
    """Select and expand the path to a matching mirror in the list"""
    found = self.treeview.findItems(QString(mirror), Qt.MatchExactly|Qt.MatchRecursive)
    if found:
      found[0].setSelected(True)
      self.treeview.setCurrentItem(found[0])
      self.treeview.scrollToItem(found[0], QAbstractItemView.PositionAtCenter)
      self.on_treeview_mirrors_cursor_changed(found[0], 0)
      self.button_choose.setFocus()
      return True
