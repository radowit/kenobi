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
import difflib
import re
import sys
import time
import traceback
from cgi import escape

from six.moves import range

from . import anti_unification
from . import arguments
from .abstract_syntax_tree import AbstractSyntaxTree


class Report(object):
    def __init__(self):
        self._error_info = []
        self._clones = []
        self.timers = []
        self._file_names = []

    def add_file_name(self, file_name):
        self._file_names.append(file_name)

    def add_error_information(self, error_info):
        self._error_info.append(error_info)

    def add_clone(self, clone):
        self._clones.append(clone)

    def sort_by_clone_size(self):
        self._clones.sort(lambda a, b: cmp(
            b.get_max_covered_line_numbers_count(),
            a.get_max_covered_line_numbers_count(),
        ))

    def start_timer(self, descr):
        self.timers.append([descr, time.time(), time.ctime()])
        sys.stdout.flush()

    def stop_timer(self):
        self.timers[-1][1] = time.time() - self.timers[-1][1]

    def get_total_time(self):
        return sum([i[1] for i in self.timers])


class HTMLReport(Report):
    def __init__(self):
        Report.__init__(self)
        self.mark_to_statement_hash = {}
        self.all_source_lines_count = None
        self.covered_source_lines_count = None

    def write_report(self, file_name):
        # TODO REWRITE! This function code was created in a hurry
        eclipse_start = "\n<!--ECLIPSE START-->"
        eclipse_end = "\n<!--ECLIPSE END-->"

        def format_line_code(line):
            line = line.replace("\t", " ")
            line = line.replace(" ", "&nbsp; ")
            return '<span style="font-family: monospace;">%s</span>' % (line,)

        errors_info = "\n".join(
            [
                "<P> <FONT COLOR=RED> %s </FONT> </P>"
                % (error_info.replace("\n", "<BR>"),)
                for error_info in self._error_info
            ]
        )

        very_strange_const = "VERY_STRANGE_CONST"

        clone_descriptions = []
        for clone_i in range(len(self._clones)):
            try:
                clone = self._clones[clone_i]
                output_string = "<P>"
                output_string += "<B>Clone # %d</B><BR>" % (clone_i + 1,)
                output_string += "Distance between two fragments = %d <BR>" % (
                    clone.calc_distance(),
                )
                output_string += "Clone size = " + str(
                    max([len(set(clone[i].covered_line_numbers)) for i in [0, 1]])
                )
                output_string += "<TABLE NOWRAP WIDTH=100% BORDER=1>"
                output_string += eclipse_start
                output_string += "<TR>"
                for j in [0, 1]:
                    output_string += (
                        '<TD> <a href="clone://%s?%d&%d"> Go to this fragment in '
                        "Eclipse </a> </TD>"
                    ) % (
                        clone[j].source_file.file_name,
                        min(clone[j][0].covered_line_numbers),
                        max(clone[j][-1].covered_line_numbers),
                    )
                    if j == 0:
                        output_string += "<TD></TD>"
                output_string += "</TR>"
                output_string += eclipse_end
                for j in [0, 1]:
                    output_string += "<TD>"
                    output_string += 'Source file "%s"<BR>' % (
                        clone[j].source_file.file_name,
                    )
                    if clone[j][0].covered_line_numbers == []:
                        raise SystemExit()
                    output_string += "The first line is %d" % (
                        min(clone[j][0].covered_line_numbers) + 1,
                    )
                    output_string += "</TD>"
                    if j == 0:
                        output_string += "<TD></TD>"
                output_string += "</TR>"
                for i in range(clone[0].length):
                    output_string += "<TR>\n"
                    output = []
                    statements = [clone[j][i] for j in [0, 1]]

                    def diff_highlight(seqs):
                        sequence_matcher = difflib.SequenceMatcher(
                            lambda x: x == "<BR>\n"
                        )
                        sequence_matcher.set_seqs(seqs[0], seqs[1])
                        blocks = sequence_matcher.get_matching_blocks()
                        if not ((blocks[0][0] == 0) and (blocks[0][1] == 0)):
                            blocks = [(0, 0, 0)] + blocks
                        diff = ["", ""]
                        for k in range(len(blocks)):
                            block = blocks[k]
                            for j in [0, 1]:
                                diff[j] += escape(
                                    seqs[j][block[j] : block[j] + block[2]]
                                )
                            if k < (len(blocks) - 1):
                                nextblock = blocks[k + 1]
                                for j in [0, 1]:
                                    diff[j] += (
                                        '<span%sstyle="color:rgb(255,0,0);">%s</span>'
                                    ) % (
                                        very_strange_const,
                                        escape(
                                            seqs[j][block[j] + block[2] : nextblock[j]]
                                        ),
                                    )
                        return diff

                    # preparation of indentation
                    indentations = (set(), set())
                    for j in (0, 1):
                        for source_line in statements[j].get_source_lines():
                            indentations[j].add(
                                re.findall(r"^\s*", source_line)[0].replace(
                                    "\t", 4 * " "
                                )
                            )
                    indentations = (list(indentations[0]), list(indentations[1]))
                    indentations[0].sort()
                    indentations[1].sort()
                    source_lines = ([], [])

                    def use_diff(statements, indentations, source_lines):
                        for j in (0, 1):
                            for source_line in statements[j].get_source_lines():
                                indent1 = re.findall(r"^\s*", source_line)[0]
                                indent2 = indent1.replace("\t", 4 * " ")
                                source_line = re.sub(
                                    "^" + indent1,
                                    indentations[j].index(indent2) * " ",
                                    source_line,
                                )
                                source_lines[j].append(source_line)
                        diff = diff_highlight(
                            [("\n".join(source_lines[j])) for j in [0, 1]]
                        )
                        diff = [
                            format_line_code(diff[i].replace("\n", "<BR>\n"))
                            for i in [0, 1]
                        ]
                        diff = [
                            diff[i].replace(very_strange_const, " ") for i in (0, 1)
                        ]
                        unifier = anti_unification.Unifier(statements[0], statements[1])
                        return diff, unifier

                    if arguments.use_diff:
                        (diff, unifier) = use_diff(
                            statements,
                            indentations,
                            source_lines,
                        )
                    else:
                        try:

                            def rec_correct_as_string(node1, node2, stmt1, stmt2):
                                def highlight(new_string):
                                    return (
                                        '<span style="color: rgb(255, 0, 0);">'
                                        '%s</span>'
                                    ) % (new_string,)

                                class NewAsString(object):
                                    def __init__(self, new_string):
                                        self.new_string = highlight(new_string)

                                    def __call__(self):
                                        return self.new_string

                                def set_as_string_node_parent(node):
                                    if not isinstance(node, AbstractSyntaxTree):
                                        node = node.parent
                                    node_string = NewAsString(node.ast_node.as_string())
                                    node.ast_node.as_string = node_string

                                if (node1 in stmt1) or (node2 in stmt2):
                                    for node in (node1, node2):
                                        set_as_string_node_parent(node)
                                    return
                                assert len(node1.children) == len(node2.children)
                                for k in range(len(node1.children)):
                                    child1 = node1.children[k]
                                    chidl2 = node2.children[k]
                                    rec_correct_as_string(child1, chidl2, stmt1, stmt2)

                            (stmt1, stmt2) = (statements[0], statements[1])
                            unifier = anti_unification.Unifier(stmt1, stmt2)
                            rec_correct_as_string(
                                stmt1,
                                stmt2,
                                list(unifier.substitutions[0].map.values()),
                                list(unifier.substitutions[1].map.values()),
                            )
                            diff = [None, None]
                            for j in (0, 1):
                                diff[j] = statements[j].ast_node.as_string()

                                lines = diff[j].split("\n")
                                for ii in range(len(lines)):
                                    temp_line = ""
                                    jj = 0
                                    try:
                                        while lines[ii][jj] == " ":
                                            temp_line += "&nbsp;"
                                            jj += 1
                                    except IndexError:
                                        # suppress errors if line has no leading spaces
                                        pass
                                    temp_line += lines[ii][jj:]
                                    lines[ii] = temp_line
                                diff[j] = "\n".join(lines)

                                diff[j] = diff[j].replace("\n", "<BR>\n")

                        except Exception:
                            print(
                                "The following error occured during highlighting "
                                "of differences on the AST level:"
                            )
                            traceback.print_exc()
                            print("using diff highlight")
                            (diff, unifier) = use_diff(
                                statements,
                                indentations,
                                source_lines,
                            )
                    for j in [0, 1]:
                        output.append("<TD>\n" + diff[j] + "</TD>\n")
                    if unifier.get_size() > 0:
                        color = "RED"
                    else:
                        color = "AQUA"
                    output_string += (
                        '%s<TD style="width: 10px;" BGCOLOR=%s> </TD>%s'
                    ) % (
                        output[0],
                        color,
                        output[1],
                    )
                    output_string += "</TR>\n"
                output_string += "</TABLE> </P> <HR>"
                clone_descriptions.append(output_string)
            except Exception:
                print("Clone info can't be written to the report. ")
                traceback.print_exc()

        descr = """<P>Source files: %d</P>
        <a href = "javascript:unhide('files');">Click here to show/hide file names</a>
        <div id="files" class="hidden"><P><B>Source files:</B><BR>%s</P></div>
        <P>Clones detected: %d</P>
        <P>%d of %d lines are duplicates (%.2f%%) </P>
<P>
<B>Parameters<BR> </B>
clustering_threshold = %d<BR>
distance_threshold = %d<BR>
size_threshold = %d<BR>
hashing_depth = %d<BR>
clusterize_using_hash = %s<BR>
clusterize_using_dcup = %s<BR>
</P>
        """ % (
            len(self._file_names),
            ", <BR>".join(self._file_names),
            len(self._clones),
            self.covered_source_lines_count,
            self.all_source_lines_count,
            100
            if not self.all_source_lines_count
            else (
                100
                * self.covered_source_lines_count
                / float(self.all_source_lines_count)
            ),
            arguments.clustering_threshold,
            arguments.distance_threshold,
            arguments.size_threshold,
            arguments.hashing_depth,
            str(arguments.clusterize_using_hash),
            str(arguments.clusterize_using_dcup),
        )
        if arguments.print_time:
            timings = ""
            timings += "<B>Time elapsed</B><BR>"
            timings += "<BR>\n".join(
                ["%s : %.2f seconds" % (i[0], i[1]) for i in self.timers]
            )
            timings += "<BR>\n Total time: %.2f" % (self.get_total_time())
            timings += "<BR>\n Started at: " + self.timers[0][2]
            timings += "<BR>\n Finished at: " + self.timers[-1][2]
        else:
            timings = ""

        marks_report = ""
        if self.mark_to_statement_hash:
            marks_report += "<P>Top 20 statement marks:"
            marks = list(self.mark_to_statement_hash.keys())
            marks.sort(
                lambda y, x: cmp(
                    len(self.mark_to_statement_hash[x]),
                    len(self.mark_to_statement_hash[y]),
                )
            )
            counter = 0
            for mark in marks[:20]:
                counter += 1
                marks_report += (
                    "<BR>%s:%s<a href=\"javascript:unhide('stmt%d');\">"
                    "show/hide representatives</a> "
                ) % (
                    str(len(self.mark_to_statement_hash[mark])),
                    str(mark.unifier_tree),
                    counter,
                )
                marks_report += '<div id="stmt%d" class="hidden"> <BR>' % (counter,)
                for statement in self.mark_to_statement_hash[mark]:
                    marks_report += str(statement) + "<BR>"
                marks_report += "</div>"
                marks_report += "</P>"

        warnings = ""
        if arguments.use_diff:
            warnings += (
                "<P>(*) Warning: the highlighting of differences is based on diff "
                "and doesn't reflect the tree-based clone detection algorithm.</P>"
            )
        save_to = '%s<b><a href="file://%s">Save this report</a></b>%s' % (
            eclipse_start,
            file_name,
            eclipse_end,
        )
        html_code = (
            """
<HTML>
    <HEAD>
        <TITLE> CloneDigger Report </TITLE>
        <script type="text/javascript">
        function unhide(divID) {
            var item = document.getElementById(divID);
            if (item) {
                item.className=(item.className=='hidden')?'unhidden':'hidden';
            }
        }
</script>

<style type="text/css">
.hidden { display: none; }
.unhidden { display: block; }
.preformatted {
        border: 1px dashed #3c78b5;
    font-size: 11px;
        font-family: Courier;
    margin: 10px;
        line-height: 13px;
}
.preformattedHeader {
    background-color: #f0f0f0;
        border-bottom: 1px dashed #3c78b5;
    padding: 3px;
        text-align: center;
}
.preformattedContent {
    background-color: #f0f0f0;
    padding: 3px;
}
<!--
<div class="preformatted"><div class="preformattedContent">
<pre>Clone Digger
</pre>
</div></div>
-->

</style>

    </HEAD>
    <BODY>
    %s
    %s
    %s
    %s
    %s
    %s
    %s
    <HR>
    Clone Digger is aimed to find software clones in Python and Java programs.
    It is provided under the GPL license and can be downloaded from the site
    <a href="http://clonedigger.sourceforge.net">http://clonedigger.sourceforge.net</a>
    </BODY>
</HTML>"""
        ) % (
            errors_info,
            save_to,
            descr,
            timings,
            "<BR>\n".join(clone_descriptions),
            marks_report,
            warnings,
        )
        with open(file_name, "w") as report_file:
            report_file.write(
                re.sub(eclipse_start + ".*?" + eclipse_end, "", html_code),
            )
