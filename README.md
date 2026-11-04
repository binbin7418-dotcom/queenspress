# QueensPress

Build print-ready **Queens puzzle books** (the LinkedIn-style color-region queens game) where every puzzle is *proven* to have exactly one solution.

## Why

Queens looks simple — one queen per row, column and color, no touching — and that is exactly why broken puzzles slip through: draw colored regions freehand, drop in a solution you found once, and a second arrangement usually also fits. QueensPress builds so that can't happen:

1. A valid queen placement is generated first (no two queens share a row, column or diagonal reach under the game's rules).
2. Colored regions are **grown around the queens** by frontier expansion, so every region is one connected piece containing exactly one queen of the intended solution.
3. Given crowns are then dug away one at a time — a crown stays removed only while a counting solver proves the puzzle still has **exactly one** solution. The printed puzzle is the dug result: minimal-ish givens, unique by proof.

## Use

**App (Windows):** launch `QueensPress.exe`, choose the puzzle count, grid size (6×6 / 7×7 / 8×8 / 9×9) and a seed, click **Build the book**. Output: `queens_book.pdf` in a `queenspress_out` folder — title page, one puzzle per page (soft-color regions, printed given crowns), then full solutions. 8.5×11in (612×792pt).

**Command line:** `python queens_press.py out/ --puzzles=50 --size=8 --seed=42`

A 6-puzzle sample book is included (`sample_book.pdf`).

Rules implemented exactly as the daily game plays them: one queen per row, column and region, and queens may not touch **diagonally** (longer diagonal lines are fine — this is not chess).

## Verified

Acceptance test (8/8 PASS, `test/acceptance_results.txt`): a 6-puzzle 8×8 book re-verified by an independent checker that enumerates **all 40,320 column permutations** per puzzle and filters by the printed rules — exactly one survives, equal to the printed solution; regions partition the grid and are all connected; every given crown sits on the solution; moving one given crown breaks the proof; PDF exactly 11 pages at 612×792pt; whole book in about 0.2 seconds; deterministic for a fixed seed.

## Scope

Queens puzzles on 6×6–9×9 grids — a public-domain puzzle form in the style popularized by LinkedIn's daily game; not affiliated with LinkedIn. 100% local — no uploads, no accounts, no per-book fees. Deterministic seeds make series production repeatable.

## Build from source

`pip install pyinstaller reportlab`, then `pyinstaller queenspress.spec`. Or push to GitHub and let the included Actions workflow build the Windows package.
