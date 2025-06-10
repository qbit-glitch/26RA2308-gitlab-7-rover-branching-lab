"""Threshold obstacle detector for the Kestrel-1 camera scores."""
from __future__ import annotations

import sys
from typing import List, Tuple

THRESHOLD = 0.55


def load_readings(path: str) -> List[Tuple[float, int]]:
    """Read 'score label' lines, skipping blank lines and '#' comments."""
    readings: List[Tuple[float, int]] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            score, label = line.split()
            readings.append((float(score), int(label)))
    return readings


def evaluate(readings: List[Tuple[float, int]], threshold: float) -> Tuple[int, int]:
    """Return (correct, total) when 'score >= threshold' means 'obstacle'."""
    correct = sum(1 for score, label in readings if (score >= threshold) == bool(label))
    return correct, len(readings)


def main(argv: List[str]) -> int:
    """Print the detector accuracy for the readings file given on the command line."""
    if len(argv) != 2:
        print("usage: detector.py <readings-file>")
        return 2
    correct, total = evaluate(load_readings(argv[1]), THRESHOLD)
    print(f"threshold={THRESHOLD:.2f} samples={total} correct={correct} accuracy={correct / total:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
