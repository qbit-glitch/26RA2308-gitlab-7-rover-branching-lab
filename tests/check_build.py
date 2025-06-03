#!/usr/bin/env python3
"""Compile and run the sensor unit test (no make needed). Exit 0 = pass, 1 = test failed, 2 = cannot build."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]


def find_compiler() -> Optional[str]:
    """Return the path of $CC, gcc or cc, whichever exists first."""
    for name in (os.environ.get("CC"), "gcc", "cc"):
        found = shutil.which(name) if name else None
        if found:
            return found
    return None


def main() -> int:
    """Build tests/test_sensor.c with src/sensor.c in a temporary folder and run it."""
    compiler = find_compiler()
    if compiler is None:
        print("No C compiler found (looked for $CC, gcc and cc). Install gcc and try again.")
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "test_sensor")
        build = [compiler, "-Wall", "-Wextra", "-I", str(ROOT / "src"), "-o", exe,
                 str(ROOT / "tests" / "test_sensor.c"), str(ROOT / "src" / "sensor.c")]
        built = subprocess.run(build, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        if built.returncode != 0:
            print(built.stdout, end="")
            print("The C code did not compile.")
            return 2
        ran = subprocess.run([exe], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        print(ran.stdout, end="")
        return ran.returncode


if __name__ == "__main__":
    sys.exit(main())
