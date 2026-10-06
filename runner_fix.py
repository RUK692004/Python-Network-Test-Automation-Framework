import ast

path = "src/network_tests/runner.py"
content = open(path).read()
try:
    ast.parse(content)
    print("SYNTAX OK")
    lines = content.split(chr(10))
    print("Total lines:", len(lines))
except SyntaxError as e:
    print("SYNTAX ERROR:", e)

import ast

path = r"d:/Projects/Python Network Test Automation Framework/src/network_tests/runner.py"
content = open(path).read()
try:
    ast.parse(content)
    print("SYNTAX OK")
    lines = content.split(chr(10))
    print("Total lines:", len(lines))
except SyntaxError as e:
    print("SYNTAX ERROR:", e)

import ast

path = "d:/Projects/Python Network Test Automation Framework/src/network_tests/runner.py"
content = open(path).read()
try:
    ast.parse(content)
    print("SYNTAX OK")
    lines = content.split(chr(10))
    print("Total lines:", len(lines))
except SyntaxError as e:
    print("SYNTAX ERROR:", e)
