"""
This module contains the Node and Tree classes, for storing and manipulating tree data respectively.
Third-party implementations/interfaces should instantiate Tree and primarily call its methods. Data can be accessed from the root attribute, which contains the tree's root Node.
Copyright 2021 Bill Dengler and open-source contributors
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

__version__ = "1.0.0rc3"

import gettext
import html
import io
import json
import os
import zipfile

from collections import deque
from enum import Enum, auto
from html.parser import HTMLParser
from tempfile import mktemp
from typing import Optional, Set

_ = gettext.translation("treemendous", fallback=True).gettext


class GVParser(HTMLParser):
    TEX_MAP = {
        "b": "\\textbf{",
        "i": "\\textit{",
        "u": "\\underline{",
        "sup": "^{",
        "sub": "_{",
        "null": "{\O",
        "bar": "^{\prime",
    }
    MATHMODE_REQUIRED = ("sup", "sub", "null", "bar")
    SPECIALS = ("null", "bar")

    def reset(self, *args, **kwargs):
        self.valid = True
        self._tag_stack = deque()
        self._math_stack = deque()
        self.tex = ""
        self.data = ""
        return super().reset(*args, **kwargs)

    def close(self, *args, **kwargs):
        if self._tag_stack:  # If we have unclosed tags
            self.valid = False
        return super().close(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        if attrs:
            self.valid = False
        if tag not in GVParser.TEX_MAP:
            self.valid = False
            self.tex += f"<{tag}>"
        else:
            self._tag_stack.append(tag)
            if tag in GVParser.MATHMODE_REQUIRED:
                if not self._math_stack:
                    self.tex += "$"
                self._math_stack.append(tag)
            self.tex += GVParser.TEX_MAP[tag]
        if (
            tag in GVParser.SPECIALS
        ):  # some tags should be part of data (for node IDs, etc)
            self.data += tag.capitalize()

    def handle_endtag(self, tag):
        try:
            self.valid = self._tag_stack.pop() in GVParser.TEX_MAP
        except IndexError:
            self.valid = False
        if tag in GVParser.TEX_MAP:
            self.tex += "}"
        else:
            self.tex += f"</{tag}>"
        if tag in GVParser.MATHMODE_REQUIRED:
            self._math_stack.pop()
            if not self._math_stack:
                self.tex += "$"

    def handle_data(self, data):
        self.tex += data
        self.data += data


class Node:
    def __init__(self, label: str = None, value: str = None):
        self.label = label
        self.value = value
        self.children = []
        self.parent = None

    @classmethod
    def from_dict(cls, data: dict) -> "Node":
        res = cls(label=data.get("label"), value=data.get("value"))
        for c in data.get("children", []):
            res.add_child(cls.from_dict(c))
        return res

    def __repr__(self) -> str:
        # Translators: Placeholder text for a node without label.
        res = _("UNLABELLED")
        if self.label:
            res = self.label
        if self.value:
            res += ": " + self.value
        return res

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "value": self.value,
            "children": [c.to_dict() for c in self.children],
        }

    def to_qtree(self) -> str:
        def _qtree(node: Node, parser: HTMLParser, level: int = 0) -> str:
            parser.reset()
            parser.feed(node.label)
            parser.close()
            lbl = parser.tex if parser.valid else node.label
            if node.value:
                parser.reset()
                parser.feed(node.value)
                parser.close()
                val = parser.tex if parser.valid else node.value
            else:
                val = None
            leaf = not node.children and level > 0
            res = "  " * level + f"{'[.' if not leaf else ''}{lbl}"
            if val:
                res += f"\\\\{val}"
            res += "\n"
            for c in node.children:
                res += _qtree(c, parser, level + 1)
            if not leaf:
                res += "  " * level + "]\n"
            return res

        parser = GVParser()
        return "\\Tree " + _qtree(self, parser)

    def to_graphviz(
        self,
        dpi: Optional[int] = None,
        graph: Optional["graphviz.Graph"] = None,
        name_set: Optional[Set[str]] = None,
    ) -> "graphviz.Graph":
        def _fresh_name(name: str, names: Set[str]):
            if name == "":  # Some nodes in angle brackets have a blank ID
                name = "node"
            res = name
            num = 1
            while res in names:
                num += 1
                res = f"{name}{num}"
            names.add(res)
            return res

        def _is_valid(text: str, parser: HTMLParser) -> bool:
            parser.reset()
            parser.feed(text)
            parser.close()
            return parser.valid

        def _escape_if_needed(text: str, parser: HTMLParser) -> str:
            cleaned_text = text
            REPLACEMENTS = {"<null/>": "Ø", "<bar/>": "<sup>′</sup>"}
            for src, dest in REPLACEMENTS.items():
                cleaned_text = cleaned_text.replace(src, dest)
            valid = _is_valid(text, parser)
            if valid:
                return cleaned_text
            else:
                return html.escape(text)

        def _add_node(
            node: Node,
            graph: "graphviz.Graph",
            name_set: Set[str],
            parser: HTMLParser,
            parent: Node = None,
        ) -> None:
            parser.reset()
            parser.feed(node.label)
            id = _fresh_name(parser.data, name_set)
            if node.value:
                label = f"<{_escape_if_needed(node.label, parser)}<br/>{_escape_if_needed(node.value, parser)}>"
            else:
                label = _escape_if_needed(node.label, parser)
                if _is_valid(label, parser):
                    label = "<" + label + ">"
            graph.node(id, label)
            if parent:
                graph.edge(parent, id)
            for c in node.children:
                _add_node(c, graph, name_set, parser, parent=id)

        import graphviz

        graph = graphviz.Graph(
            format="png",
            node_attr={"shape": "plain"},
            graph_attr={
                "dpi": str(dpi) if dpi is not None else "400",
                "nodesep": ".25",
                "ranksep": "0.02",
            },
        )  # ranksep is height of edges in inches, minimum is 0.02
        name_set = set()
        parser = GVParser()
        _add_node(self, graph, name_set, parser)
        return graph

    def add_child(self, c: "Node") -> None:
        assert c.parent is None
        self.children.append(c)
        c.parent = self

    def delete(self) -> None:
        assert self.parent is not None  # Deleting the root is a special case
        self.parent.children.remove(self)

    def add_parent(self, node: "Node") -> None:
        assert self.parent is not None  # Replacing the root is a special case
        assert node.parent is None
        i = self.parent.children.index(self)
        node.parent = self.parent
        del self.parent.children[i]
        self.parent.children.insert(i, node)
        self.parent = None
        node.add_child(self)


class Location(Enum):
    CHILD = auto()
    PARENT = auto()
    SIBLING = auto()


class TreemendousError(Exception):
    pass


class SaveError(TreemendousError):
    pass


class SelectionError(TreemendousError):
    pass


class IncompatibleFormatError(TreemendousError):
    pass


DEFAULT_MANIFEST: dict = {"version": __version__}


_pasteboard: dict = None


class Tree:
    def __init__(self, path: str = None):
        self.dirty: bool = False
        self.last_path: str = path or ""
        self.selection: Node = None
        self.manifest: dict = DEFAULT_MANIFEST.copy()

        if path:
            try:
                with zipfile.ZipFile(path) as zip:
                    with zip.open("manifest.json") as fin:
                        m = json.load(fin)
                        self.manifest.update(m)
                        my_major = int(__version__.split(".")[0])
                        their_major = int(self.manifest["version"].split(".")[0])
                        if my_major < their_major:
                            raise IncompatibleFormatError(
                                _(
                                    # Translators: A warning message displayed when a file is too new for the current Treemendous version.
                                    "This file is too new for the currently running version of Treemendous ({my_version}). Please upgrade to Treemendous {their_version} or later."
                                ).format(
                                    my_version=__version__,
                                    their_version=f"{their_major}.0.0",
                                )
                            )
                    with zip.open("tree.json") as fin:
                        d = json.load(fin)
                        self.root: Node = Node.from_dict(d)
            except (KeyError, zipfile.BadZipFile):
                raise IncompatibleFormatError(
                    # Translators: An error message displayed when a Treemendous file could not be read.
                    _("Invalid, very outdated, or damaged Treemendous file.")
                )
        else:
            self.root: Node = None

    @property
    def is_empty(self) -> bool:
        "Returns True on trees that do not contain any nodes."
        return not self.root

    @property
    def notes(self) -> str:
        "Free-form notes that can be entered and displayed along with the tree, such as the phrase from which a syntax tree was constructed."
        return self.manifest.get("notes", "")

    @notes.setter
    def notes(self, new: str):
        self.manifest["notes"] = new
        self.dirty = True

    def save(self, path: str = None) -> None:
        "Save the tree as a .treemendous, .gv (Graphviz markup), or .png file."
        if not path:
            if self.last_path:
                path = self.last_path
            else:
                raise SaveError("No last path")
        if path.endswith(".gv"):
            g = self.root.to_graphviz()
            if self.last_path:
                g.name = os.path.splitext(os.path.basename(self.last_path))[0]
            return g.save(path)
        if path.endswith(".png"):
            return self.graphviz(path)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_LZMA) as zip:
            with zip.open("tree.json", "w") as cam:
                json.dump(self.root.to_dict(), io.TextIOWrapper(cam), indent=2)
            with zip.open("manifest.json", "w") as cam:
                json.dump(self.manifest, io.TextIOWrapper(cam), indent=2)
        self.dirty = False
        self.last_path = path

    def qtree(self) -> str:
        "Renders this tree as LaTeX (dependant on qtree) markup."
        # Translators: The comment added at the top of a LaTeX document. The \usepackage{qtree} is LaTeX code that should not be translated.
        COMMENT = _("Add \\usepackage{qtree} to the preamble of your document.")
        return f"% {COMMENT}\n\n{self.root.to_qtree()}"

    def graphviz(self, path: str = None, dpi: Optional[int] = None) -> None:
        "Renders this tree as a .png image using Graphviz."
        g = self.root.to_graphviz(dpi=dpi)
        if path is None:
            path = mktemp(prefix="treemendous")
        else:
            path = os.path.splitext(path)[0]
        if self.last_path:
            g.name = os.path.splitext(os.path.basename(self.last_path))[0]
        return g.render(path, cleanup=True)

    def _add(self, where: Location, new: Node) -> None:
        assert isinstance(where, Location)
        if self.is_empty:
            self.root = new
        elif self.selection is None:
            raise SelectionError("No selection!")
        elif where == Location.CHILD:
            self.selection.add_child(new)
        elif where == Location.PARENT:
            if self.selection == self.root:
                new.add_child(self.root)
                self.root = new
            else:
                self.selection.add_parent(new)
        elif where == Location.SIBLING:
            if self.selection == self.root:
                raise TreemendousError("The root cannot have siblings!")
            self.selection.parent.add_child(new)
        self.selection = new
        self.dirty = True

    def add(self, where: Location, label: str = None, value: str = None) -> None:
        "Adds a new node at the location specified as a member of the Location enumeration in this module."
        if label == "":
            label = None
        if value == "":
            value = None
        new = Node(label, value)
        return self._add(where=where, new=new)

    def edit(self, label: str = None, value: str = None) -> None:
        "Edits the currently selected node."
        if label is not None:
            if label == "":
                self.selection.label = None
                self.dirty = True
            else:
                self.selection.label = label
                self.dirty = True
        if value is not None:
            if value == "":
                self.selection.value = None
                self.dirty = True
            else:
                self.selection.value = value
                self.dirty = True

    def delete(self) -> None:
        "Deletes the currently selected node and all descendants."
        if not self.selection:
            raise SelectionError("No selection!")
        n = self.selection
        if n == self.root:
            self.root = None
        else:
            self.selection = n.parent
            n.delete()
        self.dirty = True

    def copy(self) -> None:
        "Copys the current selection to a (Treemendous internal) pasteboard."
        if self.selection is None:
            raise SelectionError("No selection!")
        global _pasteboard
        _pasteboard = self.selection.to_dict()

    def paste(self, where: Location) -> None:
        "Pastes the contents of the (Treemendous internal) pasteboard to the location specified as a member of the Location enumeration in this module."
        global _pasteboard
        if not _pasteboard:
            raise SelectionError("Pasteboard is empty!")
        new = Node.from_dict(_pasteboard)
        self._add(where=where, new=new)

    def _shift(self, direction: int) -> None:
        if not self.selection:
            raise SelectionError("No selection!")
        elif self.selection == self.root:
            raise TreemendousError("Cannot shift the root!")
        t = self.selection.parent.children
        old = t.index(self.selection)
        new = old + direction
        t.insert(new, t.pop(old))
        self.dirty = True

    def move_up(self) -> None:
        "Moves the currently selected node up relative to its siblings."
        return self._shift(-1)

    def move_down(self) -> None:
        "Moves the currently selected node down relative to its siblings."
        return self._shift(1)
