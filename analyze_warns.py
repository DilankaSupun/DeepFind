import re
from collections import Counter

warn_file = r"d:\External Works\Portfolio\FileMind\DeepFind\engine\build\deepfind-engine\warn-deepfind-engine.txt"

unresolved = []
ignored = []
dlls = []

with open(warn_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "missing module named" in line:
            mod = line.split("missing module named ")[1].split(" -")[0]
            if not mod.startswith("torch") and not mod.startswith("scipy") and not mod.startswith("numpy"):
                unresolved.append(mod)
        elif "libgomp" in line or "dll" in line.lower():
            dlls.append(line)

print("Top 10 Unresolved Modules (ignoring torch/scipy/numpy):")
print(Counter(unresolved).most_common(10))
print("\nSuspicious DLL warnings:")
for d in dlls:
    print(d)

