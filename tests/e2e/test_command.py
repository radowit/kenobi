import sys
from pytest import raises
from pytest import fixture
from clonedigger import arguments
import os
import subprocess
from subprocess import Popen
from os import chmod


def test_no_args():
    process = Popen(['clonedigger'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ''
    assert out == 'Input is empty or the size of the input is below the size threshold\n'



def test_no_duplicates():
    process = Popen(['clonedigger', 'tests/e2e/test_data/no_duplicates/code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/no_duplicates/code.py ... done
4 sequences
average sequence length: 4.500000
maximum sequence length: 7
Number of statements:  18
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  12
Building patterns... 14 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 1  sequences were found
Refining candidates... 0 clones were found
Removing dominated clones... 0 clones were removed
'''

    with open('output.html') as result_file:
        with open('tests/e2e/test_data/no_duplicates/output.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line


def test_duplicates():
    process = Popen(['clonedigger', 'tests/e2e/test_data/duplicate/code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/duplicate/code.py ... done
31 sequences
average sequence length: 4.387097
maximum sequence length: 12
Number of statements:  136
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  71
Building patterns... 88 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 1  sequences were found
Refining candidates... 1 clones were found
Removing dominated clones... 0 clones were removed
'''

    with open('output.html') as result_file:
        with open('tests/e2e/test_data/duplicate/output.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line


def test_duplicates_output():
    process = Popen(['clonedigger', '--output', 'newout.html', 'tests/e2e/test_data/duplicate/code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/duplicate/code.py ... done
31 sequences
average sequence length: 4.387097
maximum sequence length: 12
Number of statements:  136
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  71
Building patterns... 88 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 1  sequences were found
Refining candidates... 1 clones were found
Removing dominated clones... 0 clones were removed
'''

    with open('newout.html') as result_file:
        with open('tests/e2e/test_data/duplicate/output.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line


def test_duplicates_output_error():
    Popen(['touch', 'output.html'])
    chmod('output.html', 0)
    process = Popen(['clonedigger', 'tests/e2e/test_data/duplicate/code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == '''Traceback (most recent call last):
  File "/home/dreamwalker/.virtualenvs/kenobi/bin/clonedigger", line 11, in <module>
    load_entry_point(\'clonedigger\', \'console_scripts\', \'clonedigger\')()
  File "/home/dreamwalker/Repozytoria/kenobi/clonedigger/clonedigger.py", line 226, in main
    report.writeReport(output_file_name)
  File "/home/dreamwalker/Repozytoria/kenobi/clonedigger/html_report.py", line 444, in writeReport
    f = open(file_name, "w")
IOError: [Errno 13] Permission denied: \'output.html\'
'''
    assert out == '''Parsing  tests/e2e/test_data/duplicate/code.py ... done
31 sequences
average sequence length: 4.387097
maximum sequence length: 12
Number of statements:  136
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  71
Building patterns... 88 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 1  sequences were found
Refining candidates... 1 clones were found
Removing dominated clones... 0 clones were removed
catched error, removing output file
'''


def test_duplicate_functions():
    process = Popen(['clonedigger', 'tests/e2e/test_data/dup_functions/code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/dup_functions/code.py ... done
18 sequences
average sequence length: 4.000000
maximum sequence length: 10
Number of statements:  72
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  40
Building patterns... 48 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 4  sequences were found
Refining candidates... 4 clones were found
Removing dominated clones... -3 clones were removed
'''

    with open('output.html') as result_file:
        with open('tests/e2e/test_data/dup_functions/output.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line


def test_duplicate_functions_clusterize():
    process = Popen(['clonedigger', '--clusterize-using-dcup', 'tests/e2e/test_data/dup_functions/code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/dup_functions/code.py ... done
18 sequences
average sequence length: 4.000000
maximum sequence length: 10
Number of statements:  72
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  40
Marking each statement with its hash value
Finding similar sequences of statements... 20  sequences were found
Refining candidates... 4 clones were found
Removing dominated clones... -3 clones were removed
'''

    with open('output.html') as result_file:
        with open('tests/e2e/test_data/dup_functions/output_clusterized.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line


def test_duplicate_functions_small_distance_threshold():
    process = Popen(['clonedigger', '--distance-threshold',  '1', 'tests/e2e/test_data/dup_functions/code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/dup_functions/code.py ... done
18 sequences
average sequence length: 4.000000
maximum sequence length: 10
Number of statements:  72
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  40
Building patterns... 48 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 4  sequences were found
Refining candidates... 1 clones were found
Removing dominated clones... 0 clones were removed
'''

    with open('output.html') as result_file:
        with open('tests/e2e/test_data/dup_functions/output_small_threshold.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line


def test_duplicate_functions_big_size_threshold():
    process = Popen(['clonedigger', '--size-threshold',  '10', 'tests/e2e/test_data/dup_functions/code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/dup_functions/code.py ... done
9 sequences
average sequence length: 5.444444
maximum sequence length: 10
Number of statements:  49
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  33
Building patterns... 35 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 2  sequences were found
Refining candidates... 2 clones were found
Removing dominated clones... -1 clones were removed
'''

    with open('output.html') as result_file:
        with open('tests/e2e/test_data/dup_functions/output_big_threshold.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line


def test_duplicate_functions_with_func_pre():
    process = Popen(['clonedigger', '--func-prefixes=run', 'tests/e2e/test_data/dup_functions/code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/dup_functions/code.py ... done
15 sequences
average sequence length: 4.333333
maximum sequence length: 10
Number of statements:  65
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  40
Building patterns... 46 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 1  sequences were found
Refining candidates... 0 clones were found
Removing dominated clones... 0 clones were removed
'''

def test_duplicate_recursive():
    process = Popen(['clonedigger', 'tests/e2e/test_data/recursion'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/recursion/code.py ... done
Parsing  tests/e2e/test_data/recursion/dup_functions/code.py ... done
49 sequences
average sequence length: 4.244898
maximum sequence length: 12
Number of statements:  208
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  93
Building patterns... 122 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 5  sequences were found
Refining candidates... 5 clones were found
Removing dominated clones... -3 clones were removed
'''

    with open('output.html') as result_file:
        with open('tests/e2e/test_data/recursion/output.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line



def test_duplicate_functions_diff():
    process = Popen(['clonedigger', '--force-diff', 'tests/e2e/test_data/dup_functions/code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/dup_functions/code.py ... done
18 sequences
average sequence length: 4.000000
maximum sequence length: 10
Number of statements:  72
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  40
Building patterns... 48 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 4  sequences were found
Refining candidates... 4 clones were found
Removing dominated clones... -3 clones were removed
'''

    with open('output.html') as result_file:
        with open('tests/e2e/test_data/dup_functions/output_diff.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line


def test_no_recursion():
    process = Popen(['clonedigger', '--no-recursion', 'tests/e2e/test_data/recursion'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/recursion/code.py ... done
31 sequences
average sequence length: 4.387097
maximum sequence length: 12
Number of statements:  136
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  71
Building patterns... 88 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 1  sequences were found
Refining candidates... 1 clones were found
Removing dominated clones... 0 clones were removed
'''

    with open('output.html') as result_file:
        with open('tests/e2e/test_data/recursion/output_no_rec.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line


def test_duplicate_file_list():
    process = Popen(['clonedigger', '--file-list', 'tests/e2e/test_data/file_list.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/dup_functions/code.py ... done
Parsing  tests/e2e/test_data/no_duplicates/code.py ... done
Parsing  tests/e2e/test_data/duplicate/code.py ... done
53 sequences
average sequence length: 4.264151
maximum sequence length: 12
Number of statements:  226
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  100
Building patterns... 132 patterns were discovered
Choosing pattern for each statement... done
Finding similar sequences of statements... 14  sequences were found
Refining candidates... 5 clones were found
Removing dominated clones... -3 clones were removed
'''

    with open('output.html') as result_file:
        with open('tests/e2e/test_data/output.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line


def test_parse_error():
    process = Popen(['clonedigger', 'tests/e2e/test_data/output.html'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert out == '''Parsing  tests/e2e/test_data/output.html ... Error: can't parse "tests/e2e/test_data/output.html" 
: Traceback (most recent call last):
  File "/home/dreamwalker/Repozytoria/kenobi/clonedigger/clonedigger.py", line 180, in parse_file
    source_file = supplier(file_name, func_prefixes)
  File "/home/dreamwalker/Repozytoria/kenobi/clonedigger/python_compiler.py", line 181, in __init__
    self._setTree(rec_build_tree(compiler.parseFile(file_name)))
  File "/usr/lib64/python2.7/compiler/transformer.py", line 47, in parseFile
    return parse(src)
  File "/usr/lib64/python2.7/compiler/transformer.py", line 51, in parse
    return Transformer().parsesuite(buf)
  File "/usr/lib64/python2.7/compiler/transformer.py", line 128, in parsesuite
    return self.transform(parser.suite(text))
  File "<string>", line 2
    <HTML>
    ^
SyntaxError: invalid syntax

Input is empty or the size of the input is below the size threshold
'''


def test_big_file():
    process = Popen(['clonedigger', 'tests/e2e/test_data/big_file/code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    assert err == ""
    assert out == '''Parsing  tests/e2e/test_data/big_file/code.py ... done
1 sequences
average sequence length: 1024.000000
maximum sequence length: 1024

-----------------------------------------
Warning: sequences of statements, consists of 1024 elements is too long.
It starts at tests/e2e/test_data/big_file/code.py:0.
It will be ignored. Use --force to override this restriction.
Please refer to http://clonedigger.sourceforge.net/documentation.html
-----------------------------------------
Number of statements:  1024
Calculating size for each statement... done
Building statement hash... done
Number of different hash values:  1
Building patterns... 1000, 1 patterns were discovered
Choosing pattern for each statement... 1000, done
Finding similar sequences of statements... 
-----------------------------------------
Warning: sequence of statements starting at tests/e2e/test_data/big_file/code.py:0
consists of many similar statements.
It will be ignored. Use --force to override this restriction.
Please refer to http://clonedigger.sourceforge.net/documentation.html
-----------------------------------------
0  sequences were found
Refining candidates... 0 clones were found
Removing dominated clones... 0 clones were removed
'''

    with open('output.html') as result_file:
        with open('tests/e2e/test_data/big_file/output.html') as test_data_file:
            for result_line, data_line in zip(result_file.readlines(), test_data_file.readlines()):
                if not result_line.startswith(' Started at: ') and not data_line.startswith(' Finished at: ') and 'seconds<BR>' not in data_line and not data_line.startswith(' Total time:'):
                    assert result_line == data_line
