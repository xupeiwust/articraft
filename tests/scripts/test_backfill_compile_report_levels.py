from __future__ import annotations

import json

from scripts.backfill_compile_report_levels import backfill_missing_compile_levels
from storage.repo import StorageRepo


def test_backfill_missing_compile_levels_updates_runtime_style_reports(tmp_path) -> None:
    repo = StorageRepo(tmp_path)
    repo.ensure_layout()

    record_id = "rec_runtime_full"
    record_dir = repo.layout.record_dir(record_id)
    record_dir.mkdir(parents=True, exist_ok=True)
    materialization_dir = repo.layout.record_materialization_dir(record_id)
    materialization_dir.mkdir(parents=True, exist_ok=True)

    (record_dir / "model.py").write_text("object_model = None\n", encoding="utf-8")
    (materialization_dir / "model.urdf").write_text(
        "<robot name='primitive'><link name='base'><visual><geometry><box size='1 1 1'/></geometry></visual></link></robot>",
        encoding="utf-8",
    )
    (materialization_dir / "compile_report.json").write_text(
        json.dumps(
            {
                "status": "success",
                "checks_run": ["compile_urdf"],
                "metrics": {
                    "turn_count": 4,
                    "tool_call_count": 7,
                    "compile_attempt_count": 1,
                },
            }
        ),
        encoding="utf-8",
    )

    summary = backfill_missing_compile_levels(tmp_path)

    assert summary.updated == 1
    report = repo.read_json(materialization_dir / "compile_report.json")
    assert report["metrics"]["compile_level"] == "full"


def test_backfill_missing_compile_levels_skips_reports_without_available_materialization(
    tmp_path,
) -> None:
    repo = StorageRepo(tmp_path)
    repo.ensure_layout()

    record_id = "rec_missing_assets"
    record_dir = repo.layout.record_dir(record_id)
    record_dir.mkdir(parents=True, exist_ok=True)
    materialization_dir = repo.layout.record_materialization_dir(record_id)
    materialization_dir.mkdir(parents=True, exist_ok=True)

    (record_dir / "model.py").write_text("object_model = None\n", encoding="utf-8")
    (materialization_dir / "model.urdf").write_text(
        "<robot name='mesh'><link name='base'><visual><geometry><mesh filename='assets/meshes/part.obj'/></geometry></visual></link></robot>",
        encoding="utf-8",
    )
    (materialization_dir / "compile_report.json").write_text(
        json.dumps(
            {
                "status": "success",
                "checks_run": ["compile_urdf"],
                "metrics": {
                    "turn_count": 4,
                    "tool_call_count": 7,
                    "compile_attempt_count": 1,
                },
            }
        ),
        encoding="utf-8",
    )

    summary = backfill_missing_compile_levels(tmp_path)

    assert summary.updated == 0
    assert summary.skipped["materialization is not available"] == 1
    report = repo.read_json(materialization_dir / "compile_report.json")
    assert "compile_level" not in report["metrics"]


def test_backfill_missing_compile_levels_skips_non_runtime_check_sets(tmp_path) -> None:
    repo = StorageRepo(tmp_path)
    repo.ensure_layout()

    record_id = "rec_legacy_import"
    record_dir = repo.layout.record_dir(record_id)
    record_dir.mkdir(parents=True, exist_ok=True)
    materialization_dir = repo.layout.record_materialization_dir(record_id)
    materialization_dir.mkdir(parents=True, exist_ok=True)

    (record_dir / "model.py").write_text("object_model = None\n", encoding="utf-8")
    (materialization_dir / "model.urdf").write_text(
        "<robot name='primitive'><link name='base'><visual><geometry><box size='1 1 1'/></geometry></visual></link></robot>",
        encoding="utf-8",
    )
    (materialization_dir / "compile_report.json").write_text(
        json.dumps(
            {
                "status": "success",
                "checks_run": ["legacy_import"],
                "metrics": {
                    "turn_count": 4,
                },
            }
        ),
        encoding="utf-8",
    )

    summary = backfill_missing_compile_levels(tmp_path)

    assert summary.updated == 0
    assert summary.skipped["checks_run is not ['compile_urdf']"] == 1
    report = repo.read_json(materialization_dir / "compile_report.json")
    assert "compile_level" not in report["metrics"]
