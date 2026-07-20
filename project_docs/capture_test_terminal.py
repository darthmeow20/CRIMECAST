# -*- coding: utf-8 -*-
"""
Run unit tests and save:
  1) Text log  → project_docs/figures/screenshots/run_tests_output.txt
  2) Terminal-style PNG for Forms/Report annex

Usage (from project root):
  py -3 project_docs/capture_test_terminal.py
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = Path(__file__).resolve().parent / "figures" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG = OUT_DIR / "run_tests_output.txt"
PNG = OUT_DIR / "shot_08_run_tests_terminal.png"


def run_tests() -> tuple[str, int]:
    cmd = [sys.executable, str(ROOT / "run_tests.py"), "-q"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        return out.strip() + "\n", int(proc.returncode)
    except Exception as e:
        return f"Could not run tests in subprocess: {e}\n", 1


def render_terminal_png(text: str, exit_code: int) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Keep last ~40 lines for readability
    lines = text.replace("\r\n", "\n").split("\n")
    if len(lines) > 42:
        lines = ["… (earlier output truncated) …"] + lines[-41:]
    body = "\n".join(lines)
    if not body.strip():
        body = "(no output captured)\n"

    header = (
        "PS CRIMECAST> py -3 run_tests.py\n"
        "────────────────────────────────────────\n"
    )
    footer = (
        f"\n────────────────────────────────────────\n"
        f"Exit code: {exit_code}  "
        f"{'OK' if exit_code == 0 else 'FAILED (or skips/errors — see log)'}\n"
    )
    full = header + body + footer

    # Figure size based on line count
    n = full.count("\n") + 1
    fig_h = max(5.5, min(11.0, 0.28 * n + 1.2))
    fig, ax = plt.subplots(figsize=(10.5, fig_h))
    fig.patch.set_facecolor("#0c0c0c")
    ax.set_facecolor("#0c0c0c")
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    # Title bar
    ax.text(
        0.02,
        0.98,
        "CRIMECAST  ·  run_tests.py  ·  Testing output",
        color="#22c55e",
        fontsize=11,
        fontweight="bold",
        va="top",
        family="monospace",
        transform=ax.transAxes,
    )
    ax.text(
        0.02,
        0.93,
        full,
        color="#e5e7eb",
        fontsize=8.5,
        va="top",
        ha="left",
        family="monospace",
        transform=ax.transAxes,
        linespacing=1.35,
    )
    fig.savefig(PNG, dpi=160, bbox_inches="tight", facecolor="#0c0c0c")
    plt.close(fig)


def main() -> int:
    print("Running tests…")
    text, code = run_tests()
    LOG.write_text(text, encoding="utf-8")
    print(f"[OK] Log → {LOG}")
    try:
        render_terminal_png(text, code)
        print(f"[OK] PNG → {PNG}")
    except Exception as e:
        print(f"[WARN] PNG not created: {e}")
    print(f"Test exit code: {code}")
    return 0  # capture itself succeeded even if tests failed


if __name__ == "__main__":
    raise SystemExit(main())
