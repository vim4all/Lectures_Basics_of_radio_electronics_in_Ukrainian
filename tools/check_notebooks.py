"""Check the lecture notebooks.

1. Every internal link ``[..](#anchor)`` points to an existing ``<a class="anchor" id="anchor">``
   and no anchor id is used twice.
2. (unless --no-exec) every notebook executes top to bottom without errors.

Usage:
    python tools/check_notebooks.py            # links + execution
    python tools/check_notebooks.py --no-exec  # links only (fast)
    python tools/check_notebooks.py --inplace  # also save executed outputs into the notebooks
"""
import argparse
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = sorted(glob.glob(str(ROOT / "Основи радіотехніки_*_частина.ipynb")))


def check_links(path):
    nb = json.load(open(path, encoding="utf-8"))
    text = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
    anchors = re.findall(r'<a class="anchor" id="([^"]+)"', text)
    links = set(re.findall(r"\]\(#([^)]+)\)", text))
    problems = [f"broken link #{l}" for l in sorted(links - set(anchors))]
    problems += [f"duplicate anchor #{a}" for a in sorted({a for a in anchors if anchors.count(a) > 1})]
    return problems


def execute(path, inplace):
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError

    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=600, kernel_name="python3",
                            resources={"metadata": {"path": str(ROOT)}}, store_widget_state=True)
    try:
        client.execute()
    except CellExecutionError as e:
        return [str(e).splitlines()[-1] if str(e) else "cell execution error"]
    if inplace:
        nbformat.write(nb, path)
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-exec", action="store_true")
    ap.add_argument("--inplace", action="store_true")
    args = ap.parse_args()

    failed = False
    for path in NOTEBOOKS:
        name = Path(path).name
        problems = check_links(path)
        if not args.no_exec:
            problems += execute(path, args.inplace)
        for p in problems:
            print(f"FAIL {name}: {p}")
        if problems:
            failed = True
        else:
            print(f"OK   {name}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
