"""
This module contains various context menus used in the main GUI.
Copyright 2021 Bill Dengler and open-source contributors
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

import gettext
import wx

_ = gettext.translation("treemendous", fallback=True).gettext


class AddNodeMenu(wx.Menu):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        child = wx.MenuItem(
            self,
            wx.ID_ANY,
            # Translators: The option for adding a child in the add node pop-up menu.
            _("&Child"),
            # Translators: Help text in the add node pop-up menu.
            _("Add a new node as an immediate child of the current selection"),
        )
        self.Append(child)
        self.Bind(wx.EVT_MENU, self.OnChild, child)

        parent = wx.MenuItem(
            self,
            wx.ID_ANY,
            # Translators: The option for adding a parent in the add node pop-up menu.
            _("&Parent"),
            # Translators: Help text in the add node pop-up menu.
            _("Add a new node that contains the currently selected subtree"),
        )
        self.Append(parent)
        self.Bind(wx.EVT_MENU, self.OnParent, parent)

        if self.parent.tree.selection != self.parent.tree.root:
            sibling = wx.MenuItem(
                self,
                wx.ID_ANY,
                # Translators: The option for adding a sibling in the add node pop-up menu.
                _("&Sibling"),
                _(
                    # Translators: Help text in the add node pop-up menu.
                    "Add a new node as an immediate sibling (same level) of the current selection"
                ),
            )
            self.Append(sibling)
            self.Bind(wx.EVT_MENU, self.OnSibling, sibling)

    def OnChild(self, event):
        return self.parent.DoAddChild()

    def OnParent(self, event):
        return self.parent.DoAddParent()

    def OnSibling(self, event):
        return self.parent.DoAddSibling()


class PasteDestMenu(wx.Menu):
    def __init__(self, parent, event):
        super().__init__()
        self.parent = parent
        self.event = event

        child = wx.MenuItem(
            self,
            wx.ID_ANY,
            # Translators: An option in the paste pop-up menu.
            _("As &child"),
            # Translators: Help text in the paste pop-up menu.
            _("Paste as an immediate child of the current selection"),
        )
        self.Append(child)
        self.Bind(wx.EVT_MENU, self.OnChild, child)

        parent = wx.MenuItem(
            self,
            wx.ID_ANY,
            # Translators: An option in the paste pop-up menu.
            _("As &parent"),
            # Translators: Help text in the paste pop-up menu.
            _("Merge the pasteboard with the current selection."),
        )
        self.Append(parent)
        self.Bind(wx.EVT_MENU, self.OnParent, parent)

        if self.parent.tree.selection != self.parent.tree.root:
            sibling = wx.MenuItem(
                self,
                wx.ID_ANY,
                # Translators: An option in the paste pop-up menu.
                _("As &sibling"),
                _(
                    # Translators: Help text in the paste pop-up menu.
                    "Paste as an immediate sibling (same level) of the current selection"
                ),
            )
            self.Append(sibling)
            self.Bind(wx.EVT_MENU, self.OnSibling, sibling)

    def OnChild(self, event):
        return self.parent.PasteChild(self.event)

    def OnParent(self, event):
        return self.parent.PasteParent(self.event)

    def OnSibling(self, event):
        return self.parent.PasteSibling(self.event)


class NodeContextMenu(wx.Menu):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        addSubmenu = AddNodeMenu(parent)
        self.AppendSubMenu(
            addSubmenu,
            # Translators: An item in the node context (shift+f10) menu.
            _("&Add node"),
            help=_(
                # Translators: Help text in the node context (shift+F10) menu.
                "Add a new node relative to the current selection."
            ),
        )

        edit = wx.MenuItem(
            self,
            wx.ID_EDIT,
            # Translators: An item in the node context (shift+f10) menu.
            _("Edit node...\tF2"),
            # Translators: Help text in the node context (shift+F10) menu.
            _("Edit the currently selected node."),
        )
        self.Append(edit)

        up = wx.MenuItem(
            self,
            wx.ID_ANY,
            # Translators: An item in the node context (shift+f10) menu.
            _("Move up\tAlt+up"),
            # Translators: Help text in the node context (shift+F10) menu.
            _("Move subtree to previous position in parent."),
        )
        self.Append(up)
        self.Bind(wx.EVT_MENU, self.OnUp, up)

        dn = wx.MenuItem(
            self,
            wx.ID_ANY,
            # Translators: An item in the node context (shift+f10) menu.
            _("Move down\tAlt+down"),
            # Translators: Help text in the node context (shift+F10) menu.
            _("Move subtree to next position in parent."),
        )
        self.Append(dn)
        self.Bind(wx.EVT_MENU, self.OnDn, dn)

        delsubtree = wx.MenuItem(
            self,
            wx.ID_DELETE,
            # Translators: An item in the node context (shift+f10) menu.
            _("&Delete subtree\tDEL"),
            # Translators: Help text in the node context (shift+F10) menu.
            _("Delete this node and all of its descendants."),
        )
        self.Append(delsubtree)

    def OnUp(self, event):
        return self.parent.OnMoveUp(event)

    def OnDn(self, event):
        return self.parent.OnMoveDown(event)
