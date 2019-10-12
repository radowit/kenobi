from six.moves import range

#    Copyright 2008 Peter Bulychev
#    http://clonedigger.sourceforge.net
#
#    This file is part of Clone Digger.
#
#    Clone Digger is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Clone Digger is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Clone Digger.  If not, see <http://www.gnu.org/licenses/>.


class SuffixTree:
    class StringPosition:
        def __init__(self, string, position, prevelem):
            self.string = string
            self.position = position
            self.prevelem = prevelem

    class SuffixTreeNode:
        def __init__(self):
            self.childs = {}
            self.string_positions = []
            self.ending_strings = []

    def __init__(self, f_code):
        self._node = self.SuffixTreeNode()
        self._f_code = f_code

    def _add(self, string, prevelem):
        pos = 0
        node = self._node
        for pos in range(len(string)):
            e = string[pos]
            code = self._f_code(e)
            node.string_positions.append(self.StringPosition(string, pos, prevelem))
            if code not in node.childs:
                node.childs[code] = self.SuffixTreeNode()
            node = node.childs[code]
        node.ending_strings.append(self.StringPosition(string, pos + 1, prevelem))

    def add(self, string):
        for i in range(len(string)):
            if i == 0:
                prevelem = None
            else:
                prevelem = self._f_code(string[i - 1])
            self._add(string[i:], prevelem)

    def getBestMaxSubstrings(
        self, threshold, f, f_elem, node=None, initial_threshold=None
    ):
        if initial_threshold is None:
            initial_threshold = threshold

        def check_left_diverse_and_add(s1, s2, p):
            if (
                (s1.prevelem is None)
                or (s2.prevelem is None)
                or (s1.prevelem != s2.prevelem)
            ) and s1.position > p:
                candidate = (s1.string[: s1.position - p], s2.string[: s2.position - p])
                if (
                    f_elem(candidate[0]) >= initial_threshold
                    or f_elem(candidate[1]) >= initial_threshold
                ):
                    r.append(candidate)
                return True
            else:
                return False

        if node is None:
            node = self._node
        r = []
        if threshold <= 0:
            for s1 in node.ending_strings:
                for s2 in node.string_positions:
                    if s1.string == s2.string:
                        continue
                    check_left_diverse_and_add(s1, s2, 0)
            for i in range(len(node.ending_strings)):
                for j in range(i):
                    s1 = node.ending_strings[i]
                    s2 = node.ending_strings[j]
                    check_left_diverse_and_add(s1, s2, 0)
            for i in range(len(list(node.childs.keys()))):
                for j in range(i):
                    c1 = list(node.childs.keys())[i]
                    c2 = list(node.childs.keys())[j]
                    for s1 in (
                        node.childs[c1].string_positions
                        + node.childs[c1].ending_strings
                    ):
                        for s2 in (
                            node.childs[c2].string_positions
                            + node.childs[c2].ending_strings
                        ):
                            check_left_diverse_and_add(s1, s2, 1)
        for (code, child) in node.childs.items():
            r += self.getBestMaxSubstrings(
                threshold - f(code), f, f_elem, child, initial_threshold
            )
        return r
