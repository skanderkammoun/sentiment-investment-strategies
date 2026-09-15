"""Inspection: python nbshow.py <nb> [--grep MOTIF] [--cell N] [--list]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nbtools import charger, src

NBDIR = r"C:\Users\semy4\OneDrive\Bureau\Fintech_project\src\notebooks\notebooks"

def path(nom):
    return nom if os.path.sep in nom else os.path.join(NBDIR, nom)

def main():
    nb = charger(path(sys.argv[1]))
    args = sys.argv[2:]
    if "--list" in args:
        for i, c in enumerate(nb["cells"]):
            s = src(c).strip().replace("\n", " | ")[:110]
            print(f"[{i:3d}] {c['cell_type'][:4]} {s}")
        return
    if "--cell" in args:
        for n in args[args.index("--cell") + 1].split(","):
            i = int(n)
            print(f"===== CELL {i} ({nb['cells'][i]['cell_type']}) =====")
            print(src(nb["cells"][i]))
        return
    if "--grep" in args:
        motif = args[args.index("--grep") + 1]
        for i, c in enumerate(nb["cells"]):
            s = src(c)
            if motif in s:
                for ln, line in enumerate(s.split("\n")):
                    if motif in line:
                        print(f"[{i:3d}] {c['cell_type'][:4]} L{ln}: {line.strip()[:150]}")
        return

main()
