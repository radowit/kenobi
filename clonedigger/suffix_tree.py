from six.moves import range
from .abstract_syntax_tree import StatementSequence

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


class SuffixTree(object):
    class StringPosition(object):
        def __init__(self, string, position, prevelem):
            self.string = string
            self.position = position
            self.prevelem = prevelem

    class SuffixTreeNode(object):
        def __init__(self):
            self.childs = {}
            self.string_positions = []
            self.ending_strings = []

    def __init__(self):
        self._node = self.SuffixTreeNode()

    def _add(self, string, prevelem):
        pos = 0
        node = self._node
        for pos, char in enumerate(string):
            code = char.mark
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
                prevelem = string[i - 1].mark
            self._add(string[i:], prevelem)

    def get_best_max_substrings(self, threshold, node=None, initial_threshold=None):
        if initial_threshold is None:
            initial_threshold = threshold

        def check_left_diverse_and_add(string_pos1, string_pos2, position_delta):
            def get_covered_line_numbers(candidate):
                return StatementSequence(candidate).covered_line_numbers_count()
            more_than_position_delta = (
                (string_pos1.prevelem is None)
                or (string_pos2.prevelem is None)
                or (string_pos1.prevelem != string_pos2.prevelem)
            ) and string_pos1.position > position_delta
            if more_than_position_delta:
                candidate = (
                    string_pos1.string[: string_pos1.position - position_delta],
                    string_pos2.string[: string_pos2.position - position_delta],
                )

                def more_than_thres(candidate):
                    return get_covered_line_numbers(candidate) >= initial_threshold
                if more_than_thres(candidate[0]) or more_than_thres(candidate[1]):
                    best_match_substrings.append(candidate)
                return True
            else:
                return False

        if node is None:
            node = self._node
        best_match_substrings = []
        if threshold <= 0:
            for string_pos1 in node.ending_strings:
                for string_pos2 in node.string_positions:
                    if string_pos1.string == string_pos2.string:
                        continue
                    check_left_diverse_and_add(string_pos1, string_pos2, 0)
            for i in range(len(node.ending_strings)):
                for j in range(i):
                    string_pos1 = node.ending_strings[i]
                    string_pos2 = node.ending_strings[j]
                    check_left_diverse_and_add(string_pos1, string_pos2, 0)
            for i in range(len(list(node.childs.keys()))):
                for j in range(i):
                    child1 = list(node.childs.keys())[i]
                    child2 = list(node.childs.keys())[j]

                    def get_all_pos(child):
                        return (
                            node.childs[child].string_positions
                            + node.childs[child].ending_strings
                        )
                    for string_pos1 in get_all_pos(child1):
                        for string_pos2 in get_all_pos(child2):
                            check_left_diverse_and_add(string_pos1, string_pos2, 1)
        for (code, child) in node.childs.items():
            best_match_substrings += self.get_best_max_substrings(
                threshold - code.max_covered_lines, child, initial_threshold
            )
        return best_match_substrings
