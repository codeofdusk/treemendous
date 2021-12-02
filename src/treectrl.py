"""
Tree control class, containing an abstract interface to Windows, MacOS, and GTK native tree widgets.
Copyright 2021 Bill Dengler and open-source contributors
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

import wx
import wx.dataview

from abc import ABC, abstractmethod
from enum import auto, Enum


class TreeEvent(Enum):
    ITEM_SELECTED = auto()
    ITEM_EXPANDED = auto()
    ITEM_COLLAPSED = auto()
    CONTEXT_MENU = auto()
    KEY_DOWN = auto()


class TreeCTRL(ABC):
    "Base tree control interface."

    @property
    @abstractmethod
    def widget(self):
        raise NotImplementedError

    @abstractmethod
    def AddRoot(self, node, expanded):
        raise NotImplementedError

    @abstractmethod
    def AddChild(self, node, expanded):
        raise NotImplementedError

    @abstractmethod
    def BindEvent(self, evt, handler):
        raise NotImplementedError

    @abstractmethod
    def DeleteAll(self):
        raise NotImplementedError

    @abstractmethod
    def CollapseChildren(self, itm):
        raise NotImplementedError

    @abstractmethod
    def GetNodeFromItem(self, itm):
        raise NotImplementedError

    @abstractmethod
    def Select(self, itm):
        raise NotImplementedError


class WinTreeCTRL(TreeCTRL):
    def __init__(self, *args, **kwargs):
        self._inner = wx.TreeCtrl(*args, **kwargs)

    @property
    def widget(self):
        return self._inner

    def AddRoot(self, node, expanded):
        itm = self._inner.AddRoot(str(node))
        self._inner.SetItemData(itm, node)
        if expanded:
            self._inner.Expand(itm)
        return itm

    def AddChild(self, rootitm, node, expanded):
        itm = self._inner.AppendItem(rootitm, str(node))
        self._inner.SetItemData(itm, node)
        if expanded:
            self._inner.Expand(itm)
        return itm

    def BindEvent(self, evt, handler):
        TreeEventsToWXEvents = {
            TreeEvent.ITEM_SELECTED: wx.EVT_TREE_SEL_CHANGED,
            TreeEvent.ITEM_EXPANDED: wx.EVT_TREE_ITEM_EXPANDED,
            TreeEvent.ITEM_COLLAPSED: wx.EVT_TREE_ITEM_COLLAPSED,
            TreeEvent.CONTEXT_MENU: wx.EVT_TREE_ITEM_MENU,
            TreeEvent.KEY_DOWN: wx.EVT_KEY_DOWN,
        }
        return self._inner.Bind(TreeEventsToWXEvents[evt], handler)

    def DeleteAll(self):
        return self._inner.DeleteAllItems()

    def CollapseChildren(self, itm):
        return self._inner.CollapseAllChildren(itm)

    def GetNodeFromItem(self, itm):
        return self._inner.GetItemData(itm)

    def Select(self, itm):
        return self._inner.SelectItem(itm)


class MacTreeCTRL(TreeCTRL):
    def __init__(self, *args, **kwargs):
        self._inner = wx.dataview.DataViewTreeCtrl(*args, **kwargs)
        self._inner.Bind(
            wx.dataview.EVT_DATAVIEW_ITEM_START_EDITING, lambda event: event.Veto()
        )  # block editing

    @property
    def widget(self):
        return self._inner

    def AddRoot(self, node, expanded):
        itm = self._inner.AppendContainer(
            wx.dataview.NullDataViewItem, str(node), expanded=expanded, data=node
        )
        return itm

    def AddChild(self, rootitm, node, expanded):
        if node.children:
            itm = self._inner.AppendContainer(
                rootitm, str(node), expanded=expanded, data=node
            )
        else:
            itm = self._inner.AppendItem(rootitm, str(node), data=node)
        return itm

    def BindEvent(self, evt, handler):
        TreeEventsToWXEvents = {
            TreeEvent.ITEM_SELECTED: wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED,
            TreeEvent.ITEM_EXPANDED: wx.dataview.EVT_DATAVIEW_ITEM_EXPANDED,
            TreeEvent.ITEM_COLLAPSED: wx.dataview.EVT_DATAVIEW_ITEM_COLLAPSED,
            TreeEvent.CONTEXT_MENU: wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU,
            TreeEvent.KEY_DOWN: wx.EVT_KEY_DOWN,
        }
        if evt == TreeEvent.CONTEXT_MENU:
            # VoiceOver seems not to be able to activate the context menu (VO+shift+m does nothing).
            # As a fallback, also bind to item activation.
            self._inner.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, handler)
        return self._inner.Bind(TreeEventsToWXEvents[evt], handler)

    def DeleteAll(self):
        return self._inner.DeleteAllItems()

    def CollapseChildren(self, itm):
        return self._inner.Collapse(
            itm
        )  # DataViewTreeCtrl seems not to support collapsing children

    def GetNodeFromItem(self, itm):
        return self._inner.GetItemData(itm)

    def Select(self, itm):
        return self._inner.Select(itm)
