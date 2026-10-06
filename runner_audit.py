import ast
import os

PROJECT = os.path.dirname(os.path.abspath(__file__))
RUNNER_PATH = os.path.join(PROJECT, "src", "network_tests", "runner.py")

with open(RUNNER_PATH, "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    print(f"{i:3d} | {line}", end="")
