import os
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from queens_press import run_queenspress


def run_job(count, size, seed, outdir):
    s = run_queenspress(count, outdir, seed=seed, size=size)
    lines = [f"Puzzles built: {len(s['puzzles'])}", f"Pages: {s['pages']}"]
    for i, p in enumerate(s["puzzles"], 1):
        lines.append(f"  Puzzle {i}: {p['n']}x{p['n']}, {len(p['givens'])} given crowns, "
                     f"unique solution proven")
    lines.append(f"PDF: {s['pdf_path']}")
    return lines


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QueensPress")
        self.geometry("640x520")
        self.resizable(False, False)
        self.count = tk.StringVar(value="50")
        self.size = tk.StringVar(value="8")
        self.seed = tk.StringVar(value="42")
        for label, var in [("Puzzles:", self.count),
                           ("Grid size (6/7/8/9):", self.size),
                           ("Seed:", self.seed)]:
            row = tk.Frame(self); row.pack(fill="x", padx=12, pady=2)
            tk.Label(row, text=label, width=34, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, width=10).pack(side="left")
        tk.Button(self, text="Build the book", font=("Segoe UI", 11, "bold"),
                  command=self.start).pack(pady=10)
        self.log = scrolledtext.ScrolledText(self, width=76, height=16,
                                             font=("Consolas", 9))
        self.log.pack(padx=12, pady=4)
        self.write("Regions are grown around a real queen placement, then given crowns are dug away one at a time -- a crown is only removed while a counting solver proves the puzzle still has exactly one solution.")

    def write(self, msg):
        self.log.insert(tk.END, str(msg) + "\n")
        self.log.see(tk.END)
        self.update_idletasks()

    def collect(self):
        size = int(self.size.get())
        if size not in (6, 7, 8, 9):
            raise ValueError("Grid size must be 6, 7, 8 or 9.")
        return (int(self.count.get()), size, int(self.seed.get()),
                os.path.join(os.getcwd(), "queenspress_out"))

    def start(self):
        try:
            args = self.collect()
        except Exception as e:
            messagebox.showerror("QueensPress", str(e))
            return

        def work():
            try:
                for ln in run_job(*args):
                    self.write(ln)
            except Exception as e:
                self.write(f"ERROR: {e}")

        threading.Thread(target=work, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()
