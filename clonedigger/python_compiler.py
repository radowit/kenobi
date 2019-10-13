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

from __future__ import absolute_import
import compiler

from six.moves import range
from .logilab.astng import nodes

from .abstract_syntax_tree import AbstractSyntaxTree


class PythonNodeLeaf(object):
    def __init__(self, val):
        self.val = val

    def as_string(self):
        return str(self.val)

    def __str__(self):
        return self.as_string()


class PythonCompilerSourceFile(object):
    extension = "py"
    distance_threshold = 5
    size_threshold = 5
    ignored_statements = ["Import", "From"]

    def __init__(self, file_name, func_prefixes=()):
        def filter_func(line):
            for i in range(len(line) - 1, -1, -1):
                if not line[i].isspace():
                    return line[: i + 1]
            return line

        with open(file_name, "r") as source_file:
            self.source_lines = [filter_func(line) for line in source_file.readlines()]

        self.file_name = file_name
        self.tree = None
        self._func_prefixes = func_prefixes

        def rec_build_tree(compiler_ast_node, is_statement=False):
            def flatten(node_list):
                leaf = []
                for elt in node_list:
                    if isinstance(elt, (tuple, list)):
                        for elt2 in flatten(elt):
                            leaf.append(elt2)
                    else:
                        leaf.append(elt)
                return leaf

            def _build_tree(child, is_statement):
                tree = rec_build_tree(child, is_statement)
                if tree.name in self.ignored_statements:
                    # TODO move it up
                    return
                tree.parent = result_tree
                result_tree.add_child(tree)

            def add_childs(childs):
                assert isinstance(childs, list)
                for child in childs:
                    assert isinstance(child, compiler.ast.Node)
                    _build_tree(child, is_statement)

            def add_leaf_child(child, name):
                assert not isinstance(child, list)
                node, leaf = _add_child(child)
                setattr(result_tree.ast_node, name, leaf)
                return node

            def add_leaf_childs(childs, name):
                assert isinstance(childs, (list, tuple))
                node = getattr(result_tree.ast_node, name)
                for i in range(len(childs)):
                    node[i] = _add_child(childs[i])[1]

            def _add_child(child):
                assert not isinstance(child, compiler.ast.Node)
                tree = AbstractSyntaxTree(repr(child))
                tree.parent = result_tree
                leaf = PythonNodeLeaf(child)
                tree.ast_node = leaf
                result_tree.add_child(tree)
                return tree, leaf

            def add_leaf_string_childs(childs):
                assert isinstance(childs, list)
                for child in childs:
                    assert not isinstance(child, compiler.ast.Node)
                    tree = AbstractSyntaxTree(repr(child))
                    tree.parent = tree
                    result_tree.add_child(tree)

            if isinstance(compiler_ast_node, compiler.ast.Node):
                name = compiler_ast_node.__class__.__name__
                if name == "Function":
                    for prefix in self._func_prefixes:
                        if compiler_ast_node.name.startswith(prefix):
                            # skip function that matches pattern
                            return AbstractSyntaxTree("none")
                if name in ["Function", "Class"]:
                    # ignoring class and function docs
                    compiler_ast_node.doc = None
                if compiler_ast_node.lineno:
                    lines = [compiler_ast_node.lineno - 1]
                else:
                    lines = []
                result_tree = AbstractSyntaxTree(name, lines, self)
                result_tree.ast_node = compiler_ast_node
                if is_statement and compiler_ast_node.lineno:
                    result_tree.is_statement = True
                is_statement = name == "Stmt"
                if name == "AssAttr":
                    add_childs([compiler_ast_node.expr])
                    add_leaf_child(compiler_ast_node.attrname, "attrname")
                    add_leaf_string_childs([compiler_ast_node.flags])
                elif name == "AssName":
                    add_leaf_child(compiler_ast_node.name, "name")
                elif name == "AugAssign":
                    add_childs([compiler_ast_node.node])
                    add_leaf_child(compiler_ast_node.op, "op")
                    add_childs([compiler_ast_node.expr])
                elif name == "Class":
                    add_leaf_child(compiler_ast_node.name, "name")
                    add_childs(flatten(compiler_ast_node.bases))
                    add_childs([compiler_ast_node.code])
                elif name == "Compare":
                    add_childs([compiler_ast_node.expr])
                    for i in range(len(compiler_ast_node.ops)):
                        (operator, expr) = compiler_ast_node.ops[i]
                        tree = add_leaf_child(operator, "op")
                        add_childs([expr])
                        compiler_ast_node.ops[i] = (tree.ast_node, expr)
                elif name == "Const":
                    add_leaf_child(repr(compiler_ast_node.value), "value")
                elif name == "Function":
                    add_leaf_child(compiler_ast_node.name, "name")
                    add_leaf_childs(compiler_ast_node.argnames, "argnames")
                    if compiler_ast_node.defaults == ():
                        compiler_ast_node.defaults = []
                    # TODO incomment and fix
                    add_childs(compiler_ast_node.defaults)
                    add_leaf_string_childs([compiler_ast_node.flags])
                    add_childs([compiler_ast_node.code])
                elif name == "Getattr":
                    add_childs([compiler_ast_node.expr])
                    add_leaf_child(compiler_ast_node.attrname, "attrname")
                elif name == "Global":
                    add_leaf_childs(compiler_ast_node.names, "names")
                elif name == "Keyword":
                    add_leaf_child(compiler_ast_node.name, "name")
                    add_childs([compiler_ast_node.expr])
                elif name == "Lambda":
                    add_leaf_childs(compiler_ast_node.argnames, "argnames")
                    if compiler_ast_node.defaults == ():
                        compiler_ast_node.defaults = []
                    add_childs(compiler_ast_node.defaults)
                    add_childs([compiler_ast_node.code])
                elif name == "Name":
                    add_leaf_child(compiler_ast_node.name, "name")
                else:
                    for child in compiler_ast_node.getChildren():
                        _build_tree(child, is_statement)
                return result_tree
            else:
                return AbstractSyntaxTree(repr(compiler_ast_node))

        self.tree = rec_build_tree(compiler.parseFile(file_name))
