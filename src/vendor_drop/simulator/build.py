import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from vendor_drop.layout import ORIG_FIELDS, PERF_FIELDS

SERVICERS = [f"svc{i:02d}" for i in range(1, 7)]  # svc01 .. svc06
READ_OPTS = {
    "sep": "|",
    "header": None,  # vendor files have no header row
    "dtype": str,  # keep every value exactly as delivered (no 000123 -> 123)
    "keep_default_na": False,  # empty field stays "", not NaN
    "quoting": csv.QUOTE_NONE,  # the spec has no quoting; a stray " is just a character
}


def assign_servicer(loan_id: str) -> str:
    """Map a loan to one of six servicers, deterministically (same id -> same servicer, always)."""
    digest = hashlib.md5(loan_id.encode("utf-8")).hexdigest()
    return SERVICERS[int(digest, 16) % len(SERVICERS)]


def load_orig(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, names=ORIG_FIELDS, **READ_OPTS)
    df["servicer_id"] = df["loan_seq_no"].map(assign_servicer)
    return df


def load_perf(path: Path, periods: list[str]) -> pd.DataFrame:
    wanted = set(periods)
    kept = []
    for chunk in pd.read_csv(path, names=PERF_FIELDS, chunksize=200_000, **READ_OPTS):
        kept.append(chunk[chunk["reporting_period"].isin(wanted)])
    df = pd.concat(kept, ignore_index=True)
    df["servicer_id"] = df["loan_seq_no"].map(assign_servicer)
    return df


def md5_of_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_file(df: pd.DataFrame, columns: list[str], path: Path) -> dict:
    """Write rows in the vendor's exact format (pipe-delimited, no header) and describe the file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df[columns].to_csv(
        path, sep="|", header=False, index=False, lineterminator="\n", quoting=csv.QUOTE_NONE
    )
    return {"name": path.name, "rows": int(len(df)), "md5": md5_of_file(path)}


def build_all(orig_path: Path, perf_path: Path, periods: list[str], out_dir: Path) -> list[dict]:
    """Create every <servicer>/<period> drop folder with its files and manifest."""
    periods = sorted(periods)
    orig = load_orig(orig_path)
    perf = load_perf(perf_path, periods)
    manifests = []
    for servicer in SERVICERS:
        for i, period in enumerate(periods):
            folder = out_dir / servicer / period
            mask = (perf["servicer_id"] == servicer) & (perf["reporting_period"] == period)
            perf_rows = perf[mask]
            perf_name = folder / f"perf_{servicer}_{period}.txt"
            files = [write_file(perf_rows, PERF_FIELDS, perf_name)]
            orig_count = 0
            if i == 0:  # loan master is delivered once, with the first period
                orig_rows = orig[orig["servicer_id"] == servicer]
                orig_name = folder / f"orig_{servicer}_{period}.txt"
                files.append(write_file(orig_rows, ORIG_FIELDS, orig_name))
                orig_count = len(orig_rows)
            manifest = {
                "servicer_id": servicer,
                "period": period,
                "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
                "files": files,
            }
            manifest_path = folder / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            manifests.append(manifest)
            print(f"{servicer} {period}  perf={len(perf_rows):>7}  orig={orig_count:>6}")
    return manifests
