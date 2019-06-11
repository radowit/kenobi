from unittest import TestCase

from clonedigger.abstract_syntax_tree import SourceFile, AbstractSyntaxTree, StatementSequence, PairSequences


class SourceFileTests(TestCase):
    def test_null(self):
        assert True