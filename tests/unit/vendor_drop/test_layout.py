import os

import pytest

from vendor_drop.layout import ORIG_FIELDS, PERF_FIELDS


def test_field_counts():
    assert len(ORIG_FIELDS) == 31
    assert len(PERF_FIELDS) == 35


def test_no_duplicate_names():
    assert len(set(ORIG_FIELDS)) == len(ORIG_FIELDS)
    assert len(set(PERF_FIELDS)) == len(PERF_FIELDS)


def test_key_columns_in_position():
    assert ORIG_FIELDS[19] == "loan_seq_no"
    assert PERF_FIELDS[:4] == ["loan_seq_no", "reporting_period", "current_upb", "dlq_status"]


def _first_line_piece_count(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        line = f.readline().rstrip("\r\n")
    return len(line.split("|"))


@pytest.mark.skipif("FREDDIE_DATA_DIR" not in os.environ, reason="needs local Freddie sample data")
def test_matches_real_file():
    data_dir = os.environ["FREDDIE_DATA_DIR"]
    orig_path = os.path.join(data_dir, "sample_orig_2023.txt")
    perf_path = os.path.join(data_dir, "sample_perf_2023.txt")

    assert _first_line_piece_count(orig_path) == len(ORIG_FIELDS)
    assert _first_line_piece_count(perf_path) == len(PERF_FIELDS)
