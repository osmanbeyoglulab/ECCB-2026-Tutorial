from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class TutorialPaths:
    """Canonical paths used by every independently runnable tutorial part."""

    root: Path
    raw_data: Path
    processed_data: Path
    results: Path
    figures: Path
    checkpoints: Path


def find_tutorial_root(start: Path | None = None) -> Path:
    """Find the hands-on tutorial root from Jupyter or a command-line process."""

    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "src" / "dgat_tutorial").is_dir() and (
            candidate / "requirements-colab.txt"
        ).is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate the hands-on tutorial root. Open the notebook through "
        "the participant Colab link and rerun its first bootstrap cell."
    )


def tutorial_paths(start: Path | None = None) -> TutorialPaths:
    root = find_tutorial_root(start)
    state_dir_value = os.environ.get("DGAT_TUTORIAL_STATE_DIR")
    state_root = Path(state_dir_value).expanduser().resolve() if state_dir_value else root
    paths = TutorialPaths(
        root=root,
        raw_data=root / "data" / "raw",
        processed_data=state_root / "data" / "processed",
        results=state_root / "results",
        figures=state_root / "results" / "figures",
        checkpoints=state_root / "checkpoints",
    )
    for directory in (paths.processed_data, paths.results, paths.figures, paths.checkpoints):
        directory.mkdir(parents=True, exist_ok=True)
    return paths


def write_checkpoint(
    part_id: str,
    artifacts: Iterable[Path],
    *,
    summary: dict[str, Any] | None = None,
    start: Path | None = None,
) -> Path:
    """Write a small manifest proving that a tutorial part completed."""

    paths = tutorial_paths(start)
    session_id = part_id.split(".", maxsplit=1)[0]
    checkpoint_dir = paths.checkpoints / f"session_{int(session_id):02d}"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = checkpoint_dir / f"part_{part_id.replace('.', '_')}.json"

    artifact_rows = []
    for artifact in artifacts:
        resolved = Path(artifact).resolve()
        try:
            display_path = str(resolved.relative_to(paths.root))
        except ValueError:
            # Colab keeps restart-safe artifacts in Google Drive, outside the cloned repo.
            display_path = str(resolved)
        artifact_rows.append(
            {
                "path": display_path,
                "exists": resolved.exists(),
            }
        )

    manifest = {
        "part": part_id,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": artifact_rows,
        "summary": summary or {},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def preferred_prediction_path(paths: TutorialPaths) -> Path:
    """Use a Session 2 checkpoint when present, otherwise the committed DGAT table."""

    processed = paths.processed_data / "predicted_proteins.csv"
    if processed.is_file():
        return processed
    committed = paths.raw_data / "dgat_predictions.csv"
    if committed.is_file():
        return committed
    raise FileNotFoundError(
        "No prediction table found. Restore data/raw/dgat_predictions.csv or run Session 2, Part 4."
    )
