#!/usr/bin/env python3
"""Regenerate the native RevA.2 schematic from the deterministic legacy source.

KiCad 9 can read the generated legacy .sch but has no CLI conversion command.
This wrapper performs the conversion under Xvfb, marks the schematic-only debug
net anchor as not placed/on-board, and atomically installs the native schematic.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASENAME = "CoffeeRoast-Control-RevA"
GENERATOR = ROOT / "tools" / "generate_full_schematic.py"
LEGACY = Path("/tmp/CoffeeRoast-Control-RevA-generated.sch")
DEFAULT_OUTPUT = ROOT / f"{BASENAME}.kicad_sch"


def patch_schematic_only_anchor(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    marker = '(property "Reference" "JDEBUGSCHEM1"'
    pos = text.find(marker)
    if pos < 0:
        raise RuntimeError("JDEBUGSCHEM1 marker missing from converted schematic")
    start = text.rfind("\n\t(symbol", 0, pos)
    end = text.find("\n\t(symbol", pos)
    if start < 0:
        raise RuntimeError("Cannot locate JDEBUGSCHEM1 symbol block")
    if end < 0:
        end = len(text)
    block = text[start:end]
    if "\t\t(on_board yes)" not in block:
        raise RuntimeError("JDEBUGSCHEM1 on_board flag is not in the expected state")
    block = block.replace("\t\t(in_bom yes)", "\t\t(in_bom no)", 1)
    block = block.replace("\t\t(on_board yes)", "\t\t(on_board no)", 1)
    path.write_text(text[:start] + block + text[end:], encoding="utf-8")


def convert(output: Path) -> None:
    subprocess.run(["python3", str(GENERATOR)], cwd=ROOT, check=True)
    if not LEGACY.is_file() or LEGACY.stat().st_size == 0:
        raise RuntimeError(f"Legacy generator did not create {LEGACY}")

    with tempfile.TemporaryDirectory(prefix="coffeeroast-sch-") as tmp:
        work = Path(tmp)
        legacy_target = work / f"{BASENAME}.sch"
        native_target = work / f"{BASENAME}.kicad_sch"
        shutil.copy2(LEGACY, legacy_target)
        shutil.copy2(ROOT / f"{BASENAME}.kicad_pro", work / f"{BASENAME}.kicad_pro")

        shell = f'''
set -eu
eeschema {legacy_target} >{work / "eeschema.log"} 2>&1 &
pid=$!
for _ in $(seq 1 40); do
  warn=$(xdotool search --onlyvisible --name 'Warnung|Warning' 2>/dev/null | tail -1 || true)
  [ -n "$warn" ] && break
  sleep 0.5
done
[ -n "${{warn:-}}" ] || {{ kill "$pid" 2>/dev/null || true; exit 21; }}
xdotool key --window "$warn" Return
for _ in $(seq 1 60); do
  main=$(xdotool search --onlyvisible --name 'Schaltplaneditor|Schematic Editor' 2>/dev/null | tail -1 || true)
  [ -n "$main" ] && break
  sleep 0.5
done
[ -n "${{main:-}}" ] || {{ kill "$pid" 2>/dev/null || true; exit 22; }}
sleep 2
xdotool key --window "$main" ctrl+s
for _ in $(seq 1 40); do
  [ -s {native_target} ] && break
  sleep 0.5
done
kill "$pid" 2>/dev/null || true
[ -s {native_target} ]
'''
        subprocess.run(["xvfb-run", "-a", "bash", "-c", shell], check=True)
        patch_schematic_only_anchor(native_target)
        output.parent.mkdir(parents=True, exist_ok=True)
        staged = output.with_suffix(output.suffix + ".tmp")
        shutil.copy2(native_target, staged)
        staged.replace(output)

    print(f"Regenerated native schematic: {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    convert(args.output.resolve())


if __name__ == "__main__":
    main()
