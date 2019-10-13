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
from __future__ import print_function
import sys

from six.moves import range

from . import arguments
from .abstract_syntax_tree import StatementSequence, PairSequences
from .anti_unification import VERBOSE, Cluster, Unifier
from . import suffix_tree


def find_duplicate_code(source_files, report):
    statement_sequences = []
    statement_count = 0
    sequences_lengths = []
    for source_file in source_files:
        sequences = source_file.tree.get_all_statement_sequences()
        statement_sequences.extend(sequences)
        sequences_lengths.extend([len(s) for s in sequences])
        statement_count += sum([len(s) for s in sequences])

    if not sequences_lengths:
        print("Input is empty or the size of the input is below the size threshold")
        sys.exit(0)

    if VERBOSE:
        n_sequences = len(sequences_lengths)
        avg_seq_length = sum(sequences_lengths) / float(n_sequences)
        max_seq_length = max(sequences_lengths)

        print("%d sequences" % (n_sequences,))
        print("average sequence length: %f" % (avg_seq_length,))
        print("maximum sequence length: %d" % (max_seq_length,))
        sequences_without_restriction = statement_sequences
        sequences = []
        if not arguments.force:
            for sequence in sequences_without_restriction:
                if len(sequence) > 1000:
                    first_statement = sequence[0]
                    print(
                        (
                            "\n-----------------------------------------\n"
                            "Warning: sequences of statements, consists of %d elements "
                            "is too long.\n"
                            "It starts at %s:%d.\nIt will be ignored. "
                            "Use --force to override this restriction.\n"
                            "Please refer to "
                            "http://clonedigger.sourceforge.net/documentation.html\n"
                            "-----------------------------------------"
                        )
                        % (
                            len(sequence),
                            first_statement.source_file.file_name,
                            min(first_statement.covered_line_numbers),
                        )
                    )
                else:
                    sequences.append(sequence)

    def calc_statement_sizes():
        for sequence in statement_sequences:
            for statement in sequence:
                statement.store_size()

    def build_hash_to_statement(dcup_hash=True):
        hash_to_statement = {}
        for statement_sequence in statement_sequences:
            for statement in statement_sequence:
                if dcup_hash:
                    # 3 - CONSTANT HERE!
                    node_hash = statement.get_dcup_hash(arguments.hashing_depth)
                else:
                    node_hash = statement.get_full_hash()
                if node_hash not in hash_to_statement:
                    hash_to_statement[node_hash] = [statement]
                else:
                    hash_to_statement[node_hash].append(statement)
        return hash_to_statement

    def build_unifiers(hash_to_statement):
        processed_statements_count = 0
        clusters = []
        ret = {}
        for node_hash in hash_to_statement.keys():
            local_clusters = []
            statements = hash_to_statement[node_hash]
            for statement in statements:
                processed_statements_count += 1
                if VERBOSE and ((processed_statements_count % 1000) == 0):
                    print("%d," % (processed_statements_count,), end=" ")
                    sys.stdout.flush()
                bestcluster = None
                mincost = sys.maxsize
                for cluster in local_clusters:
                    cost = cluster.get_add_cost(statement)
                    if cost < mincost:
                        mincost = cost
                        bestcluster = cluster
                assert local_clusters == [] or bestcluster
                assert mincost >= 0
                if bestcluster is None or mincost > arguments.clustering_threshold:
                    newcluster = Cluster(statement)
                    local_clusters.append(newcluster)
                else:
                    bestcluster.unify(statement)
            ret[node_hash] = local_clusters
            clusters.extend(local_clusters)
        return ret

    def clusterize(hash_to_statement, clusters_map):
        processed_statements_count = 0
        # clusters_map contain hash values for statements, not unifiers
        # therefore it will work correct even if unifiers are smaller than
        # hashing depth value
        for node_hash in hash_to_statement.keys():
            clusters = clusters_map[node_hash]
            for statement in hash_to_statement[node_hash]:
                processed_statements_count += 1
                if VERBOSE and ((processed_statements_count % 1000) == 0):
                    print("%d," % (processed_statements_count,), end=" ")
                    sys.stdout.flush()
                mincost = sys.maxsize
                for cluster in clusters:
                    new_u = Unifier(cluster.unifier_tree, statement)
                    cost = new_u.get_size()
                    if cost < mincost:
                        mincost = cost
                        statement.mark = cluster
                        cluster.add_without_unification(statement)

    def filter_out_long_equally_labeled_sequences(statement_sequences):
        # TODO - refactor, combine with the previous warning
        sequences_without_restriction = statement_sequences
        statement_sequences = []
        for sequence in sequences_without_restriction:
            new_sequence = sequence.copy()
            current_mark = None
            length = 0
            first_statement_index = None
            flag = False
            for i in range(len(sequence)):
                statement = sequence[i]
                if statement.mark != current_mark:
                    if flag is True:
                        flag = False
                    current_mark = statement.mark
                    length = 0
                    first_statement_index = i
                else:
                    length += 1
                    if length > 10:
                        new_sequence[i] = None
                        if not flag:
                            for j in range(first_statement_index, i):
                                new_sequence[j] = None
                            first_statement = sequence[first_statement_index]
                            print(
                                (
                                    "\n-----------------------------------------\n"
                                    "Warning: sequence of statements starting "
                                    "at %s:%d\n"
                                    "consists of many similar statements.\n"
                                    "It will be ignored. Use --force to "
                                    "override this restriction.\n"
                                    "Please refer to "
                                    "http://clonedigger.sourceforge.net/"
                                    "documentation.html"
                                    "\n-----------------------------------------"
                                )
                                % (
                                    first_statement.source_file.file_name,
                                    min(first_statement.covered_line_numbers),
                                )
                            )
                            flag = True
            new_sequence = new_sequence + [None]
            cur_sequence = StatementSequence()
            for statement in new_sequence:
                if statement is None:
                    if cur_sequence:
                        statement_sequences.append(cur_sequence)
                        cur_sequence = StatementSequence()
                else:
                    cur_sequence.add_statement(statement)
        return statement_sequences

    def mark_using_hash(hash_to_statement):
        for node_hash in hash_to_statement:
            cluster = Cluster()
            for statement in hash_to_statement[node_hash]:
                cluster.add_without_unification(statement)
                statement.mark = cluster

    def find_huge_sequences():
        suffix_tree_instance = suffix_tree.SuffixTree()
        for sequence in statement_sequences:
            suffix_tree_instance.add(sequence)
        return [
            PairSequences([StatementSequence(s1), StatementSequence(s2)])
            for (s1, s2) in suffix_tree_instance.get_best_max_substrings(
                arguments.size_threshold
            )
        ]

    def refine_duplicates(pairs_sequences):
        duplicates = []
        flag = False
        while pairs_sequences:
            pair_sequences = pairs_sequences.pop()

            def all_pairsub_sequences_size_n_threshold(seq_length):
                sequence_pairs = []
                for first in range(0, pair_sequences.length - seq_length + 1):
                    new_pair_sequences = pair_sequences.sub_sequence(first, seq_length)
                    size = new_pair_sequences.get_max_covered_line_numbers_count()
                    if size >= arguments.size_threshold:
                        sequence_pairs.append((new_pair_sequences, first))
                return sequence_pairs

            seq_length = pair_sequences.length + 1
            while 1:
                seq_length -= 1
                if seq_length == 0:
                    break
                new_pairs_sequences = all_pairsub_sequences_size_n_threshold(seq_length)
                for (candidate_sequence, first) in new_pairs_sequences:
                    distance = candidate_sequence.calc_distance()
                    if distance < arguments.distance_threshold:
                        duplicates.append(candidate_sequence)
                        if first > 0:
                            pairs_sequences.append(
                                pair_sequences.sub_sequence(0, first - 1)
                            )
                        if first + seq_length < pair_sequences.length:
                            pairs_sequences.append(
                                pair_sequences.sub_sequence(
                                    first + seq_length,
                                    pair_sequences.length - first - seq_length
                                )
                            )
                        seq_length += 1
                        flag = True
                        break
                if flag:
                    flag = False
                    break
        return duplicates

    def remove_dominated_clones(clones):
        ret_clones = []
        #       def f_cmp(a, b):
        #           return a.getLevel().__cmp__(b.getLevel())
        #       clones.sort(f_cmp)
        statement_to_clone = {}
        for clone in clones:
            for sequence in clone:
                for statement in sequence:
                    if statement not in statement_to_clone:
                        statement_to_clone[statement] = []
                    statement_to_clone[statement].append(clone)
        for clone in clones:
            ancestors_2 = clone[1].ancestors
            flag = True
            for statement1 in clone[0].ancestors:
                if statement1 in statement_to_clone:
                    for clone2 in statement_to_clone[statement1]:
                        if statement1 in clone2[0]:
                            seq = clone2[1]
                        else:
                            assert statement1 in clone2[1]
                            seq = clone2[0]
                        for statement2 in seq:
                            if statement2 in ancestors_2:
                                flag = False
                                break
                        if not flag:
                            break
                if not flag:
                    break
            if flag:
                ret_clones.append(clone)
        return ret_clones

    if VERBOSE:
        print("Number of statements: ", statement_count)
        print("Calculating size for each statement...", end=" ")
        sys.stdout.flush()
    calc_statement_sizes()
    if VERBOSE:
        print("done")

    if VERBOSE:
        print("Building statement hash...", end=" ")
        sys.stdout.flush()
    report.start_timer("Building statement hash")
    if arguments.clusterize_using_hash:
        hash_to_statement = build_hash_to_statement(dcup_hash=False)
    else:
        hash_to_statement = build_hash_to_statement(dcup_hash=True)
    report.stop_timer()
    if VERBOSE:
        print("done")
        print("Number of different hash values: ", len(hash_to_statement))

    if arguments.clusterize_using_dcup or arguments.clusterize_using_hash:
        print("Marking each statement with its hash value")
        mark_using_hash(hash_to_statement)
    else:
        if VERBOSE:
            print("Building patterns...", end=" ")
            sys.stdout.flush()
        report.start_timer("Building patterns")
        clusters_map = build_unifiers(hash_to_statement)
        report.stop_timer()
        if VERBOSE:
            print(Cluster.count, "patterns were discovered")
            print("Choosing pattern for each statement...", end=" ")
            sys.stdout.flush()
        report.start_timer("Marking similar statements")
        clusterize(hash_to_statement, clusters_map)
        report.stop_timer()
        if VERBOSE:
            print("done")

    if arguments.report_unifiers:
        if VERBOSE:
            print("Building reverse hash for reporting ...", end=" ")
            sys.stdout.flush()
        reverse_hash = {}
        for sequence in statement_sequences:
            for statement in sequence:
                mark = statement.mark
                if mark not in reverse_hash:
                    reverse_hash[mark] = []
                reverse_hash[mark].append(statement)
        report.mark_to_statement_hash = reverse_hash
        if VERBOSE:
            print("done")

    if VERBOSE:
        print("Finding similar sequences of statements...", end=" ")
        sys.stdout.flush()

    if not arguments.force:
        statement_sequences = filter_out_long_equally_labeled_sequences(
            statement_sequences,
        )

    report.start_timer("Finding similar sequences of statements")
    duplicate_candidates = find_huge_sequences()
    report.stop_timer()
    if VERBOSE:
        print(len(duplicate_candidates), " sequences were found")
        print("Refining candidates...", end=" ")
        sys.stdout.flush()
    if arguments.distance_threshold != -1:
        report.start_timer("Refining candidates")
        clones = refine_duplicates(duplicate_candidates)
        report.stop_timer()
    else:
        clones = duplicate_candidates
    if VERBOSE:
        print(len(clones), "clones were found")
    if arguments.distance_threshold != -1:
        if VERBOSE:
            print("Removing dominated clones...", end=" ")
            sys.stdout.flush()
        old_clone_count = len(clones)
        clones = remove_dominated_clones(clones)
        if VERBOSE:
            print(len(clones) - old_clone_count, "clones were removed")

    covered_source_lines = set()
    for clone in clones:
        for sequence in clone:
            covered_source_lines = covered_source_lines.union(
                sequence.get_line_number_hashables()
            )
    source_lines = set()
    for sequence in statement_sequences:
        source_lines = source_lines.union(sequence.get_line_number_hashables())
    report.all_source_lines_count = len(source_lines)
    report.covered_source_lines_count = len(covered_source_lines)

    return clones
