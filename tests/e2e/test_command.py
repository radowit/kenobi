import sys
from pytest import raises
from pytest import fixture
from clonedigger import arguments
import os
import subprocess
from subprocess import Popen


def test_no_args():
    process = Popen(['clonedigger'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

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
    
