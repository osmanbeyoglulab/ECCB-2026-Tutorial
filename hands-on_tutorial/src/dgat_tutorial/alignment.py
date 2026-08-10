"""Strict ID-alignment helpers that refuse silent intersections."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class AlignmentReport:
    """Describe whether two index/column sets agree exactly."""

    missing_in_left: list[str]
    missing_in_right: list[str]
    left_only: list[str]
    right_only: list[str]

    @property
    def is_exact(self) -> bool:
        return not (self.left_only or self.right_only)


def compare_identifiers(left, right, *, label: str = "IDs") -> AlignmentReport:
    """Compare two pandas Index-like collections without silently dropping values."""

    left_ids = pd.Index(left)
    right_ids = pd.Index(right)
    left_only = [str(value) for value in left_ids.difference(right_ids)]
    right_only = [str(value) for value in right_ids.difference(left_ids)]
    return AlignmentReport(
        missing_in_left=right_only,
        missing_in_right=left_only,
        left_only=left_only,
        right_only=right_only,
    )


def require_exact_identifiers(left, right, *, left_name: str, right_name: str) -> None:
    """Raise if identifier sets differ; never silently intersect."""

    report = compare_identifiers(left, right)
    if report.is_exact:
        return
    details = []
    if report.left_only:
        preview = ", ".join(report.left_only[:5])
        more = "" if len(report.left_only) <= 5 else f" (+{len(report.left_only) - 5} more)"
        details.append(f"{len(report.left_only)} only in {left_name}: {preview}{more}")
    if report.right_only:
        preview = ", ".join(report.right_only[:5])
        more = "" if len(report.right_only) <= 5 else f" (+{len(report.right_only) - 5} more)"
        details.append(f"{len(report.right_only)} only in {right_name}: {preview}{more}")
    raise ValueError(
        f"{left_name} and {right_name} identifiers do not match exactly. "
        + " ".join(details)
        + " Resolve the mismatch before continuing; silent intersections are not allowed."
    )


def align_frames_exactly(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    left_name: str,
    right_name: str,
    axis: str = "index",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return copies after verifying exact index or column agreement."""

    if axis == "index":
        require_exact_identifiers(left.index, right.index, left_name=left_name, right_name=right_name)
        if not left.index.equals(right.index):
            right = right.loc[left.index]
        return left.copy(), right.copy()
    if axis == "columns":
        require_exact_identifiers(left.columns, right.columns, left_name=left_name, right_name=right_name)
        if not left.columns.equals(right.columns):
            right = right.loc[:, left.columns]
        return left.copy(), right.copy()
    raise ValueError("axis must be 'index' or 'columns'")
