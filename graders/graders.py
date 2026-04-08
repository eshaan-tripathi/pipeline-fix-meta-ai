"""
Graders compare the agent's output CSV against the golden CSV.
Each grader returns a score in [0.0, 1.0] plus a breakdown dict.
All graders are deterministic and reproducible.
"""

import io
import math
import pandas as pd
from typing import Tuple


def _parse_csv(csv_text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(csv_text.strip()))


def _col_score(got: pd.DataFrame, golden: pd.DataFrame) -> float:
    """Fraction of golden columns present in got."""
    golden_cols = set(golden.columns)
    got_cols = set(got.columns)
    if not golden_cols:
        return 1.0
    return len(golden_cols & got_cols) / len(golden_cols)


def _row_score(got: pd.DataFrame, golden: pd.DataFrame) -> float:
    """Fraction of expected row count (capped at 1.0)."""
    if len(golden) == 0:
        return 1.0
    ratio = len(got) / len(golden)
    return min(ratio, 1.0) * (1.0 if abs(ratio - 1.0) < 0.05 else 0.5)


def _value_score(got: pd.DataFrame, golden: pd.DataFrame, tol: float = 0.01) -> float:
    """Cell-level accuracy for columns present in both, numeric within tolerance."""
    common_cols = list(set(got.columns) & set(golden.columns))
    if not common_cols:
        return 0.0
    n_rows = min(len(got), len(golden))
    if n_rows == 0:
        return 0.0
    total = 0
    correct = 0
    for col in common_cols:
        g_col = golden[col].reset_index(drop=True)
        o_col = got[col].reset_index(drop=True)
        for i in range(n_rows):
            total += 1
            try:
                gv = float(g_col.iloc[i])
                ov = float(o_col.iloc[i])
                if math.isclose(gv, ov, rel_tol=tol):
                    correct += 1
            except (ValueError, TypeError):
                if str(g_col.iloc[i]).strip() == str(o_col.iloc[i]).strip():
                    correct += 1
    return correct / total if total > 0 else 0.0


class BaseGrader:
    weights = {"cols": 0.3, "rows": 0.3, "values": 0.4}

    def score(self, output_csv: str, golden_csv: str) -> Tuple[float, dict]:
        try:
            got = _parse_csv(output_csv)
            golden = _parse_csv(golden_csv)
        except Exception as e:
            return 0.0, {"error": str(e), "cols": 0, "rows": 0, "values": 0}

        cs = _col_score(got, golden)
        rs = _row_score(got, golden)
        vs = _value_score(got, golden)

        total = (
            self.weights["cols"] * cs
            + self.weights["rows"] * rs
            + self.weights["values"] * vs
        )
        total = round(min(max(total, 0.0), 1.0), 4)
        return total, {"cols": round(cs, 3), "rows": round(rs, 3), "values": round(vs, 3)}


class EasyGrader(BaseGrader):
    """Grader for task_easy. Weights value accuracy higher since it's a simple fix."""
    weights = {"cols": 0.25, "rows": 0.25, "values": 0.50}


class MediumGrader(BaseGrader):
    """Grader for task_medium. Balanced — 3 independent bugs, partial credit per bug."""
    weights = {"cols": 0.30, "rows": 0.30, "values": 0.40}


class HardGrader(BaseGrader):
    """Grader for task_hard. Penalises row explosion (wrong merge) heavily."""

    def score(self, output_csv: str, golden_csv: str) -> Tuple[float, dict]:
        try:
            got = _parse_csv(output_csv)
            golden = _parse_csv(golden_csv)
        except Exception as e:
            return 0.0, {"error": str(e)}

        cs = _col_score(got, golden)
        rs = _row_score(got, golden)
        vs = _value_score(got, golden)

        # Extra penalty if row count is > 2x expected (row explosion from bad merge)
        if len(got) > len(golden) * 2:
            rs = rs * 0.2

        # Check sort order: revenue_usd should be descending
        sort_ok = 0.0
        if "revenue_usd" in got.columns and len(got) > 1:
            vals = got["revenue_usd"].dropna().tolist()
            if vals == sorted(vals, reverse=True):
                sort_ok = 1.0

        total = 0.25 * cs + 0.25 * rs + 0.35 * vs + 0.15 * sort_ok
        total = round(min(max(total, 0.0), 1.0), 4)
        return total, {
            "cols": round(cs, 3),
            "rows": round(rs, 3),
            "values": round(vs, 3),
            "sort_order": sort_ok,
        }


GRADER_REGISTRY = {
    "task_easy": EasyGrader(),
    "task_medium": MediumGrader(),
    "task_hard": HardGrader(),
}
