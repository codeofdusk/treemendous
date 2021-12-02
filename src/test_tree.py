"""
Unit tests for tree module.
Copyright 2021 Bill Dengler and open-source contributors
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

import unittest

from tree import Node


class TestNode(unittest.TestCase):
    SIMPLE_TREE_DICT = {
        "label": "TP",
        "value": None,
        "children": [
            {"label": "DP", "value": None, "children": []},
            {"label": "T<bar/>", "value": None, "children": []},
        ],
    }

    SIMPLE_QTREE = "\Tree [.TP\n" "  DP\n" "  T$^{\prime}$\n" "]\n"

    def test_init_empty(self):
        n = Node()
        self.assertIsNone(n.label)
        self.assertIsNone(n.value)
        self.assertEqual(len(n.children), 0)
        self.assertIsNone(n.parent)

    def test_string_empty(self):
        n = Node()
        self.assertEqual(str(n), "UNLABELLED")

    def test_string_label_only(self):
        n = Node()
        n.label = "TP"
        self.assertEqual(str(n), "TP")

    def test_string_label_and_value(self):
        n = Node()
        n.label = "D"
        n.value = "I"
        self.assertEqual(str(n), "D: I")

    def test_string_value_only(self):
        n = Node()
        n.value = "val"
        self.assertEqual(str(n), "UNLABELLED: val")

    def test_add_child(self):
        tp = Node()
        dp = Node()
        tp.label = "TP"
        dp.label = "DP"
        tp.add_child(dp)
        self.assertIn(dp, tp.children)
        self.assertEqual(dp.parent, tp)

    def test_add_child_connected(self):
        tp = Node(label="TP")
        dp = Node(label="DP")
        tp.add_child(dp)
        tp2 = Node(label="TP")
        with self.assertRaises(AssertionError):
            tp2.add_child(dp)

    def test_add_parent(self):
        dp = Node(label="DP")
        d = Node(label="D", value="the")
        dp.add_child(d)
        n = Node(label="N", value="cactus")
        dp.add_child(n)
        np = Node(label="NP")
        n.add_parent(np)
        self.assertIn(np, dp.children)
        self.assertEqual(np, n.parent)
        self.assertNotIn(n, dp.children)

    def test_add_parent_replacing_root(self):
        n = Node(label="N", value="cacti")
        np = Node(label="NP")
        with self.assertRaises(AssertionError):
            n.add_parent(np)

    def test_delete(self):
        dp = Node(label="DP")
        d = Node(label="D", value="the")
        dp.add_child(d)
        np = Node(label="NP")
        dp.add_child(np)
        n = Node(label="N", value="cactus")
        np.add_child(n)
        np.delete()
        self.assertNotIn(np, dp.children)
        self.assertNotIn(n, dp.children)

    def test_delete_root(self):
        n = Node()
        with self.assertRaises(AssertionError):
            n.delete()

    def test_from_dict_empty(self):
        n = Node.from_dict({})
        self.assertIsNone(n.label)
        self.assertIsNone(n.value)
        self.assertEqual(len(n.children), 0)
        self.assertIsNone(n.parent)

    def test_from_dict_label_only(self):
        n = Node.from_dict({"label": "TP"})
        self.assertEqual(n.label, "TP")
        self.assertIsNone(n.value)
        self.assertEqual(len(n.children), 0)
        self.assertIsNone(n.parent)

    def test_from_dict_label_and_value(self):
        n = Node.from_dict({"label": "D", "value": "I"})
        self.assertEqual(n.label, "D")
        self.assertEqual(n.value, "I")
        self.assertEqual(len(n.children), 0)
        self.assertIsNone(n.parent)

    def test_from_dict_value_only(self):
        n = Node.from_dict({"value": "val"})
        self.assertIsNone(n.label)
        self.assertEqual(n.value, "val")
        self.assertEqual(len(n.children), 0)
        self.assertIsNone(n.parent)

    def test_from_dict_simple(self):
        tp = Node.from_dict(TestNode.SIMPLE_TREE_DICT)
        self.assertEqual(tp.label, "TP")
        self.assertIsNone(tp.value)
        self.assertEqual(len(tp.children), 2)
        self.assertIsNone(tp.parent)
        dp = tp.children[0]
        self.assertEqual(dp.label, "DP")
        self.assertIsNone(dp.value)
        self.assertEqual(len(dp.children), 0)
        self.assertEqual(dp.parent, tp)
        tbar = tp.children[1]
        self.assertEqual(tbar.label, "T<bar/>")
        self.assertIsNone(tbar.value)
        self.assertEqual(len(tbar.children), 0)
        self.assertEqual(tbar.parent, tp)

    def test_to_dict_simple(self):
        tp = Node(label="TP")
        dp = Node(label="DP")
        tbar = Node(label="T<bar/>")
        tp.add_child(dp)
        tp.add_child(tbar)
        self.assertEqual(tp.to_dict(), TestNode.SIMPLE_TREE_DICT)

    def test_qtree_simple(self):
        self.assertEqual(
            Node.from_dict(TestNode.SIMPLE_TREE_DICT).to_qtree(), TestNode.SIMPLE_QTREE
        )

    def test_qtree_degenerate(self):
        self.assertEqual(Node(label="root").to_qtree(), "\Tree [.root\n]\n")

    def test_qtree_bold(self):
        self.assertEqual(
            Node(label="<b>root</b>").to_qtree(), "\Tree [.\\textbf{root}\n]\n"
        )

    def test_qtree_bold_unclosed(self):
        self.assertEqual(Node(label="<b>root").to_qtree(), "\Tree [.<b>root\n]\n")

    def test_qtree_bold_unopened(self):
        self.assertEqual(Node(label="root</b>").to_qtree(), "\Tree [.root</b>\n]\n")


if __name__ == "__main__":
    unittest.main()
