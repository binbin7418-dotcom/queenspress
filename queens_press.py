#!/usr/bin/env python3
"""QueensPress engine: LinkedIn-style Queens puzzle books (PDF) where
every puzzle is PROVEN to have exactly one solution.

A Queens puzzle is an NxN grid divided into N colored regions. Place
exactly one queen in every row, every column and every region, so that
no two queens touch -- not even diagonally.

How a puzzle is made: a valid queen placement is generated first, then
regions are grown around the queens (frontier growth, so every region
is one connected piece). Queens are then turned into printed "given"
crowns one at a time; a given is only removed if an independent
counting solver proves the puzzle still has exactly one solution.
Deterministic for a fixed seed. 100% local. Requires: reportlab.

Usage:
    python queens_press.py out/ [--puzzles 12] [--size 8] [--seed 42]
"""
import os
import random
import sys

PAGE_W, PAGE_H = 612, 792
PALETTE = ["#f6c6c6", "#f9e2ae", "#cdeac0", "#bde0fe", "#ffc8dd",
           "#d5c6f0", "#b8f1cc", "#ffd6a5", "#a0c4ff"]

# ------------------------------------------------------------- combinatorics

def gen_placement(rng, n):
    """One queen per row/col/region-slot with no touching (incl. diag)."""
    cols = [-1] * n

    def ok(r, c):
        for rr in range(r):
            cc = cols[rr]
            if cc == c or abs(cc - c) == r - rr:
                return False
        return True

    def bt(r):
        if r == n:
            return True
        cand = list(range(n))
        rng.shuffle(cand)
        for c in cand:
            if ok(r, c):
                cols[r] = c
                if bt(r + 1):
                    return True
                cols[r] = -1
        return False

    if not bt(0):
        raise RuntimeError("no placement")
    return cols  # cols[row] = queen column


def grow_regions(rng, n, placement):
    """Grow one connected region per queen by frontier expansion."""
    region = [[-1] * n for _ in range(n)]
    for r in range(n):
        region[r][placement[r]] = r
    left = n * n - n
    while left:
        frontier = []
        for r in range(n):
            for c in range(n):
                if region[r][c] == -1:
                    ns = [region[nr][nc] for dr, dc in
                          ((1, 0), (-1, 0), (0, 1), (0, -1))
                          for nr, nc in [(r + dr, c + dc)]
                          if 0 <= nr < n and 0 <= nc < n and region[nr][nc] >= 0]
                    if ns:
                        frontier.append((r, c, ns))
        if not frontier:
            return None
        rng.shuffle(frontier)
        for r, c, ns in frontier:
            if region[r][c] == -1:
                region[r][c] = ns[rng.randrange(len(ns))]
                left -= 1
    return region


def solve_queens(region, givens, n, limit=2):
    """Counting solver used by the generator (row-by-row backtracking).
    givens: dict (r, c) forced queen cells (or set of cells).
    Returns list of solutions (each a tuple cols-per-row), up to limit."""
    forced = {}
    if givens:
        items = givens.items() if hasattr(givens, "items") else \
            [(rc, True) for rc in givens]
        for (r, c), _v in items:
            forced[r] = c
    cols = [-1] * n
    used_col = [False] * n
    used_reg = [False] * n
    sols = []

    def ok(r, c):
        # LinkedIn Queens rules: distinct column, distinct region, and
        # no diagonal TOUCHING (queens in adjacent rows may not sit in
        # adjacent columns). Longer diagonal attacks are allowed.
        if used_col[c] or used_reg[region[r][c]]:
            return False
        if r > 0 and cols[r - 1] >= 0 and abs(cols[r - 1] - c) <= 1:
            return False
        return True

    def bt(r):
        if len(sols) >= limit:
            return
        if r == n:
            sols.append(tuple(cols))
            return
        cand = [forced[r]] if r in forced else range(n)
        for c in cand:
            if 0 <= c < n and ok(r, c):
                cols[r] = c
                used_col[c] = True
                used_reg[region[r][c]] = True
                bt(r + 1)
                cols[r] = -1
                used_col[c] = False
                used_reg[region[r][c]] = False
            if len(sols) >= limit:
                return

    bt(0)
    return sols


def dig_givens(rng, region, placement, n):
    """Start from the full placement as givens; remove givens while the
    puzzle keeps exactly one solution."""
    givens = {(r, placement[r]) for r in range(n)}
    cells = list(givens)
    rng.shuffle(cells)
    for cell in cells:
        trial = givens - {cell}
        sols = solve_queens(region, trial, n, limit=2)
        if len(sols) == 1:
            givens = trial
    return givens


def make_puzzle(rng, n):
    for _try in range(300):
        placement = gen_placement(rng, n)
        region = grow_regions(rng, n, placement)
        if region is None:
            continue
        givens = dig_givens(rng, region, placement, n)
        sols = solve_queens(region, givens, n, limit=2)
        if len(sols) == 1 and list(sols[0]) == placement:
            return {"n": n, "region": region, "givens": givens,
                    "solution": placement}
    raise RuntimeError("could not construct a proven Queens puzzle")

