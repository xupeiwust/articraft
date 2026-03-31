from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from storage.materialize import infer_materialization_status, materialization_paths
from storage.repo import StorageRepo


@dataclass(slots=True, frozen=True)
class BackfillSummary:
    scanned: int
    updated: int
    skipped: Counter[str]


def _eligible_compile_report(
    repo: StorageRepo,
    record_id: str,
    report: object,
) -> tuple[bool, str]:
    if not isinstance(report, dict):
        return False, "missing compile report"
    if report.get("status") != "success":
        return False, "compile status is not success"
    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        return False, "missing metrics"
    if isinstance(metrics.get("compile_level"), str):
        return False, "compile level already present"
    checks_run = report.get("checks_run")
    if checks_run != ["compile_urdf"]:
        return False, "checks_run is not ['compile_urdf']"
    paths = materialization_paths(repo, record_id)
    if not paths["model_urdf"].exists():
        return False, "missing model.urdf"
    if infer_materialization_status(repo, record_id) != "available":
        return False, "materialization is not available"
    return True, "eligible"


def backfill_missing_compile_levels(
    repo_root: Path,
    *,
    dry_run: bool = False,
) -> BackfillSummary:
    repo = StorageRepo(repo_root)
    records_root = repo.layout.records_root
    if not records_root.exists():
        return BackfillSummary(scanned=0, updated=0, skipped=Counter())

    skipped: Counter[str] = Counter()
    updated = 0
    scanned = 0

    for record_dir in sorted(path for path in records_root.iterdir() if path.is_dir()):
        scanned += 1
        record_id = record_dir.name
        compile_report_path = materialization_paths(repo, record_id)["compile_report_json"]
        report = repo.read_json(compile_report_path)
        eligible, reason = _eligible_compile_report(repo, record_id, report)
        if not eligible:
            skipped[reason] += 1
            continue

        metrics = dict(report["metrics"])
        metrics["compile_level"] = "full"
        report = dict(report)
        report["metrics"] = metrics
        if not dry_run:
            repo.write_json(compile_report_path, report)
        updated += 1

    return BackfillSummary(
        scanned=scanned,
        updated=updated,
        skipped=skipped,
    )


def _build_summary_table(summary: BackfillSummary) -> Table:
    table = Table(title="Compile Report Backfill")
    table.add_column("Metric")
    table.add_column("Count", justify="right")
    table.add_row("Scanned records", str(summary.scanned))
    table.add_row("Updated reports", str(summary.updated))
    for reason, count in sorted(summary.skipped.items()):
        table.add_row(f"Skipped: {reason}", str(count))
    return table


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="backfill_compile_report_levels.py")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root containing data/records.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show how many reports would be updated without writing changes.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    summary = backfill_missing_compile_levels(
        args.repo_root.resolve(),
        dry_run=bool(args.dry_run),
    )
    console = Console()
    console.print(_build_summary_table(summary))
    if args.dry_run:
        console.print("[green]Dry run complete.[/green]")
    else:
        console.print("[green]Backfill complete.[/green]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
