from __future__ import annotations

from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = Path(r"C:\Users\L2791\thinfilm_outputs")

DEG_S_DIR = DATA_DIR / "deg.s"
DEG_P_DIR = DATA_DIR / "deg.p"
DEG_AVG_DIR = DATA_DIR / "deg.avg"


def data_file(*parts: str) -> Path:
    return DATA_DIR.joinpath(*parts)


def output_file(name: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / name
