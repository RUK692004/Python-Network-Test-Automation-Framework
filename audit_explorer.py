import os

base = "d:/Projects/Python Network Test Automation Framework"

for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d not in [".git", ".venv", "__pycache__", ".pytest_cache"]]
    for f in files:
        if f.endswith((".py", ".md", ".txt", ".ini", ".sh", ".yaml", ".yml")):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, base)
            print(rel)
