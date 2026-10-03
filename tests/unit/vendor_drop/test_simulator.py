import hashlib
import json

import pandas as pd

from vendor_drop.layout import ORIG_FIELDS, PERF_FIELDS
from vendor_drop.simulator.build import SERVICERS, assign_servicer, build_all, write_file


def _fake_perf(n_loans: int, periods: list[str]) -> pd.DataFrame:
    rows = []
    for i in range(n_loans):
        for p in periods:
            r = dict.fromkeys(PERF_FIELDS, "")
            r.update(loan_seq_no=f"F23Q1{i:07d}", reporting_period=p, dlq_status="00")
            rows.append(r)
    return pd.DataFrame(rows, columns=PERF_FIELDS)


def _fake_orig(n_loans: int) -> pd.DataFrame:
    rows = []
    for i in range(n_loans):
        r = dict.fromkeys(ORIG_FIELDS, "")
        r.update(loan_seq_no=f"F23Q1{i:07d}", seller_name="OTHER")
        rows.append(r)
    return pd.DataFrame(rows, columns=ORIG_FIELDS)


def test_assign_servicer_is_deterministic_and_in_range():
    assert assign_servicer("F23Q10000001") == assign_servicer("F23Q10000001")
    assert all(assign_servicer(f"F23Q1{i:07d}") in SERVICERS for i in range(100))


def test_write_file_round_trip(tmp_path):
    path = tmp_path / "perf_test.txt"
    info = write_file(_fake_perf(5, ["202601"]), PERF_FIELDS, path)
    lines = path.read_text().splitlines()
    assert info["rows"] == len(lines) == 5
    assert all(len(line.split("|")) == len(PERF_FIELDS) for line in lines)
    assert info["md5"] == hashlib.md5(path.read_bytes()).hexdigest()
    assert b"\r\n" not in path.read_bytes()  # LF only, even on Windows


def test_build_all_layout(tmp_path):
    periods = ["202601", "202602"]
    _fake_orig(60).to_csv(tmp_path / "orig.txt", sep="|", header=False, index=False)
    _fake_perf(60, periods).to_csv(tmp_path / "perf.txt", sep="|", header=False, index=False)
    out = tmp_path / "out"
    manifests = build_all(tmp_path / "orig.txt", tmp_path / "perf.txt", periods, out)
    assert len(manifests) == len(SERVICERS) * len(periods)
    for servicer in SERVICERS:
        first, second = out / servicer / "202601", out / servicer / "202602"
        assert (first / "manifest.json").exists() and (second / "manifest.json").exists()
        assert (first / f"perf_{servicer}_202601.txt").exists()
        assert (first / f"orig_{servicer}_202601.txt").exists()
        assert not (second / f"orig_{servicer}_202602.txt").exists()
    perf_files = [f for m in manifests for f in m["files"] if f["name"].startswith("perf_")]
    total_perf = sum(f["rows"] for f in perf_files)
    assert total_perf == 60 * len(periods)
    m = json.loads((out / "svc01" / "202601" / "manifest.json").read_text())
    assert m["servicer_id"] == "svc01" and m["period"] == "202601"
