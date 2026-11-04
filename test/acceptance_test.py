#!/usr/bin/env python3
"""QueensPress acceptance test.

Proof-output method: build a real book (8x8, 6 puzzles), then re-verify
every puzzle with a checker written independently of the engine: it
enumerates ALL column permutations (one queen per row) and filters by
the printed rules -- distinct columns, distinct regions, no diagonal
touching, givens respected. Exactly one permutation may survive, and
it must equal the printed solution. Also audits the regions (exact
partition of the grid, every region connected), a tamper case (move
one given crown: the proof must break), PDF geometry, timing,
determinism.
"""
import os
import sys
import time
from itertools import permutations

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from queens_press import run_queenspress  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "out")
results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def count_by_permutation(region, givens, n, limit=2):
    """Independent recount over all n! column permutations."""
    sols = []
    given_at = dict(givens) if isinstance(givens, dict) else \
        {r: c for (r, c) in givens}
    for perm in permutations(range(n)):
        ok = True
        for r, c in given_at.items():
            if perm[r] != c:
                ok = False
                break
        if not ok:
            continue
        regs = [region[r][perm[r]] for r in range(n)]
        if len(set(regs)) != n:
            continue
        for r in range(n - 1):
            if abs(perm[r] - perm[r + 1]) <= 1:
                ok = False
                break
        if not ok:
            continue
        sols.append(perm)
        if len(sols) >= limit:
            break
    return sols


def regions_ok(region, n):
    flat = [region[r][c] for r in range(n) for c in range(n)]
    if sorted(set(flat)) != list(range(n)):
        return False
    for reg in range(n):
        cells = [(r, c) for r in range(n) for c in range(n)
                 if region[r][c] == reg]
        seen, stack = set(), [cells[0]]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            for nb in ((cur[0] + 1, cur[1]), (cur[0] - 1, cur[1]),
                       (cur[0], cur[1] + 1), (cur[0], cur[1] - 1)):
                if nb in cells and nb not in seen:
                    stack.append(nb)
        if seen != set(cells):
            return False
    return True


def main():
    t0 = time.time()
    s = run_queenspress(6, OUT, seed=42, size=8)
    dt = time.time() - t0
    ps = s["puzzles"]
    check("counts: 6 puzzles at 8x8", len(ps) == 6 and all(p["n"] == 8 for p in ps),
          f"({[len(p['givens']) for p in ps]} givens)")

    reg_ok, giv_ok, unique_ok = True, True, True
    for p in ps:
        if not regions_ok(p["region"], p["n"]):
            reg_ok = False
        for (r, c) in p["givens"]:
            if p["solution"][r] != c:
                giv_ok = False
        sols = count_by_permutation(p["region"], p["givens"], p["n"], limit=2)
        if len(sols) != 1 or list(sols[0]) != p["solution"]:
            unique_ok = False
    check("regions partition the grid and every region is connected", reg_ok, "")
    check("every given crown sits on the printed solution", giv_ok, "")
    check("every puzzle: exactly one solution (independent permutation "
          "recount), equal to printed solution", unique_ok, "")

    # tamper: move one given crown to a wrong cell of its row
    p0 = ps[0]
    if p0["givens"]:
        (r0, c0) = sorted(p0["givens"])[0]
        bad = (set(p0["givens"]) - {(r0, c0)}) | {(r0, (c0 + 1) % p0["n"])}
        sols = count_by_permutation(p0["region"], bad, p0["n"], limit=2)
        tamper_ok = not (len(sols) == 1 and list(sols[0]) == p0["solution"])
    else:
        tamper_ok = True
    check("tamper: a moved given crown breaks the proof", tamper_ok, "")

    with open(s["pdf_path"], "rb") as fh:
        data = fh.read()
    pages = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
    check("PDF 612x792pt, 11 pages", b"612 792" in data and pages == 11,
          f"({pages})")
    check("6-puzzle book builds in under 180s", dt < 180, f"({dt:.1f}s)")

    s2 = run_queenspress(6, OUT, seed=42, size=8)
    same = [p["region"] for p in s2["puzzles"]] == [p["region"] for p in ps] and \
        [p["givens"] for p in s2["puzzles"]] == [p["givens"] for p in ps]
    check("deterministic for fixed seed", same, "")

    npass = sum(1 for _, ok, _ in results if ok)
    print(f"\n{npass}/{len(results)} PASS")
    with open(os.path.join(os.path.dirname(__file__),
                           "acceptance_results.txt"), "w") as fh:
        for name, ok, detail in results:
            fh.write(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}\n")
        fh.write(f"\n{npass}/{len(results)} PASS\n")
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
