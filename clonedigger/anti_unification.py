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
import copy

from six.moves import range

from .abstract_syntax_tree import FREE_VARIABLE_COST, AbstractSyntaxTree

# NOTE that everywhere is written Unifier instead of AntiUnifier, for simplicity

# Constants here
VERBOSE = True


class FreeVariable(AbstractSyntaxTree):
    free_variables_count = 1

    def __init__(self):
        FreeVariable.free_variables_count += 1
        name = "VAR(%d)" % (FreeVariable.free_variables_count,)
        #       self._childs = []
        AbstractSyntaxTree.__init__(self, name)


class Substitution(object):
    def __init__(self, initial_value=None):
        if initial_value is None:
            initial_value = {}
        self.map = initial_value

    def substitute(self, tree):
        if tree in list(self.map.keys()):
            return self.map[tree]
        else:
            if isinstance(tree, FreeVariable):
                return tree
            node = AbstractSyntaxTree(tree.name)
            for child in tree.children:
                node.add_child(self.substitute(child))
            return node

    def get_size(self):
        ret = 0
        for tree in self.map.values():
            ret += tree.get_size(False) - FREE_VARIABLE_COST
        return ret


class Unifier(object):
    def __init__(self, tree1, tree2, ignore_parametrization=False):
        def combine_subs(node, subs1, subs2):
            # subs1 and subs2 are 2-tuples
            assert list(subs1[0].map.keys()) == list(
                subs1[1].map.keys(),
            )
            assert list(subs2[0].map.keys()) == list(
                subs2[1].map.keys(),
            )

            def cmp_subs(sub0_key, sub1_key):
                return (
                    subs1[0].map[sub0_key] == subs2[0].map[sub1_key]
                    and subs1[1].map[sub0_key] == subs2[1].map[sub1_key]
                )
            newt = (copy.copy(subs2[0]), copy.copy(subs2[1]))
            relabel = {}
            for sub0_key in subs1[0].map.keys():
                if ignore_parametrization:
                    newt[0].map[sub0_key] = subs1[0].map[sub0_key]
                    newt[1].map[sub0_key] = subs1[1].map[sub0_key]
                    continue

                for sub1_key in subs2[0].map.keys():
                    if cmp_subs(sub0_key, sub1_key):
                        relabel[sub0_key] = sub1_key
                        break
                else:
                    newt[0].map[sub0_key] = subs1[0].map[sub0_key]
                    newt[1].map[sub0_key] = subs1[1].map[sub0_key]
            return (Substitution(relabel).substitute(node), newt)

        def unify(node1, node2):
            if node1 == node2:
                return (node1, (Substitution(), Substitution()))
            elif node1.name != node2.name or len(node1.children) != len(node2.children):
                var = FreeVariable()
                return (var, (Substitution({var: node1}), Substitution({var: node2})))

            substitutions = (Substitution(), Substitution())
            name = node1.name
            return_node = AbstractSyntaxTree(name)
            count = len(node1.children)
            for i in range(count):
                (node, subs) = unify(node1.children[i], node2.children[i])
                (node, substitutions) = combine_subs(node, subs, substitutions)
                return_node.add_child(node)
            return (return_node, substitutions)

        (self.unifier, self.substitutions) = unify(tree1, tree2)
        self.unifier.store_size()
        for i in (0, 1):
            for key in self.substitutions[i].map:
                self.substitutions[i].map[key].store_size()

    def get_size(self):
        return sum([s.get_size() for s in self.substitutions])


class Cluster(object):
    count = 0

    def __init__(self, tree=None):
        if tree:
            self._n = 1
            self.unifier_tree = tree
            self._trees = [tree]
            self.max_covered_lines = len(tree.covered_line_numbers)
        else:
            self._n = 0
            self._trees = []
            self.max_covered_lines = 0
        Cluster.count += 1

    def get_add_cost(self, tree):
        substitutions = Unifier(self.unifier_tree, tree).substitutions
        return (
            self._n
            * substitutions[0].get_size()
            + substitutions[1].get_size()
        )

    def unify(self, tree):
        self._n += 1
        self.unifier_tree = Unifier(self.unifier_tree, tree).unifier
        self._trees.append(tree)

    def add_without_unification(self, tree):
        self._n += 1
        self._trees.append(tree)
        if len(tree.covered_line_numbers) > self.max_covered_lines:
            self.max_covered_lines = len(tree.covered_line_numbers)
