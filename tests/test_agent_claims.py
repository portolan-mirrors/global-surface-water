#!/usr/bin/env python3
"""Run every query in the published agent guides and check its stated result.

Each ```sql and ```bash fence in catalog/**/AGENTS.md runs against the
published objects at data.source.coop. The comment lines in a fence state
the result: `-- ...` in SQL, `# ...` in bash. Every number in those comments
must occur in the fence's output, unless the number also occurs in the code
itself (a year in a URL, for example). So an edited number, a changed file,
or a broken URL fails the gate.

Needs: duckdb (CLI) and GDAL command-line tools on PATH.

Run: python3 tests/test_agent_claims.py

Before publishing, GUIDE_BASE=$PWD/catalog runs the same fences against the
local catalog: the public base URL is replaced by that path and the
/vsicurl/ prefix is dropped.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"
PUBLIC = "https://data.source.coop/portolan-mirrors/global-surface-water"
LOCAL = os.environ.get("GUIDE_BASE")

FENCE = re.compile(r"^```(sql|bash)\n(.*?)^```\s*$", re.M | re.S)
NUMBER = re.compile(r"[-−]?\d[\d,]*(?:\.\d+)?")


def numbers(text: str) -> set[str]:
    """Numbers in text, normalized: no thousands commas, ASCII minus, no .0.

    Output is CSV, so the caller replaces its commas with spaces first.
    """
    out = set()
    for raw in NUMBER.findall(text):
        n = raw.replace(",", "").replace("−", "-")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        if n == "-0":
            n = "0"
        out.add(n)
        out.add(n.lstrip("-"))  # a signed claim may print as a column of a subtraction
    return out


def split(lang: str, body: str) -> tuple[str, str]:
    """Separate a fence into code and the comment lines that state its result."""
    mark = "--" if lang == "sql" else "#"
    code, claims = [], []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(mark) and not stripped.startswith("#!"):
            claims.append(stripped[len(mark):])
        else:
            code.append(line)
    return "\n".join(code), "\n".join(claims)


def run(lang: str, code: str, cwd: str) -> subprocess.CompletedProcess:
    if LOCAL:
        code = code.replace("/vsicurl/" + PUBLIC, LOCAL).replace(PUBLIC, LOCAL)
    if lang == "sql":
        return subprocess.run(["duckdb", "-csv", "-c", code], capture_output=True, text=True,
                              cwd=cwd, timeout=900)
    return subprocess.run(["bash", "-eo", "pipefail", "-c", code], capture_output=True,
                          text=True, cwd=cwd, timeout=900)


def main() -> int:
    failures, ran = [], 0
    for guide in sorted(CATALOG.rglob("AGENTS.md")):
        rel = guide.relative_to(ROOT)
        for match in FENCE.finditer(guide.read_text()):
            lang, body = match.groups()
            code, claims = split(lang, body)
            line = guide.read_text()[: match.start()].count("\n") + 1
            with tempfile.TemporaryDirectory() as tmp:
                result = run(lang, code, tmp)
            ran += 1
            where = f"{rel}:{line}"
            if result.returncode != 0:
                failures.append(f"{where}: exit {result.returncode}\n{result.stderr.strip()[-800:]}")
                continue
            missing = sorted(numbers(claims) - numbers(code) - numbers(result.stdout.replace(",", " ")))
            if missing:
                failures.append(f"{where}: stated numbers not in the output: {missing}\n"
                                f"output:\n{result.stdout.strip()[:800]}")
            else:
                print(f"ok   {where}")
    for f in failures:
        print(f"FAIL {f}")
    print(f"\n{ran} fences run, {len(failures)} failed")
    return 1 if failures or ran == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
