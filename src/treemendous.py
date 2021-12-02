"""
This module contains the Treemendous GUI and is the entry point for the program.
Copyright 2021 Bill Dengler and open-source contributors
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Build-time options
# nuitka-project: --standalone
# nuitka-project: --enable-plugin=anti-bloat
# nuitka-project-if: {OS} == "Windows":
#    nuitka-project: --windows-disable-console
# nuitka-project-if: {OS} == "Darwin":
#    nuitka-project: --macos-disable-console
#    nuitka-project: --macos-create-app-bundle


import argparse
import gettext
import json
import os
import platform
import urllib.request
import webbrowser
import wx

from graphviz import ExecutableNotFound as GraphvizNotFound
from json.decoder import JSONDecodeError
from menus import AddNodeMenu, NodeContextMenu, PasteDestMenu
from pkg_resources import packaging
from sys import maxsize
from tree import (
    __version__,
    IncompatibleFormatError,
    Location,
    SaveError,
    SelectionError,
    Tree,
)
from treectrl import MacTreeCTRL, TreeEvent, WinTreeCTRL
from urllib.error import URLError

_ = gettext.translation("treemendous", fallback=True).gettext

# Translators: The name of the Treemendous file format, to be shown in the "files of type" combobox.
TREEMENDOUS_FMT = _("Treemendous files")
# Translators: The name of the Graphviz file format, to be shown in the "files of type" combobox.
GRAPHVIZ_FMT = _("Graphviz files")
# Translators: a label to be shown in the "files of type" combobox.
PNG_FMT = _("Images")

WILDCARD = f"{TREEMENDOUS_FMT} (*.treemendous)|*.treemendous"
# TODO: According to the WXPython docs, the native Motif dialog can't handle
# this. If someone shouts, try and detect Motif and use WILDCARD instead of
# SAVE_WILDCARD (disabling gv functionality) or show split dialogs for
# GV/Treemendous saving.
SAVE_WILDCARD = (
    f"{TREEMENDOUS_FMT} (*.treemendous)|*.treemendous"
    f"|{GRAPHVIZ_FMT} (*.gv)|*.gv"
    f"|{PNG_FMT} (*.png)|*.png"
)

GRAPHVIZ_DOWNLOAD_URL = "https://graphviz.org/download/"

AUTOUPDATE_ENDPOINT = "https://raw.githubusercontent.com/codeofdusk/treemendous/master/channels/stable.json"
AUTOUPDATE_SCHEMA_VERSION = 1


class EditNodeDialog(wx.Dialog):
    def __init__(self, title, label=None, value=None):
        if label is None:
            label = ""
        if value is None:
            value = ""
        super().__init__(parent=None, title=title)
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        fgs = wx.FlexGridSizer(2, 2, 5, 5)
        # label box
        labelLbl = wx.StaticText(
            panel,
            # Translators: The label for the node label field in the edit node dialog.
            label=_("&Label:"),
        )
        self.label = wx.TextCtrl(panel, value=label)
        # value box
        valueLbl = wx.StaticText(
            panel,
            # Translators: The label for the node value field in the edit node dialog.
            label=_("&Value:"),
        )
        self.value = wx.TextCtrl(panel, value=value)
        # put boxes into sizer
        fgs.AddMany(
            [
                (labelLbl),
                (self.label, 1, wx.EXPAND),
                (valueLbl),
                (self.value, 1, wx.EXPAND),
            ]
        )
        fgs.AddGrowableCol(1, 1)
        vbox.Add(
            fgs, proportion=1, flag=wx.TOP | wx.RIGHT | wx.LEFT | wx.EXPAND, border=5
        )
        # button box
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        ok = wx.Button(panel, wx.ID_OK)
        ok.SetDefault()
        cancel = wx.Button(panel, wx.ID_CANCEL)
        btnSizer.Add(ok)
        btnSizer.Add(cancel)
        vbox.Add(btnSizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        # bring everything together
        panel.SetSizer(vbox)


class ReadOnlyViewDialog(wx.Dialog):
    def __init__(self, title, text):
        super().__init__(parent=None, title=title)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.output = wx.TextCtrl(
            self,
            wx.ID_ANY,
            size=(500, 500),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
            value=text,
        )
        self.output.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        mainSizer.Add(self.output, proportion=1, flag=wx.EXPAND)
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)

    def onKeyDown(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_ESCAPE:
            return self.Close()
        event.Skip()


class VisualViewDialog(wx.Dialog):
    def __init__(self, path, platform):
        self.path = path
        self.platform = platform
        file = wx.Image(path, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        (self.imgWidth, self.imgHeight) = (file.GetWidth(), file.GetHeight())
        self.imgSize = wx.Size(self.imgWidth, self.imgHeight)
        self.imgProportion = self.imgWidth / self.imgHeight

        super().__init__(
            parent=None,
            # Translators: The title of a dialog used to show the visual representation of a tree.
            title=_("Visual rendering"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=self.imgSize,
        )
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.bmp = wx.Bitmap(self.path)
        self.img = wx.StaticBitmap(
            self, wx.ID_ANY, self.bmp, (0, 0), (self.imgWidth, self.imgHeight)
        )
        self.Bind(
            wx.EVT_CHAR_HOOK, self.onCharHook
        )  ## Use EVT_CHAR_HOOK here, because dialogs don't send EVT_KEY_DOWN on all platforms
        self.mainSizer.Add(self.img, proportion=1, flag=wx.EXPAND | wx.ALL, border=15)
        self.SetSizerAndFit(self.mainSizer)

    def onCharHook(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_ESCAPE:
            return self.Close()
        event.Skip()

    def OnSize(self, event):
        (dialogWidth, dialogHeight) = self.GetSize()
        if self.platform not in ("Windows", "Darwin"):
            # magic numbers are needed to make sure the image doesn't go outside the bounds of the dialog window
            dialogWidthAdjust = -50
            dialogHeightAdjust = -90
            dialogWidth += dialogWidthAdjust
            dialogHeight += dialogHeightAdjust
        dialogProportion = dialogWidth / dialogHeight
        if dialogProportion > self.imgProportion:
            newHeight = dialogHeight
            newWidth = self.imgWidth * (dialogHeight / self.imgHeight)
        else:
            newHeight = self.imgHeight * (dialogWidth / self.imgWidth)
            newWidth = dialogWidth
        # make sure we're scaling from a fresh load of the image
        self.img.SetBitmap(self.scaleBitmap(self.bmp, newWidth, newHeight))
        self.Refresh()

    def scaleBitmap(self, bitmap, width, height):
        image = bitmap.ConvertToImage()
        image = image.Scale(round(width), round(height), wx.IMAGE_QUALITY_HIGH)
        result = wx.Bitmap(image)
        return result


class Editor(wx.Frame):
    def __init__(self, path=None, system=None):
        wx.Frame.__init__(self, parent=None, title="Treemendous")

        # Variables.
        self.tree = Tree()
        self.treectrl = None
        self._expanded = []
        if system:
            self.platform = system
        else:
            self.platform = platform.system()
        if self.platform != "Windows":
            msg = wx.MessageDialog(
                self,
                _(
                    # Translators: A message shown when a user launches Treemendous on an unsupported OS.
                    "Support for your operating system ({platform}) has not been fully verified by the Treemendous developers. If you proceed, a baseline level of functionality and accessibility may be present, but the user experience may not be complete or native to your system. In particular, tree nodes may appear in the wrong order, and some keyboard commands may not function at all or as intended. If the usual commands for opening the context menu on a tree node do not work, try pressing enter or double-clicking the selected node with the mouse. If the arrow keys do not expand/collapse nodes, try plus/minus."
                ).format(platform=self.platform),
                # Translators: The title of a message box.
                _("OS not supported"),
                wx.OK | wx.OK_DEFAULT | wx.CANCEL | wx.ICON_WARNING,
            )
            if msg.ShowModal() != wx.ID_OK:
                raise RuntimeError("OS not supported")

        self.AutoUpdate()

        # Setting up menubar.
        menubar = wx.MenuBar()

        file = wx.Menu()
        new = wx.MenuItem(
            file,
            wx.ID_NEW,
            # Translators: An item in the file menu.
            _("&New\tCtrl+n"),
            # Translators: Help text for "new" in the file menu.
            _("Creates a new blank Treemendous instance."),
        )
        file.Append(new)

        open = wx.MenuItem(
            file,
            wx.ID_OPEN,
            # Translators: An item in the file menu.
            _("&Open\tCtrl+O"),
            # Translators: Help text for "open" in the file menu.
            _("Open an existing tree."),
        )
        file.Append(open)
        file.AppendSeparator()

        save = wx.MenuItem(
            file,
            wx.ID_SAVE,
            # Translators: An item in the file menu.
            _("&Save\tCtrl+S"),
            # Translators: Help text for "save" in the file menu.
            _("Save this tree to disk."),
        )
        file.Append(save)

        saveas = wx.MenuItem(
            file,
            wx.ID_SAVEAS,
            # Translators: An item in the file menu.
            _("Save &as...\tShift+Ctrl+S"),
            # Translators: Help text for "save as" in the file menu.
            _("Save this tree to a different location."),
        )
        file.Append(saveas)
        file.AppendSeparator()

        quit = wx.MenuItem(
            file,
            wx.ID_EXIT,
            # Translators: An item in the file menu.
            _("&Quit\tCtrl+Q"),
            # Translators: Help text for "quit" in the file menu.
            _("Exit Treemendous."),
        )
        file.Append(quit)

        edit = wx.Menu()
        copy = wx.MenuItem(
            edit,
            wx.ID_COPY,
            # Translators: An item in the edit menu.
            _("Copy\tCTRL+c"),
            # Translators: Help text for "copy" in the edit menu.
            "Copy the currently selected node to the pasteboard.",
        )
        paste = wx.MenuItem(
            edit,
            wx.ID_PASTE,
            # Translators: An item in the edit menu.
            _("Paste\tCTRL+v"),
            _(
                # Translators: Help text for "paste" in the edit menu.
                "Place the contents of the pasteboard in the tree at the specified position."
            ),
        )
        edit.Append(copy)
        edit.Append(paste)

        view = wx.Menu()
        self.viewVisualMenuItem = wx.MenuItem(
            view,
            wx.ID_ANY,
            # Translators: An item in the "view" menu.
            _("&Visual"),
            _(
                # Translators: Help text for "visual" in the view menu.
                "Show a graphical representation of this tree."
            ),
        )
        view.Append(self.viewVisualMenuItem)
        self.NotesCheckBox = wx.MenuItem(
            view,
            wx.ID_ANY,
            # Translators: An item in the "view" menu that toggles the display of the notes window.
            # The notes window allows users to enter freeform text along with their tree.
            _("&Notes"),
            _(
                # Translators: Help text for "notes" in the view menu.
                "Show or hide the notes window, which allows entry of freeform text to be shown along with the tree."
            ),
            kind=wx.ITEM_CHECK,
        )
        view.Append(self.NotesCheckBox)
        self.qtreeMenuItem = wx.MenuItem(
            view,
            wx.ID_ANY,
            # Translators: An item in the "view" menu.
            _("La&TeX (Qtree)"),
            _(
                # Translators: Help text for "LaTeX" in the view menu.
                "Show this tree as source code suitable for pasting into a LaTeX document. Requires that the qtree package be included in the document preamble."
            ),
        )
        view.Append(self.qtreeMenuItem)

        help = wx.Menu()
        about = wx.MenuItem(
            help,
            wx.ID_ABOUT,
            # Translators: An item in the help menu.
            _("&About\tF1"),
            # Translators: Help text for the "about" option in the help menu. Please indicate that this dialog is always in English.
            _("View version and licence."),
        )
        help.Append(about)

        menubar.Append(
            file,
            # Translators: The name of a menu in the menu bar.
            _("&File"),
        )
        menubar.Append(
            edit,
            # Translators: The name of a menu in the menu bar.
            _("&Edit"),
        )
        menubar.Append(
            view,
            # Translators: The name of a menu in the menu bar.
            _("&View"),
        )
        menubar.Append(
            help,
            # Translators: The name of a menu in the menu bar.
            _("&Help"),
        )

        self.SetMenuBar(menubar)

        self.panel = wx.Panel(self)

        notesSizer = wx.BoxSizer(wx.VERTICAL)
        self.notesLbl = wx.StaticText(
            self.panel,
            # Translators: The label for the notes window.
            label=_("&Notes:"),
        )
        notesSizer.Add(self.notesLbl)
        self.notesField = wx.TextCtrl(
            self.panel, style=wx.TE_MULTILINE | wx.TE_RICH2, value=self.tree.notes
        )
        notesSizer.Add(self.notesField, flag=wx.EXPAND | wx.TOP | wx.BOTTOM)

        self.notesField.Bind(wx.EVT_TEXT, self.OnNotesChanged)

        self.addNodeButton = wx.Button(
            self.panel,
            # Translators: The label of the add node button in the main window.
            label=_("&Add..."),
        )
        self.addNodeButton.Bind(wx.EVT_BUTTON, self.OnAddNode)

        self.Bind(wx.EVT_MENU, self.NewInstance, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.OnOpenFile, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSaveFile, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSaveAsFile, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.QuitApplication, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, self.OnPaste, id=wx.ID_PASTE)
        self.Bind(wx.EVT_MENU, self.OnEditNode, id=wx.ID_EDIT)
        self.Bind(wx.EVT_MENU, self.OnDeleteNode, id=wx.ID_DELETE)
        self.Bind(wx.EVT_MENU, self.OnViewVisual, self.viewVisualMenuItem)
        self.Bind(wx.EVT_MENU, self.OnToggleNotes, self.NotesCheckBox)
        self.Bind(wx.EVT_MENU, self.OnQtree, self.qtreeMenuItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_CLOSE, self.QuitApplication)

        fgs = wx.FlexGridSizer(3, 1, 5, 5)
        self.InitTree()
        fgs.Add(self.treectrl.widget, wx.ID_ANY, wx.EXPAND | wx.ALL, border=3)
        fgs.Add(
            notesSizer,
            wx.ID_ANY,
            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            border=3,
        )
        fgs.Add(self.addNodeButton, flag=wx.LEFT | wx.RIGHT, border=3)

        fgs.AddGrowableRow(0, 1)
        fgs.AddGrowableCol(0, 1)

        self.panel.SetSizer(fgs)

        self.StatusBar()

        self.Centre()

        if path is not None:
            self.OpenTree(path)

        self.RenderTree()

        notesenabled = bool(self.tree.notes)
        self.EnableNotes(notesenabled)

        self.Show()

    def InitTree(self):
        ctrl = WinTreeCTRL if self.platform == "Windows" else MacTreeCTRL
        self.treectrl = ctrl(self.panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize)
        self.treectrl.BindEvent(TreeEvent.ITEM_SELECTED, self.OnSelectionChanged)
        self.treectrl.BindEvent(TreeEvent.ITEM_EXPANDED, self.OnExpand)
        self.treectrl.BindEvent(TreeEvent.ITEM_COLLAPSED, self.OnCollapse)
        self.treectrl.BindEvent(TreeEvent.CONTEXT_MENU, self.OnNodeContextMenu)
        self.treectrl.BindEvent(TreeEvent.KEY_DOWN, self.OnTreeKeyDown)

    def RenderTree(self):
        sel = self.tree.selection
        root = None
        toExpand = []

        def _initializeLevel(guiRoot, treeRoot):
            r = self.treectrl.AddChild(guiRoot, treeRoot, treeRoot in self._expanded)
            if treeRoot == sel:
                self.treectrl.Select(r)
            for c in treeRoot.children:
                _initializeLevel(r, c)

        self.UpdateName()

        self.viewVisualMenuItem.Enable(not self.tree.is_empty)
        self.qtreeMenuItem.Enable(not self.tree.is_empty)

        if not self.treectrl:
            self.InitTree()
        else:
            self.treectrl.DeleteAll()
        if not self.tree.is_empty:
            root = self.treectrl.AddRoot(
                self.tree.root, self.tree.root in self._expanded
            )
            if sel is None or sel == self.tree.root:
                self.treectrl.Select(root)
            for c in self.tree.root.children:
                _initializeLevel(root, c)
        self.treectrl.widget.SetFocus()

    def UpdateName(self):
        title = "Treemendous"
        if self.tree.last_path:
            name = os.path.splitext(os.path.basename(self.tree.last_path))[0]
            title = f"{name} – {title}"
        if self.tree.dirty:
            title = f"*{title}"
        self.SetTitle(title)

    def AutoUpdate(self):
        try:
            req = urllib.request.Request(
                AUTOUPDATE_ENDPOINT,
                headers={
                    "User-Agent": f"Mozilla/5.0 (compatible; python-Treemendous/{__version__}; +https://github.com/codeofdusk/treemendous)"
                },
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        except (URLError, JSONDecodeError) as e:
            # Translators: Part of a message printed to the command line when the update check could not be completed.
            UPDATE_FAIL = _("Error while checking for updates:")
            print(f"{UPDATE_FAIL} {e}")
            return
        if AUTOUPDATE_SCHEMA_VERSION < resp.get("schema_version", maxsize):
            return self.UpdateAvailable(required=True)
        my_version = packaging.version.parse(__version__)
        latest_version = packaging.version.parse(resp["latest_version"])
        minimum_version = packaging.version.parse(resp["minimum_version"])
        if my_version < minimum_version:
            return self.UpdateAvailable(
                version=resp["latest_version"], page=resp["release_page"], required=True
            )
        elif my_version < latest_version:
            return self.UpdateAvailable(
                version=resp["latest_version"],
                page=resp["release_page"],
                required=False,
            )

    def NewInstance(self, event):
        editor = Editor(system=self.platform)
        editor.Centre()
        editor.Show()

    def OnOpenFile(self, event):
        file_name = os.path.basename(self.tree.last_path)

        if self.tree.dirty:
            dlg = wx.MessageDialog(
                self,
                # Translators: The text of a prompt asking if the user wants to save unsaved changes (for instance, when closing the program or opening a new tree over top of the current).
                _("Save changes ?"),
                "Treemendous",
                wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION,
            )

            val = dlg.ShowModal()
            if val == wx.ID_YES:
                self.OnSaveFile(event)
                self.DoOpenFile()
            elif val == wx.ID_CANCEL:
                dlg.Destroy()
            else:
                self.DoOpenFile()
        else:
            self.DoOpenFile()

    def OpenTree(self, path):
        try:
            self.tree = Tree(path)
            self._expanded = []
            self.EnableNotes(bool(self.tree.notes))
        except (IncompatibleFormatError, IOError) as e:
            dlg = wx.MessageDialog(
                self,
                str(e),
                # Translators: The title of an error dialog shown when a Treemendous file could not be opened.
                _("Error"),
                wx.ICON_ERROR,
            )
            dlg.ShowModal()

    def DoOpenFile(self):
        open_dlg = wx.FileDialog(
            self,
            # Translators: The title of the open file dialog.
            message=_("Choose tree"),
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=WILDCARD,
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST | wx.FD_PREVIEW,
        )

        if open_dlg.ShowModal() == wx.ID_OK:
            path = open_dlg.GetPath()
            self.OpenTree(path)
            self.RenderTree()
            self.statusbar.SetStatusText("", 1)
        open_dlg.Destroy()

    def OnSaveFile(self, event):
        try:
            self.tree.save()
            self.statusbar.SetStatusText("", 1)
            self.UpdateName()
        except IOError as error:
            dlg = wx.MessageDialog(self, "Error saving file\n" + str(error))
            dlg.ShowModal()
        except SaveError:
            self.OnSaveAsFile(event)

    def OnSaveAsFile(self, event):
        save_dlg = wx.FileDialog(
            self,
            # Translators: The title of the "save tree as" dialog.
            message=_("Save tree as ..."),
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=SAVE_WILDCARD,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        save_dlg.SetFilterIndex(0)

        if save_dlg.ShowModal() == wx.ID_OK:
            path = save_dlg.GetPath()

            if path.endswith(".png"):
                msg = wx.MessageDialog(
                    self,
                    _(
                        # Translators: A message shown when a user tries to save an image.
                        "Image files are inaccessible to screen reader users. To ensure accessibility, please provide an additional accessible format, such as a textual discription, Treemendous file, or Graphviz source code whereever you distribute this image."
                    ),
                    # Translators: The title of a message box.
                    _("Accessibility warning"),
                    wx.OK | wx.OK_DEFAULT | wx.CANCEL | wx.ICON_WARNING,
                )
                if msg.ShowModal() != wx.ID_OK:
                    return

            try:
                self.tree.save(path=path)
                self.statusbar.SetStatusText(self.tree.last_path + " Saved", 0)
                self.statusbar.SetStatusText("", 1)
                self.UpdateName()
            except GraphvizNotFound:
                self.GetGraphviz()
            except IOError as error:
                # Translators: Text displayed in a message box before the OS error message when a file could not be saved.
                HEADER = _("Error saving file")
                dlg = wx.MessageDialog(self, f"{HEADER}\n{error}")
                dlg.ShowModal()
        save_dlg.Destroy()

    def QuitApplication(self, event):
        if self.tree.dirty:
            dlg = wx.MessageDialog(
                self,
                # Translators: The text of a prompt asking if the user wants to save unsaved changes (for instance, when closing the program or opening a new tree over top of the current).
                _("Save changes ?"),
                "Treemendous",
                wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION,
            )
            val = dlg.ShowModal()
            if val == wx.ID_YES:
                self.OnSaveFile(event)
                if not self.tree.dirty:
                    wx.Exit()
            elif val == wx.ID_CANCEL:
                dlg.Destroy()
            else:
                self.Destroy()
        else:
            self.Destroy()

    def OnSelectionChanged(self, event):
        self.tree.selection = self.treectrl.GetNodeFromItem(event.GetItem())

    def OnExpand(self, event):
        itm = event.GetItem()
        if itm.IsOk:
            self._expanded.append(self.treectrl.GetNodeFromItem(itm))

    def OnCollapse(self, event):
        itm = event.GetItem()
        if itm.IsOk:
            self._expanded.remove(self.treectrl.GetNodeFromItem(itm))
            self.treectrl.CollapseChildren(itm)

    def OnNotesChanged(self, event):
        self.tree.notes = self.notesField.GetValue()
        self.UpdateName()

    def OnToggleNotes(self, event):
        notesenabled = not self.notesField.Shown
        self.EnableNotes(notesenabled)

    def EnableNotes(self, notesenabled):
        # Changing the value of the notes field causes self.notes to be updated and the dirty flag to be set.
        # Unbind the event handler temporarily when  refreshing the field to avoid this.
        self.notesField.Unbind(wx.EVT_TEXT)
        self.notesField.SetValue(self.tree.notes)
        self.notesField.Bind(wx.EVT_TEXT, self.OnNotesChanged)
        self.notesLbl.Show(notesenabled)
        self.notesField.Show(notesenabled)
        self.NotesCheckBox.Check(notesenabled)
        self.panel.GetSizer().Layout()  # Update control sizing after show/hide

    def OnAddNode(self, event):
        if not self.tree.is_empty:
            self.PopupMenu(AddNodeMenu(self))
        else:
            self.DoAddChild()

    def DoAddChild(self):
        title = (
            # Translators: The name of the dialog for adding the first node to a tree.
            _("Add root")
            if self.tree.is_empty
            # Translators: The name of the dialog for adding a child (contained item) to a node labelled {label}.
            else _("Add child of {label}").format(label=self.tree.selection.label)
        )
        dlg = EditNodeDialog(title=title)
        if dlg.ShowModal() == wx.ID_OK:
            self.tree.add(Location.CHILD, dlg.label.GetValue(), dlg.value.GetValue())
            self.RenderTree()
        dlg.Destroy()

    def DoAddParent(self):
        # Translators: The name of the dialog for adding a parent (containg item) to a node labelled {label}.
        title = _("Add parent of {label}").format(label=self.tree.selection.label)
        dlg = EditNodeDialog(title=title)
        if dlg.ShowModal() == wx.ID_OK:
            self.tree.add(Location.PARENT, dlg.label.GetValue(), dlg.value.GetValue())
            self.RenderTree()
        dlg.Destroy()

    def DoAddSibling(self):
        # Translators: The name of the dialog for adding a sibling (item on same level) to a node labelled {label}.
        title = _("Add sibling of {label}").format(label=self.tree.selection.label)
        dlg = EditNodeDialog(title=title)
        if dlg.ShowModal() == wx.ID_OK:
            self.tree.add(Location.SIBLING, dlg.label.GetValue(), dlg.value.GetValue())
            self.RenderTree()
        dlg.Destroy()

    def OnCopy(self, event):
        self.tree.copy()

    def OnPaste(self, event):
        if not self.tree.is_empty:
            self.PopupMenu(PasteDestMenu(self, event))
        else:
            self.DoPaste(Location.CHILD, event)

    def DoPaste(self, location, event):
        try:
            self.tree.paste(location)
            self.RenderTree()
        except SelectionError:  # Raised when the pasteboard is empty
            event.Skip()

    def PasteChild(self, event):
        self.DoPaste(Location.CHILD, event)

    def PasteParent(self, event):
        self.DoPaste(Location.PARENT, event)

    def PasteSibling(self, event):
        self.DoPaste(Location.SIBLING, event)

    def OnNodeContextMenu(self, event):
        if self.tree.is_empty:
            return event.Skip()
        self.PopupMenu(NodeContextMenu(self))

    def OnTreeKeyDown(self, event):
        keycode = event.GetKeyCode()
        if event.AltDown():
            if keycode == wx.WXK_UP:
                return self.OnMoveUp(event)
            elif keycode == wx.WXK_DOWN:
                return self.OnMoveDown(event)
        if keycode == wx.WXK_F2:
            return self.OnEditNode(event)
        elif keycode == wx.WXK_DELETE:
            return self.OnDeleteNode(event)
        else:
            return event.Skip()

    def OnEditNode(self, event):
        dlg = EditNodeDialog(
            # Translators: The name of the dialog for editing a node labelled {label}.
            title=_("Editing {label}").format(label=self.tree.selection.label),
            label=self.tree.selection.label,
            value=self.tree.selection.value,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.tree.edit(label=dlg.label.GetValue(), value=dlg.value.GetValue())
            self.RenderTree()
        dlg.Destroy()

    def OnDeleteNode(self, event):
        # Translators: A confirmation message asking if the user wants to delete this node. Options are OK and cancel.
        LEAF_MSG = _("Are you sure that you want to delete this node?")
        NONLEAF_MSG = _(
            # Translators: A confirmation message asking if the user wants to delete this node and all of its descendants (children, grandchildren, etc.). Options are OK and cancel.
            "Are you sure that you want to delete this node and all descendants?"
        )
        dlg = wx.MessageDialog(
            self,
            LEAF_MSG if not self.tree.selection.children else NONLEAF_MSG,
            # Translators: Title of a message dialog confirming deletion of the node labelled {label}.
            _("Delete {label}").format(label=self.tree.selection.label),
            wx.OK | wx.OK_DEFAULT | wx.CANCEL | wx.ICON_WARNING,
        )

        val = dlg.ShowModal()
        if val == wx.ID_OK:
            self.tree.delete()
            self.RenderTree()

    def OnMoveUp(self, event):
        self.tree.move_up()
        self.RenderTree()

    def OnMoveDown(self, event):
        self.tree.move_down()
        self.RenderTree()

    def StatusBar(self):
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusWidths([-5, -2, -1])

    def GetGraphviz(self):
        dlg = wx.MessageDialog(
            self,
            _(
                # Translators: Text of a message shown when the user tries to use a function that requires Graphviz but doesn't have it installed.
                "Treemendous requires that Graphviz is installed to perform this action, but it could not be found. If you proceed, the Graphviz website will be opened in your web browser so that you can download and install it. During installation, if prompted, please select to have Graphviz added to the system path. You may need to restart Treemendous after installation."
            ),
            # Translators: The title of a message box.
            _("Graphviz required"),
            wx.OK | wx.OK_DEFAULT | wx.CANCEL | wx.ICON_QUESTION,
        )

        val = dlg.ShowModal()
        if val == wx.ID_OK:
            webbrowser.open(GRAPHVIZ_DOWNLOAD_URL)

    def UpdateAvailable(self, version=None, page=None, required=False):
        if required:
            flags = wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR
            # Translators: The title of a message box shown when a Treemendous update must be downloaded.
            title = _("Update required")
            if version:
                # Translators: Part of a message shown when a Treemendous update is required.
                body = _("An update to Treemendous {version} is required.").format(
                    version=version
                )
            else:
                # Translators: Part of a message shown when a Treemendous update is required.
                body = _("A Treemendous update is required.")
            if page:
                # Translators: Part of a message shown when a Treemendous update is required.
                footer = _(
                    "The release page will be opened in your web browser so that you can download and install the update."
                )
            else:
                # Translators: Part of a message shown when a Treemendous update is required.
                footer = _("This update must be downloaded and installed manually.")
        else:
            flags = wx.OK | wx.OK_DEFAULT | wx.CANCEL | wx.ICON_QUESTION
            # Translators: The title of a message box shown when a Treemendous update is available for download, but not required.
            title = _("Update available")
            if version:
                # Translators: Part of a message shown when a Treemendous update is available, but not required.
                body = _("An update to Treemendous {version} is available.").format(
                    version=version
                )
            else:
                # Translators: Part of a message shown when a Treemendous update is available, but not required.
                body = _("A Treemendous update is available.")
            if page:
                # Translators: Part of a message shown when a Treemendous update is available, but not required.
                footer = _(
                    "If you proceed, the release page will be opened in your web browser so that you can download and install the update."
                )
            else:
                # Translators: Part of a message shown when a Treemendous update is available, but not required.
                footer = _("Please manually download and install this update.")
        dlg = wx.MessageDialog(self, f"{body}\n{footer}", title, flags)

        val = dlg.ShowModal()
        if val == wx.ID_OK:
            if page:
                webbrowser.open(page)
            raise RuntimeError("Update requested, exiting.")

    def OnViewVisual(self, event):
        try:
            path = self.tree.graphviz(dpi=200)
        except GraphvizNotFound:
            self.GetGraphviz()
        else:
            dlg = VisualViewDialog(path, self.platform)
            dlg.ShowModal()
            dlg.Destroy()
            os.remove(path)

    def OnQtree(self, event):
        dlg = ReadOnlyViewDialog(
            # Translators: The title of a dialog displaying LaTeX source code for the currently opened tree.
            _("LaTeX source"),
            self.tree.qtree(),
        )
        dlg.ShowModal()
        dlg.Destroy()

    def OnAbout(self, event):
        dlg = wx.MessageDialog(
            self,
            (
                f"Treemendous {__version__}\n"
                "Copyright 2021 Bill Dengler and open-source contributors\n"
                "Licensed under the Mozilla Public License, v. 2.0: https://mozilla.org/MPL/2.0/"
            ),
            "Treemendous",
            wx.OK | wx.ICON_INFORMATION,
        )
        dlg.ShowModal()
        dlg.Destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path", help="The path of a .treemendous file to open on launch", nargs="?"
    )
    parser.add_argument(
        "--platform",
        help="Override the detected system platform used when drawing the UI (will probably break accessibility, only use for testing)",
        choices=("Windows", "Darwin", "Linux"),
    )
    args = parser.parse_args()
    app = wx.App()
    Editor(path=args.path, system=args.platform)
    app.MainLoop()
