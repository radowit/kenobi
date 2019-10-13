#    Copyright 2008 Peter Bulychev
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

from __future__ import absolute_import
from copy import copy
from six.moves import range

from . import arguments


FREE_VARIABLE_COST = 0.5


class AbstractSyntaxTree(object):
    def __init__(self, name=None, line_numbers=None, source_file=None):
        self.children = []
        self.line_numbers = line_numbers or []
        self.covered_line_numbers = set()
        self.parent = None
        self._hash = None
        self.source_file = source_file
        self.is_statement = False
        self._height = None
        self._size = None
        self._none_count = None
        if name is not None:
            self.name = name

    @property
    def ancestors(self):
        statements = []
        node = self.parent
        while node:
            if node.is_statement:
                statements.append(node)
            node = node.parent
        return statements

    def get_source_lines(self):
        source_line_numbers = set([])
        source_lines = []
        source_line_numbers = self.covered_line_numbers
        source_line_numbers_list = list(
            range(min(source_line_numbers), max(source_line_numbers) + 1)
        )
        source_line_numbers_list.sort()
        for source_line_number in source_line_numbers_list:
            source_lines.append(self.source_file.source_lines[source_line_number])
        return source_lines

    def propagate_covered_line_numbers(self):
        self.covered_line_numbers = set(self.line_numbers)
        for child in self.children:
            self.covered_line_numbers.update(child.propagate_covered_line_numbers())
        return self.covered_line_numbers

    def propagate_height(self):
        if not self.children:
            self._height = 0
        else:
            self._height = max([c.propagate_height() for c in self.children]) + 1
        return self._height

    def add_child(self, child, save_parent=False):
        if not save_parent:
            child.parent = self
        self.children.append(child)

    def __str__(self):
        return " ( {0}{1} ) ".format(
            self.name, " ".join([str(child) for child in self.children])
        )

    def get_full_hash(self):
        return self.get_dcup_hash(-1)

    def get_dcup_hash(self, level):
        if not self.children:
            ret = 0  # in case of names and constants
        else:
            ret = (level + 1) * hash(self.name) * len(self.children)
        # if level == -1, it will not stop until it reaches the leaves
        if level != 0:
            for i in range(len(self.children)):
                child = self.children[i]
                ret += (i + 1) * child.get_dcup_hash(level - 1)
        return hash(ret)

    def __hash__(self):
        if not self._hash:
            self._hash = hash(self.get_dcup_hash(3) + hash(self.name))
        return self._hash

    def __eq__(self, tree2):
        tree1 = self
        if tree2 is None:
            return False
        if tree1.name != tree2.name:
            return False
        if len(tree1.children) != len(tree2.children):
            return False
        for i in range(len(tree1.children)):
            if tree1.children[i] != tree2.children[i]:
                return False
        return True

    def get_all_statement_sequences(self):
        sequences = []
        current = StatementSequence()
        for child in self.children:
            if child.is_statement:
                current.add_statement(child)
            else:
                if not current.is_empty:
                    if len(current.covered_line_numbers) >= arguments.size_threshold:
                        sequences.append(current)
                        current = StatementSequence()
            sequences.extend(child.get_all_statement_sequences())
        if not current.is_empty:
            if len(current.covered_line_numbers) >= arguments.size_threshold:
                sequences.append(current)
        return sequences

    def store_size(self):
        observed = set()
        self._none_count = 0

        def rec_calc_size(node):
            size = 0
            if node not in observed:
                if node.children:
                    for child in node.children:
                        size += rec_calc_size(child)
                else:
                    observed.add(node)
                    if node.name == "None":
                        self._none_count += 1
                    if node.__class__.__name__ == "FreeVariable":
                        size += FREE_VARIABLE_COST
                    else:
                        size += 1
            return size

        if self._size is None:
            self._size = rec_calc_size(self)

    def get_size(self, ignore_none=True):
        ret = self._size
        if ignore_none:
            ret -= self._none_count
        return ret


class StatementSequence(object):
    def __init__(self, sequence=None):
        self._sequence = []
        self.source_file = None
        for statement in sequence or []:
            self.add_statement(statement)

    @property
    def covered_line_numbers(self):
        line_numbers = set()
        for statement in self:
            line_numbers.update(statement.covered_line_numbers)
        return line_numbers

    @property
    def ancestors(self):
        return self[0].ancestors

    @property
    def is_empty(self):
        return len(self._sequence) == 0

    def add_statement(self, statement):
        self._sequence.append(statement)
        if self.source_file is None:
            self.source_file = statement.source_file
        else:
            assert self.source_file == statement.source_file

    def __getitem__(self, *args):
        return self._sequence.__getitem__(*args)

    def __len__(self):
        return self._sequence.__len__()

    def __str__(self):
        return ",".join([str(s) for s in self])

    def get_source_lines(self):
        source_lines = []
        for statement in self:
            source_lines.extend(statement.get_source_lines())
        return source_lines

    @property
    def line_numbers(self):
        numbers = []
        for statement in self:
            numbers.extend(statement.line_numbers)
        return numbers

    def get_line_number_hashables(self):
        source_file_name = self.source_file.file_name
        line_numbers = self.covered_line_numbers
        return set([(source_file_name, line_number) for line_number in line_numbers])

    def construct_tree(self):
        tree = AbstractSyntaxTree("__SEQUENCE__")
        for statement in self:
            tree.add_child(statement, True)
        return tree

    @property
    def length(self):
        return len(self)

    def covered_line_numbers_count(self):
        covered = set()
        for node in self:
            covered.update(node.covered_line_numbers)
        return len(covered)

    def copy(self):
        return copy(self._sequence)


class PairSequences(object):
    def __init__(self, sequences):
        self._sequences = sequences

    def __getitem__(self, *args):
        return self._sequences.__getitem__(*args)

    def __str__(self):
        return ";\t".join([str(s) for s in self])

    def calc_distance(self):
        from . import anti_unification

        trees = [s.construct_tree() for s in self]
        unifier = anti_unification.Unifier(trees[0], trees[1])
        return unifier.get_size()

    def sub_sequence(self, first, length):
        return PairSequences(
            [
                StatementSequence(self[0][first : first + length]),
                StatementSequence(self[1][first : first + length]),
            ]
        )

    @property
    def length(self):
        return self[0].length

    def get_max_covered_line_numbers_count(self):
        return min([s.covered_line_numbers_count() for s in self])
