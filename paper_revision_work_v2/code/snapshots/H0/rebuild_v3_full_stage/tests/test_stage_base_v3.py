import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_stage_base_v3.py"
spec = importlib.util.spec_from_file_location("build_stage_base_v3", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_rows():
    return pd.DataFrame(
        [
            ("A", 1, "2022-01-01T00:00:00Z", "2022-01-01T01:00:00Z", 10, "N", "71"),
            ("A", 2, "2022-01-01T02:00:00Z", "2022-01-01T03:00:00Z", 10, "Y", "71"),
            ("B", 1, "2022-01-01T00:00:00Z", "2022-01-01T02:00:00Z", 20, "0", "06"),
            ("B", 2, "2022-01-01T03:00:00Z", "2022-01-01T04:00:00Z", 20, "1", "06"),
            ("C", 1, "2022-01-01T00:00:00Z", "2022-01-01T01:00:00Z", 0, "Y", "71"),
        ],
        columns=[
            "Incident Reference",
            "Restoration Stage",
            "Start Date and Time",
            "End Date and Time",
            "Number of Customers Restored",
            "Re-interruption Stage",
            "Cause Code",
        ],
    )


def test_stage_rows_are_preserved_and_event_values_are_mapped_back():
    source = make_rows()
    result, qa, boundary, _ = module.build_stage_dataset(source)
    assert len(result) == len(source) == 5
    assert result["source_row_number"].tolist() == [1, 2, 3, 4, 5]
    assert qa["rows_preserved_exactly"] is True
    assert result.loc[result["Incident Reference"] == "A", "customers_v2_event_excl_reinterruptions"].eq(10).all()
    assert result.loc[result["Incident Reference"] == "B", "customers_v2_event_excl_reinterruptions"].eq(20).all()
    assert boundary["Incident Reference"].tolist() == ["C"]


def test_legacy_one_is_treated_as_reinterruption_and_durations_are_exact():
    result, _, _, _ = module.build_stage_dataset(make_rows())
    a = result[result["Incident Reference"] == "A"].iloc[0]
    b = result[result["Incident Reference"] == "B"].iloc[0]
    assert a["duration_A_customer_weighted_hours"] == 1.0
    assert a["duration_B_full_span_hours"] == 3.0
    assert a["customer_minutes_lost_event"] == 1200.0
    assert b["duration_A_customer_weighted_hours"] == 1.5
    assert b["duration_B_full_span_hours"] == 4.0
    assert b["customers_v2_event_excl_reinterruptions"] == 20.0
    assert np.isclose(b["Duration (hours)"], 1.5)