# -------------------------------------------------------------------- PDF

def _crown(c, x, y, s, color):
    """Draw a simple crown polygon centred in a cell of size s."""
    from reportlab.lib.colors import HexColor
    c.setFillColor(HexColor(color))
    w = s * 0.62
    h = s * 0.4
    x0 = x + (s - w) / 2
    y0 = y + (s - h) / 2
    p = c.beginPath()
    p.moveTo(x0, y0)
    p.lineTo(x0, y0 + h * 0.75)
    p.lineTo(x0 + w * 0.25, y0 + h * 0.35)
    p.lineTo(x0 + w * 0.5, y0 + h)
    p.lineTo(x0 + w * 0.75, y0 + h * 0.35)
    p.lineTo(x0 + w, y0 + h * 0.75)
    p.lineTo(x0 + w, y0)
    p.close()
    c.setStrokeColor(HexColor("#333333"))
    c.setLineWidth(0.8)
    c.drawPath(p, stroke=1, fill=1)


def _draw_grid(c, p, ox, oy, cell, show_givens, show_solution):
    from reportlab.lib.colors import HexColor
    n = p["n"]
    for r in range(n):
        for cc in range(n):
            x = ox + cc * cell
            y = oy + (n - 1 - r) * cell
            c.setFillColor(HexColor(PALETTE[p["region"][r][cc] % len(PALETTE)]))
            c.setStrokeColor(HexColor("#ffffff"))
            c.setLineWidth(1.2)
            c.rect(x, y, cell, cell, stroke=1, fill=1)
    for r in range(n):
        for cc in range(n):
            x = ox + cc * cell
            y = oy + (n - 1 - r) * cell
            if (show_givens and (r, cc) in p["givens"]) or \
               (show_solution and p["solution"][r] == cc):
                _crown(c, x, y, cell, "#1a1a1a")
    c.setStrokeColor(HexColor("#1a1a1a"))
    c.setLineWidth(2.2)
    c.rect(ox, oy, n * cell, n * cell, stroke=1, fill=0)


def render_pdf(path, puzzles):
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.colors import HexColor
    ink = HexColor("#1a1a1a")
    c = rl_canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))
    c.setFillColor(ink)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(72, 640, "QueensPress")
    c.setFont("Helvetica", 15)
    c.drawString(72, 606, "One queen per row, column and color. No touching.")
    c.setFont("Helvetica", 11.5)
    lines = [
        "Place one crown in every row, every column and every color",
        "region. Crowns may not touch, not even diagonally. Some crowns",
        "are printed as givens.",
        "",
        "Every puzzle in this book was re-solved by a counting program",
        "before it was printed: each one has exactly one solution, and",
        "the full solutions are at the back.",
    ]
    y = 540
    for ln in lines:
        c.drawString(72, y, ln)
        y -= 20
    c.showPage()
    for i, p in enumerate(puzzles, 1):
        n = p["n"]
        cell = min(56.0, 470.0 / n)
        ox = (PAGE_W - n * cell) / 2
        oy = (PAGE_H - n * cell) / 2 - 10
        c.setFillColor(ink)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(54, 748, f"Queens {i} -- {n}x{n}, {len(p['givens'])} given crowns")
        _draw_grid(c, p, ox, oy, cell, True, False)
        c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(54, 748, "Solutions")
    c.showPage()
    per = 2
    for k in range(0, len(puzzles), per):
        for j, p in enumerate(puzzles[k:k + per]):
            n = p["n"]
            cell = min(34.0, 280.0 / n)
            ox = 60 + j * 290
            oy = 430
            c.setFillColor(ink)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(ox, oy + n * cell + 12, f"Solution {k + j + 1}")
            _draw_grid(c, p, ox, oy, cell, False, True)
        c.showPage()
    c.save()
    with open(path, "rb") as fh:
        data = fh.read()
    return data.count(b"/Type /Page") - data.count(b"/Type /Pages")

# -------------------------------------------------------------------- run

def run_queenspress(count, outdir, seed=42, size=8, **kw):
    if size not in (6, 7, 8, 9):
        raise ValueError("grid size must be 6, 7, 8 or 9")
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(seed)
    puzzles = [make_puzzle(rng, size) for _ in range(count)]
    pdf_path = os.path.join(outdir, "queens_book.pdf")
    pages = render_pdf(pdf_path, puzzles)
    return {"puzzles": puzzles, "pages": pages, "pdf_path": pdf_path,
            "count": len(puzzles)}


def main(argv):
    outdir = argv[1] if len(argv) > 1 else "out"
    opts = {"puzzles": 12, "size": 8, "seed": 42}
    for a in argv[2:]:
        if a.startswith("--") and "=" in a:
            k, v = a[2:].split("=", 1)
            opts[k] = int(v)
    s = run_queenspress(opts["puzzles"], outdir, seed=opts["seed"],
                        size=opts["size"])
    for i, p in enumerate(s["puzzles"], 1):
        print(f"Queens {i}: {p['n']}x{p['n']}, {len(p['givens'])} givens, unique OK")
    print(f"Pages: {s['pages']}")
    print(f"PDF: {s['pdf_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
