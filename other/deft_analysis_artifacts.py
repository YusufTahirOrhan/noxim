#!/usr/bin/env python3
"""
Prepare traceable DeFT final-analysis scaffolding from T0021 runner outputs.

This helper intentionally performs only mechanical aggregation of existing
manifests and T0020 stats exports. It does not run simulations, define a final
sweep policy, or make performance claims.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any, Dict, Iterable, List, Sequence, Tuple


SCRIPT_NAME = "deft_analysis_artifacts.py"
ANALYZER_VERSION = "1"
ANALYZER_SCHEMA = "deft_analysis_artifacts.v1"
RUNNER_SCHEMA = "deft_experiment_runner.v1"

METRIC_COLUMNS = (
    "total_injected_packets",
    "total_injected_flits",
    "total_received_packets",
    "total_received_flits",
    "reachability_ratio",
    "global_average_delay_cycles",
    "network_throughput_flits_per_cycle",
    "average_ip_throughput_flits_per_cycle_per_ip",
)

KEY_METRIC_COLUMNS = (
    "reachability_ratio",
    "global_average_delay_cycles",
    "network_throughput_flits_per_cycle",
)


def default_noxim_root() -> Path:
    return Path(__file__).resolve().parents[1]


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create traceable CSV and Markdown analysis scaffolding from "
            "T0021 deft_experiment_runner output directories."
        )
    )
    parser.add_argument(
        "--noxim-root",
        type=Path,
        default=default_noxim_root(),
        help="Noxim repository root. Defaults to the parent of this script's directory.",
    )
    parser.add_argument(
        "--input-dir",
        action="append",
        type=Path,
        required=True,
        help=(
            "T0021 runner output directory containing manifest.json and summary.csv. "
            "May be repeated."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "Directory for generated analysis artifacts. Defaults to "
            "other/generated/deft_analysis/<timestamp> under Noxim."
        ),
    )
    parser.add_argument(
        "--dataset-kind",
        choices=("smoke", "final_sweep"),
        default="smoke",
        help=(
            "Caller-declared dataset purpose. Default smoke keeps generated report "
            "blocked for final performance claims."
        ),
    )
    return parser


def resolve_output_dir(noxim_root: Path, requested: Path | None) -> Path:
    if requested is not None:
        return requested.resolve()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return noxim_root / "other" / "generated" / "deft_analysis" / timestamp


def path_from_text(path_text: str) -> Path:
    return Path(path_text.replace("\\", os.sep))


def wsl_to_windows_path(path_text: str) -> Path | None:
    normalized = path_text.replace("\\", "/")
    parts = normalized.split("/")
    if len(parts) >= 4 and parts[0] == "" and parts[1] == "mnt" and len(parts[2]) == 1:
        drive = parts[2].upper()
        return Path(f"{drive}:/" + "/".join(parts[3:]))
    return None


def windows_to_wsl_path(path_text: str) -> Path | None:
    normalized = path_text.replace("\\", "/")
    if len(normalized) >= 3 and normalized[1] == ":" and normalized[2] == "/":
        drive = normalized[0].lower()
        return Path("/mnt") / drive / normalized[3:]
    return None


def resolve_artifact_path(
    path_text: str,
    input_dir: Path,
    fallback_subdir: str | None = None,
) -> Tuple[str, bool]:
    if not path_text:
        return "", False

    candidates: List[Path] = []
    raw = path_from_text(path_text)
    candidates.append(raw)
    if not raw.is_absolute():
        candidates.append(input_dir / raw)

    converted = wsl_to_windows_path(path_text) if os.name == "nt" else windows_to_wsl_path(path_text)
    if converted is not None:
        candidates.append(converted)

    if fallback_subdir:
        candidates.append(input_dir / fallback_subdir / Path(path_text).name)

    for candidate in candidates:
        if candidate.exists():
            return candidate.as_posix(), True

    return candidates[0].as_posix(), False


def read_json_file(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_summary_csv(input_dir: Path) -> Dict[str, Dict[str, str]]:
    summary_file = input_dir / "summary.csv"
    if not summary_file.exists():
        return {}

    with summary_file.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row.get("run_id", ""): row for row in rows if row.get("run_id")}


def first_nonempty(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return ""


def stringify_sequence(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value) if value is not None else ""


def load_stats_metrics(stats_path_text: str, input_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Any], str, bool]:
    resolved_path, exists = resolve_artifact_path(stats_path_text, input_dir, "stats")
    if not exists:
        return {}, {}, resolved_path, False

    stats_path = Path(resolved_path)
    if stats_path.suffix.lower() != ".json":
        return {}, {}, resolved_path, True

    data = read_json_file(stats_path)
    return data.get("config", {}), data.get("summary", {}), resolved_path, True


def has_metrics(row: Dict[str, Any]) -> bool:
    return any(str(row.get(column, "")) != "" for column in KEY_METRIC_COLUMNS)


def normalize_return_code(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def classify_row(row: Dict[str, Any]) -> str:
    status = row.get("status", "")
    return_code = normalize_return_code(row.get("return_code", ""))
    if status == "completed" and return_code == "0" and has_metrics(row):
        return "completed_with_metrics"
    if status == "completed" and return_code == "0":
        return "completed_missing_metrics"
    if status == "planned":
        return "planned_only"
    if status == "blocked":
        return "blocked"
    return "failed_or_incomplete"


def load_input_directory(input_dir: Path, dataset_kind: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    manifest_path = input_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest is missing: {manifest_path}")

    manifest = read_json_file(manifest_path)
    summary_rows = read_summary_csv(input_dir)
    rows: List[Dict[str, Any]] = []

    for run in manifest.get("runs", []):
        run_id = run.get("run_id", "")
        csv_row = summary_rows.get(run_id, {})
        stats_path_text = first_nonempty(run.get("stats_file"), csv_row.get("stats_file"))
        stats_config, stats_summary, resolved_stats_path, stats_exists = load_stats_metrics(
            str(stats_path_text), input_dir
        )

        row: Dict[str, Any] = {
            "input_dir": input_dir.as_posix(),
            "manifest_file": manifest_path.as_posix(),
            "runner_schema": manifest.get("schema", ""),
            "runner_mode": manifest.get("mode", ""),
            "dataset_kind": dataset_kind,
            "run_id": run_id,
            "status": first_nonempty(run.get("status"), csv_row.get("status")),
            "return_code": normalize_return_code(first_nonempty(run.get("return_code"), csv_row.get("return_code"))),
            "routing": first_nonempty(run.get("routing"), csv_row.get("routing"), stats_config.get("routing_algorithm")),
            "traffic_profile": first_nonempty(run.get("traffic_profile"), csv_row.get("traffic_profile")),
            "traffic_distribution": stats_config.get("traffic_distribution", ""),
            "fault_mask": first_nonempty(run.get("fault_mask"), csv_row.get("fault_mask"), stats_config.get("deft_active_fault_mask")),
            "faulty_vl_ids": first_nonempty(
                stringify_sequence(run.get("faulty_vl_ids")),
                csv_row.get("faulty_vl_ids"),
            ),
            "seed": first_nonempty(run.get("seed"), csv_row.get("seed"), stats_config.get("rnd_generator_seed")),
            "simulation_time_cycles": first_nonempty(
                run.get("simulation_time_cycles"),
                stats_config.get("simulation_time_cycles"),
            ),
            "stats_warm_up_time_cycles": first_nonempty(
                run.get("stats_warm_up_time_cycles"),
                stats_config.get("stats_warm_up_time_cycles"),
            ),
            "stats_file": resolved_stats_path,
            "stats_file_exists": "yes" if stats_exists else "no",
            "stdout_file": resolve_artifact_path(str(run.get("stdout_file", "")), input_dir, "logs")[0],
            "stderr_file": resolve_artifact_path(str(run.get("stderr_file", "")), input_dir, "logs")[0],
            "config_file": str(run.get("config_file", "")),
            "lut_file": resolve_artifact_path(str(run.get("lut_file", "")), input_dir, "luts")[0],
            "lut_provenance": str(run.get("lut_provenance", "")),
            "metrics_source": "json_stats" if stats_summary else ("summary_csv" if csv_row else "missing"),
        }

        for column in METRIC_COLUMNS:
            row[column] = first_nonempty(stats_summary.get(column), csv_row.get(column))

        row["analysis_status"] = classify_row(row)
        rows.append(row)

    return manifest, rows


def unique_ordered(values: Iterable[Any]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        text = str(value)
        if text in seen or text == "":
            continue
        seen.add(text)
        result.append(text)
    return result


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def aggregate_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, str, str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("analysis_status") != "completed_with_metrics":
            continue
        key = (
            str(row.get("routing", "")),
            str(row.get("traffic_profile", "")),
            str(row.get("fault_mask", "")),
            str(row.get("simulation_time_cycles", "")),
            str(row.get("stats_warm_up_time_cycles", "")),
        )
        groups[key].append(row)

    aggregates: List[Dict[str, Any]] = []
    for key, group_rows in sorted(groups.items()):
        routing, traffic_profile, fault_mask, sim_cycles, warmup_cycles = key
        aggregate: Dict[str, Any] = {
            "routing": routing,
            "traffic_profile": traffic_profile,
            "fault_mask": fault_mask,
            "simulation_time_cycles": sim_cycles,
            "stats_warm_up_time_cycles": warmup_cycles,
            "completed_run_count": len(group_rows),
            "unique_seed_count": len(unique_ordered(row.get("seed", "") for row in group_rows)),
            "seeds": ",".join(unique_ordered(row.get("seed", "") for row in group_rows)),
            "input_dirs": ";".join(unique_ordered(row.get("input_dir", "") for row in group_rows)),
        }
        for column in METRIC_COLUMNS:
            values = [to_float(row.get(column)) for row in group_rows]
            numeric_values = [value for value in values if value is not None]
            aggregate[f"mean_{column}"] = fmean(numeric_values) if numeric_values else ""
        aggregates.append(aggregate)

    return aggregates


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def markdown_table(rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str], limit: int = 12) -> List[str]:
    if not rows:
        return ["No rows available."]

    selected_rows = list(rows[:limit])
    lines = [
        "| " + " | ".join(fieldnames) + " |",
        "| " + " | ".join("---" for _ in fieldnames) + " |",
    ]
    for row in selected_rows:
        values = [str(row.get(field, "")).replace("|", "\\|") for field in fieldnames]
        lines.append("| " + " | ".join(values) + " |")
    if len(rows) > limit:
        lines.append(f"\nAdditional rows omitted from this preview: {len(rows) - limit}.")
    return lines


def build_blockers(dataset_kind: str, rows: Sequence[Dict[str, Any]]) -> List[str]:
    blockers: List[str] = []
    if dataset_kind != "final_sweep":
        blockers.append(
            "Blocked: No validated final sweep output set was provided; current inputs are caller-labeled smoke data."
        )
    if not any(row.get("analysis_status") == "completed_with_metrics" for row in rows):
        blockers.append("Blocked: No completed runs with T0020 metrics were found.")
    blockers.append(
        "Blocked: Final fault-rate accounting over physical bidirectional VLs versus directional VLs remains unresolved."
    )
    blockers.append(
        "Blocked: Final simulation window, seed count, and drain policy remain unresolved."
    )
    return blockers


def write_report(
    path: Path,
    manifest: Dict[str, Any],
    rows: Sequence[Dict[str, Any]],
    aggregates: Sequence[Dict[str, Any]],
    run_summary_file: Path,
    comparison_summary_file: Path,
) -> None:
    observed_routings = ", ".join(unique_ordered(row.get("routing", "") for row in rows)) or "None"
    observed_traffic = ", ".join(unique_ordered(row.get("traffic_profile", "") for row in rows)) or "None"
    observed_fault_masks = ", ".join(unique_ordered(row.get("fault_mask", "") for row in rows)) or "None"
    observed_seeds = ", ".join(unique_ordered(row.get("seed", "") for row in rows)) or "None"
    observed_sim_windows = ", ".join(
        unique_ordered(row.get("simulation_time_cycles", "") for row in rows)
    ) or "None"

    lines = [
        "# DeFT Final Analysis Scaffold",
        "",
        f"Generated by `{SCRIPT_NAME}` version `{ANALYZER_VERSION}`.",
        "",
        "Assumption: Input directories were produced by T0021 `deft_experiment_runner.py`, and machine-readable stats files were produced by the T0020 stats export path.",
        "",
        "No performance claims are made by this scaffold.",
        "",
        "## Status",
        "",
    ]
    for blocker in manifest["blockers"]:
        lines.append(f"- {blocker}")

    lines.extend(
        [
            "",
            "## Generated Tables",
            "",
            f"- Run summary CSV: `{run_summary_file.as_posix()}`",
            f"- Comparison summary CSV: `{comparison_summary_file.as_posix()}`",
            f"- Analysis manifest: `{manifest['analysis_manifest_file']}`",
            "",
            "## Observed Coverage",
            "",
            f"- Routing modes: {observed_routings}",
            f"- Traffic profiles: {observed_traffic}",
            f"- Fault masks: {observed_fault_masks}",
            f"- Seeds: {observed_seeds}",
            f"- Simulation windows: {observed_sim_windows}",
            "",
            "## Run Summary Preview",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            rows,
            (
                "run_id",
                "analysis_status",
                "routing",
                "traffic_profile",
                "fault_mask",
                "seed",
                "reachability_ratio",
                "global_average_delay_cycles",
                "network_throughput_flits_per_cycle",
            ),
        )
    )
    lines.extend(["", "## Comparison Summary Preview", ""])
    lines.extend(
        markdown_table(
            aggregates,
            (
                "routing",
                "traffic_profile",
                "fault_mask",
                "completed_run_count",
                "unique_seed_count",
                "mean_reachability_ratio",
                "mean_global_average_delay_cycles",
                "mean_network_throughput_flits_per_cycle",
            ),
        )
    )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Smoke outputs can validate traceability and export shape, but they are not final performance results.",
            "- Short runs can leave packets in flight and therefore can report reachability below one.",
            "- Temporary DEFT LUTs generated by the T0021 runner use the T0016 uniform-unit-interchiplet demand assumption.",
            "- This helper does not update golden regression outputs and does not inspect simulator logs for deadlock conclusions.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    noxim_root = args.noxim_root.resolve()
    input_dirs = [input_dir.resolve() for input_dir in args.input_dir]
    output_dir = resolve_output_dir(noxim_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_manifests: List[Dict[str, Any]] = []
    all_rows: List[Dict[str, Any]] = []
    for input_dir in input_dirs:
        input_manifest, rows = load_input_directory(input_dir, args.dataset_kind)
        input_manifests.append(
            {
                "input_dir": input_dir.as_posix(),
                "schema": input_manifest.get("schema", ""),
                "mode": input_manifest.get("mode", ""),
                "run_count": input_manifest.get("run_count", len(rows)),
                "safety_note": input_manifest.get("safety_note", ""),
            }
        )
        all_rows.extend(rows)

    aggregates = aggregate_rows(all_rows)
    run_summary_file = output_dir / "run_summary.csv"
    comparison_summary_file = output_dir / "comparison_summary.csv"
    report_file = output_dir / "report_scaffold.md"
    analysis_manifest_file = output_dir / "analysis_manifest.json"

    blockers = build_blockers(args.dataset_kind, all_rows)
    analysis_manifest: Dict[str, Any] = {
        "schema": ANALYZER_SCHEMA,
        "analyzer": SCRIPT_NAME,
        "analyzer_version": ANALYZER_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_kind": args.dataset_kind,
        "noxim_root": noxim_root.as_posix(),
        "output_dir": output_dir.as_posix(),
        "analysis_manifest_file": analysis_manifest_file.as_posix(),
        "run_summary_file": run_summary_file.as_posix(),
        "comparison_summary_file": comparison_summary_file.as_posix(),
        "report_scaffold_file": report_file.as_posix(),
        "input_manifests": input_manifests,
        "run_count": len(all_rows),
        "completed_with_metrics_count": sum(
            1 for row in all_rows if row.get("analysis_status") == "completed_with_metrics"
        ),
        "comparison_group_count": len(aggregates),
        "claims_allowed": False,
        "blockers": blockers,
        "notes": [
            "Mechanical aggregation only; no simulation, final sweep definition, or performance claim is performed.",
            f"Expected runner schema is {RUNNER_SCHEMA}; observed schemas are preserved for traceability.",
        ],
    }

    run_summary_columns = [
        "input_dir",
        "manifest_file",
        "runner_schema",
        "runner_mode",
        "dataset_kind",
        "run_id",
        "analysis_status",
        "status",
        "return_code",
        "routing",
        "traffic_profile",
        "traffic_distribution",
        "fault_mask",
        "faulty_vl_ids",
        "seed",
        "simulation_time_cycles",
        "stats_warm_up_time_cycles",
        "metrics_source",
        "stats_file_exists",
        "stats_file",
        "stdout_file",
        "stderr_file",
        "config_file",
        "lut_file",
        "lut_provenance",
    ] + list(METRIC_COLUMNS)

    comparison_columns = [
        "routing",
        "traffic_profile",
        "fault_mask",
        "simulation_time_cycles",
        "stats_warm_up_time_cycles",
        "completed_run_count",
        "unique_seed_count",
        "seeds",
        "input_dirs",
    ] + [f"mean_{column}" for column in METRIC_COLUMNS]

    write_csv(run_summary_file, all_rows, run_summary_columns)
    write_csv(comparison_summary_file, aggregates, comparison_columns)
    analysis_manifest_file.write_text(
        json.dumps(analysis_manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_report(
        report_file,
        analysis_manifest,
        all_rows,
        aggregates,
        run_summary_file,
        comparison_summary_file,
    )

    print(f"inputs: {len(input_dirs)}")
    print(f"runs: {len(all_rows)}")
    print(f"completed_with_metrics: {analysis_manifest['completed_with_metrics_count']}")
    print(f"output: {output_dir}")
    print(f"report: {report_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
