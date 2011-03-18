#!/usr/bin/env python
# -*- coding: utf-8 -*-
# generated by wxGlade 0.6 on Sun May 25 23:31:23 2008

# Copyright 2008 Martin Manns
# Distributed under the terms of the GNU General Public License
# generated by wxGlade 0.6 on Mon Mar 17 23:22:49 2008

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""
_menubars
===========

Provides menubars

Provides:
---------
  1. ContextMenu: Context menu for main grid
  2. MainMenu: Main menu of pyspread

"""

import wx

from _events import *

class _filledMenu(wx.Menu):
    """Menu that fills from the attribute menudata.

    Parameters:
    parent: object
    \tThe parent object that hosts the event handler methods
    menubar: wx.Menubar, defaults to parent
    \tThe menubar to which the menu is attached

    menudata has the following structure:
    [
        [wx.Menu, "Menuname", [\
            [wx.MenuItem, ["Methodname", "Itemlabel", "Help"]] , \
            ...
            "Separator" , \
            ...
            [wx.Menu, ...], \
            ...
        ] , \
    ...
    ]
    """

    menudata = []

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent')
        try:
            self.menubar = kwargs.pop('menubar')
        except KeyError:
            self.menubar = self.parent
        wx.Menu.__init__(self, *args, **kwargs)
        
        # id - message type storage
        self.ids_msgs = {}
        
        # Stores approve_item for disabling
        self.approve_item = None
        
        self._add_submenu(self, self.menudata)

    def _add_submenu(self, parent, data):
        """Adds items in data as a submenu to parent"""
        
        for item in data:
            obj = item[0]
            if obj == wx.Menu:
                try:
                    _, menuname, submenu, menu_id = item
                except ValueError:
                    _, menuname, submenu = item
                    menu_id = -1
                
                menu = obj()
                self._add_submenu(menu, submenu)
                
                if parent == self:
                    self.menubar.Append(menu, menuname)
                else:
                    parent.AppendMenu(menu_id, menuname, menu)
                    
            elif obj == wx.MenuItem:
                try:
                    msgtype, shortcut, helptext, item_id = item[1]
                except ValueError:
                    msgtype, shortcut, helptext = item[1]
                    item_id = wx.NewId()
                    
                try:
                    style = item[2]
                except IndexError:
                    style = wx.ITEM_NORMAL
                
                menuitem = obj(parent, item_id, shortcut, helptext, style)
                parent.AppendItem(menuitem)
                
                if "&Approve file" == shortcut:
                    self.approve_item = menuitem
                
                self.ids_msgs[item_id] = msgtype
                
                self.parent.Bind(wx.EVT_MENU, self.OnMenu, id=item_id)
                
            elif obj == "Separator":
                parent.AppendSeparator()
                
            else:
                raise TypeError, "Menu item unknown"

    def OnMenu(self, event):
        """Menu event handler"""
        
        msgtype = self.ids_msgs[event.GetId()]
        post_command_event(self.parent._grid, msgtype)

# end of class _filledMenu


class ContextMenu(_filledMenu):
    """Context menu for grid operations"""

    item = wx.MenuItem
    menudata = [ \
    [item, [CutMsg, "Cu&t\tCtrl+x", "Cut cell to clipboard"]], \
    [item, [CopyMsg, "&Copy\tCtrl+c", "Copy input strings to clipboard"]], \
    [item, [PasteMsg, "&Paste\tCtrl+v", "Paste cell from clipboard"]], \
    [item, [InsertRowsMsg, "Insert &rows\tShift+Ctrl+i", 
        "Insert rows at cursor"]], \
    [item, [InsertColsMsg, "&Insert columns\tCtrl+i", 
        "Insert columns at cursor"]], \
    [item, [DeleteRowsMsg, "Delete rows\tShift+Ctrl+d", "Delete rows" ]], \
    [item, [DeleteColsMsg, "Delete columns\tCtrl+Alt+d", "Delete columns"]]]


# end of class ContextMenu


class MainMenu(_filledMenu):
    """Main application menu"""
    item = wx.MenuItem
    menudata = [ \
        [wx.Menu, "&File", [\
            [item, [NewMsg, "&New\tCtrl+n", 
                "Create a new, empty spreadsheet", wx.ID_NEW]], \
            [item, [OpenMsg, "&Open", 
                "Open spreadsheet from file", wx.ID_OPEN]], \
            [item, [SaveMsg, "&Save\tCtrl+s", 
                    "Save spreadsheet", wx.ID_SAVE]], \
            [item, [SaveAsMsg, "Save &As\tShift+Ctrl+s", 
                "Save spreadsheet to a new file"], wx.ID_SAVEAS], \
            ["Separator"], \
            [item, [ImportMsg, "&Import", "Import a file " + \
                "(Supported formats: CSV, Tab separated text)"]], \
            [item, [ExportMsg, "&Export", 
                "Export a file (Supported formats: CSV)"]], \
            ["Separator"], \
            [item, [ApproveMsg, "&Approve file", 
                "Approve, unfreeze and sign the current file"]], \
            ["Separator"], \
            [item, [PrintMsg, "&Print...\tCtrl+p", 
                "Print current spreadsheet", wx.ID_PRINT]], \
            ["Separator"], \
            [item, [CloseMsg, "E&xit\tCtrl+q", "Exit Program", wx.ID_EXIT]]] \
        ], \
        [wx.Menu, "&Edit", [\
            [item, [UndoMsg, "&Undo\tCtrl+z", "Undo last step", wx.ID_UNDO]], \
            [item, [RedoMsg, "&Redo\tShift+Ctrl+z", 
                "Redo last undone step", wx.ID_REDO]], \
            ["Separator"], \
            [item, [CutMsg, "Cu&t\tCtrl+x", "Cut cell to clipboard"]], \
            [item, [CopyMsg, "&Copy\tCtrl+c", 
                "Copy the input strings of the cells to clipboard"]], \
            [item, [CopyResultMsg, "Copy &Results\tShift+Ctrl+c", 
                "Copy the result strings of the cells to the clipboard"]], \
            [item, [PasteMsg, "&Paste\tCtrl+v", 
                "Paste cells from clipboard", wx.ID_PASTE]], \
            ["Separator"], \
            [item, [FindMsg, "&Find\tCtrl+f", "Find cell by content"]], \
            [item, [ReplaceMsg, "Replace\tCtrl+Shift+f", 
                "Replace strings in cells"]], \
            ["Separator"], \
            [item, [InsertRowsMsg, "Insert &rows", 
                "Insert rows at cursor"]], \
            [item, [InsertColsMsg, "&Insert columns", 
                "Insert columns at cursor"]], \
            [item, [InsertTabsMsg, "Insert &table", 
                "Insert table before current table"]], \
            ["Separator"], \
            [item, [DeleteRowsMsg, "Delete rows", 
                "Delete rows"]], \
            [item, [DeleteColsMsg, "Delete columns", 
                "Delete columns"]], \
            [item, [DeleteTabsMsg, "Delete table", 
                "Delete current table"]], \
            ["Separator"], \
            [item, [ResizeGridMsg, "Resize grid", "Resize the grid. " + \
                    "The buttom right lowermost cells are deleted first."]]] \
        ], \
        [wx.Menu, "&View", [ \
            [item, [RefreshSelectionMsg, "Refresh selected cells\tF5", 
                        "Refresh selected cells even when frozen"]],
            [item, [GotoCellMsg, "Go to cell ...", 
                        "Moves the grid to a cell."]],
            [wx.Menu, "Zoom", [ \
                [item, [ZoomMsg, str(int(zoom)) + "%", 
                        "Zoom " + str(int(zoom)) + "%"] \
                ] for zoom in xrange(50, 350, 10)]
                ] \
            ], \
        ], \
        [wx.Menu, "&Macro", [\
            [item, [MacroListMsg, "&Macro list\tCtrl+m", 
                        "Choose, fill in, manage, and create macros"]], \
            [item, [MacroLoadMsg, "&Load macro list", 
                        "Load macro list"]], \
            [item, [MacroSaveMsg, "&Save macro list", 
                        "Save macro list"]]]], \
        [wx.Menu, "&Help", [\
            [item, [ManualMsg, "&Manual", "Launch manual"]],
            [item, [TutorialMsg, "&Tutorial", "Launch tutorial"]],
            [item, [FaqMsg, "&FAQ", "Launch frequently asked questions"]],
            ["Separator"], \
            [item, [AboutMsg, "&About", "About this program", wx.ID_ABOUT]],
            ] \
        ] \
    ]

    def enable_file_approve(self, enable=True):
        """Enables or disables menu item (for entering/leaving save mode)"""
        
        self.approve_item.Enable(enable)
        
# end of class MainMenu
