#!/usr/bin/env python3
"""
Launch traceable tiny DeFT/XY experiment runs.

This runner is intentionally small. It builds Noxim command lines from the
existing DEFT_2_5D traffic configs, existing fault CLI switches, the T0016 LUT
generator, and the T0020 stats export path. It does not define a final sweep or
claim experiment results.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


SCRIPT_NAME = "deft_experiment_runner.py"
RUNNER_VERSION = "1"
FAULT_MASK_WIDTH = 4
VERTICAL_LINK_COUNT = 16
VERTICAL_LINKS_PER_CHIPLET = 4
CHIPLET_COUNT = 4
DEFAULT_LUT_TRAFFIC_PROFILE_ID = "t0021-runner-uniform-interchiplet"

TRAFFIC_PROFILES = {
    "uniform": "config_examples/deft_2_5d_traffic_uniform.yaml",
    "localized_40": "config_examples/deft_2_5d_traffic_localized_40.yaml",
    "hotspot_3x10": "config_examples/deft_2_5d_traffic_hotspot_3x10.yaml",
}

FAULT_PRESETS = {
    "none": 0x0000,
    "physical_25": 0x1111,
}

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


def default_noxim_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_fault_mask(value: str) -> int:
    try:
        mask = int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid fault mask: {value}") from exc

    if mask < 0 or mask >= (1 << VERTICAL_LINK_COUNT):
        raise argparse.ArgumentTypeError(
            f"fault mask must fit {VERTICAL_LINK_COUNT} physical VL bits"
        )
    try:
        validate_fault_mask(mask)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return mask


def validate_fault_mask(mask: int) -> None:
    faults_per_chiplet = [0 for _ in range(CHIPLET_COUNT)]
    for vl_id in faulty_vl_ids(mask):
        faults_per_chiplet[vl_id // VERTICAL_LINKS_PER_CHIPLET] += 1

    for chiplet_id, fault_count in enumerate(faults_per_chiplet):
        if fault_count >= VERTICAL_LINKS_PER_CHIPLET:
            raise ValueError(
                f"fault mask {format_fault_mask(mask)} disconnects chiplet {chiplet_id}"
            )


def faulty_vl_ids(mask: int) -> List[int]:
    return [vl_id for vl_id in range(VERTICAL_LINK_COUNT) if mask & (1 << vl_id)]


def format_fault_mask(mask: int) -> str:
    return f"0x{mask:0{FAULT_MASK_WIDTH}x}"


def unique_ordered(values: Iterable[Any]) -> List[Any]:
    result: List[Any] = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def command_path(path: Path, cwd: Path) -> str:
    try:
        relpath = os.path.relpath(path, cwd)
    except ValueError:
        return path.as_posix()
    return Path(relpath).as_posix()


def shell_join(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def command_text(command: Sequence[str], cwd: Path, env_prefix: Dict[str, str] | None = None) -> str:
    env_parts = []
    for key, value in sorted((env_prefix or {}).items()):
        if value:
            env_parts.append(f"{key}={shlex.quote(value)}")
    prefix = " ".join(env_parts)
    joined = shell_join(command)
    if prefix:
        joined = f"{prefix} {joined}"
    return f"(cd {shlex.quote(cwd.as_posix())} && {joined})"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create or execute tiny traceable DEFT_2_5D experiment runs using "
            "existing Noxim configs and stats export."
        )
    )
    parser.add_argument(
        "--noxim-root",
        type=Path,
        default=default_noxim_root(),
        help="Noxim repository root. Defaults to the parent of this script's directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "Directory for generated manifests, stats, logs, and temporary LUTs. "
            "Defaults to other/generated/deft_experiments/<timestamp> under Noxim."
        ),
    )
    parser.add_argument(
        "--routing",
        action="append",
        choices=("XY", "DEFT"),
        help="Routing mode to include. May be repeated. Default: XY.",
    )
    parser.add_argument(
        "--traffic",
        action="append",
        choices=tuple(TRAFFIC_PROFILES.keys()),
        help="Traffic profile to include. May be repeated. Default: localized_40.",
    )
    parser.add_argument(
        "--fault-mask",
        action="append",
        type=parse_fault_mask,
        help="Physical VL fault mask such as 0x0000 or 0x1111. May be repeated.",
    )
    parser.add_argument(
        "--fault-preset",
        action="append",
        choices=tuple(FAULT_PRESETS.keys()),
        help="Named fault setting. May be repeated. Defaults to none when no mask is supplied.",
    )
    parser.add_argument(
        "--seed",
        action="append",
        type=int,
        help="Random seed. May be repeated. Default: 0.",
    )
    parser.add_argument(
        "--sim",
        type=int,
        default=20,
        help="Simulation cycles passed to -sim. Default: 20.",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=0,
        help="Stats warm-up cycles passed to -warmup. Default: 0.",
    )
    parser.add_argument(
        "--stats-format",
        choices=("json", "csv"),
        default="json",
        help="Machine-readable stats export format. Default: json.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute planned runs. Without this flag the runner records a dry-run plan only.",
    )
    parser.add_argument(
        "--max-execute-runs",
        type=int,
        default=4,
        help="Safety cap for --execute. Default: 4.",
    )
    return parser


def resolve_output_dir(noxim_root: Path, requested: Path | None) -> Path:
    if requested is not None:
        return requested.resolve()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return noxim_root / "other" / "generated" / "deft_experiments" / timestamp


def selected_fault_masks(args: argparse.Namespace) -> List[int]:
    masks: List[int] = []
    for preset in args.fault_preset or []:
        masks.append(FAULT_PRESETS[preset])
    masks.extend(args.fault_mask or [])
    if not masks:
        masks.append(FAULT_PRESETS["none"])
    return unique_ordered(masks)


def build_runs(args: argparse.Namespace, noxim_root: Path, output_dir: Path) -> List[Dict[str, Any]]:
    routings = args.routing or ["XY"]
    traffics = args.traffic or ["localized_40"]
    fault_masks = selected_fault_masks(args)
    seeds = args.seed or [0]

    bin_dir = noxim_root / "bin"
    stats_dir = output_dir / "stats"
    logs_dir = output_dir / "logs"
    lut_dir = output_dir / "luts"

    runs: List[Dict[str, Any]] = []
    run_index = 1
    for routing in routings:
        for traffic in traffics:
            for fault_mask in fault_masks:
                for seed in seeds:
                    mask_id = format_fault_mask(fault_mask)
                    run_id = (
                        f"{run_index:03d}_{routing.lower()}_{traffic}_fault{mask_id}_seed{seed}"
                    )
                    config_path = noxim_root / TRAFFIC_PROFILES[traffic]
                    stats_suffix = "json" if args.stats_format == "json" else "csv"
                    stats_path = stats_dir / f"{run_id}.{stats_suffix}"
                    stdout_path = logs_dir / f"{run_id}.stdout.txt"
                    stderr_path = logs_dir / f"{run_id}.stderr.txt"
                    command = [
                        "./noxim",
                        "-config",
                        command_path(config_path, bin_dir),
                        "-seed",
                        str(seed),
                        "-sim",
                        str(args.sim),
                        "-warmup",
                        str(args.warmup),
                        "-routing",
                        routing,
                        "-stats_format",
                        args.stats_format,
                        "-stats_file",
                        command_path(stats_path, bin_dir),
                    ]

                    faulty_ids = faulty_vl_ids(fault_mask)
                    if faulty_ids:
                        command.extend(["-deft_faulty_vls", ",".join(str(vl_id) for vl_id in faulty_ids)])

                    lut_path = None
                    lut_command = None
                    if routing == "DEFT":
                        lut_path = lut_dir / f"deft_vl_lut_{mask_id}.yaml"
                        generator_path = noxim_root / "other" / "deft_vl_lut_generator.py"
                        lut_command = [
                            sys.executable,
                            command_path(generator_path, noxim_root),
                            "--fault-mask",
                            mask_id,
                            "--traffic-profile-id",
                            DEFAULT_LUT_TRAFFIC_PROFILE_ID,
                            "--output",
                            command_path(lut_path, noxim_root),
                        ]
                        command.extend(["-deft_vl_lut", command_path(lut_path, bin_dir)])

                    runs.append(
                        {
                            "run_id": run_id,
                            "index": run_index,
                            "routing": routing,
                            "traffic_profile": traffic,
                            "config_file": command_path(config_path, noxim_root),
                            "fault_mask": mask_id,
                            "faulty_vl_ids": faulty_ids,
                            "seed": seed,
                            "simulation_time_cycles": args.sim,
                            "stats_warm_up_time_cycles": args.warmup,
                            "stats_format": args.stats_format,
                            "stats_file": stats_path.as_posix(),
                            "stdout_file": stdout_path.as_posix(),
                            "stderr_file": stderr_path.as_posix(),
                            "lut_file": lut_path.as_posix() if lut_path else "",
                            "lut_provenance": (
                                "Generated by T0016 deft_vl_lut_generator.py with "
                                "uniform_unit_interchiplet_demand assumption"
                                if lut_path
                                else ""
                            ),
                            "lut_generator_cwd": noxim_root.as_posix() if lut_command else "",
                            "lut_generator_command": lut_command or [],
                            "simulator_cwd": bin_dir.as_posix(),
                            "simulator_command": command,
                            "status": "planned",
                            "return_code": None,
                        }
                    )
                    run_index += 1

    return runs


def ld_library_env(noxim_root: Path) -> Dict[str, str]:
    library_dir = noxim_root / "bin" / "libs" / "systemc-2.3.1" / "lib-linux64"
    if not library_dir.exists():
        return {}
    return {"LD_LIBRARY_PATH": library_dir.as_posix()}


def write_commands_file(path: Path, runs: Sequence[Dict[str, Any]], noxim_root: Path) -> None:
    env_prefix = ld_library_env(noxim_root)
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        f"# Generated by {SCRIPT_NAME} v{RUNNER_VERSION}",
        "# These commands are intentionally tiny-run launch commands, not a final sweep.",
        "",
    ]

    emitted_lut_commands = set()
    for run in runs:
        lut_command = run["lut_generator_command"]
        if lut_command:
            key = tuple(lut_command)
            if key not in emitted_lut_commands:
                lines.append(command_text(lut_command, noxim_root))
                emitted_lut_commands.add(key)
        lines.append(command_text(run["simulator_command"], Path(run["simulator_cwd"]), env_prefix))
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def read_metrics(run: Dict[str, Any]) -> Dict[str, Any]:
    if run["stats_format"] != "json":
        return {}

    stats_path = Path(run["stats_file"])
    if not stats_path.exists():
        return {}

    data = json.loads(stats_path.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    return {column: summary.get(column, "") for column in METRIC_COLUMNS}


def write_summary_csv(path: Path, runs: Sequence[Dict[str, Any]]) -> None:
    columns = [
        "run_id",
        "status",
        "return_code",
        "routing",
        "traffic_profile",
        "fault_mask",
        "faulty_vl_ids",
        "seed",
        "stats_file",
    ] + list(METRIC_COLUMNS)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for run in runs:
            metrics = read_metrics(run)
            row = {
                "run_id": run["run_id"],
                "status": run["status"],
                "return_code": run["return_code"],
                "routing": run["routing"],
                "traffic_profile": run["traffic_profile"],
                "fault_mask": run["fault_mask"],
                "faulty_vl_ids": ",".join(str(vl_id) for vl_id in run["faulty_vl_ids"]),
                "seed": run["seed"],
                "stats_file": run["stats_file"],
            }
            row.update(metrics)
            writer.writerow(row)


def write_manifest(path: Path, manifest: Dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")


def ensure_execute_environment(noxim_root: Path, runs: Sequence[Dict[str, Any]]) -> None:
    if os.name == "nt":
        raise RuntimeError("--execute must be run from WSL/Linux because bin/noxim is a Linux ELF binary")

    noxim_binary = noxim_root / "bin" / "noxim"
    if not noxim_binary.exists():
        raise RuntimeError(f"Noxim binary is missing: {noxim_binary}")
    if not os.access(noxim_binary, os.X_OK):
        raise RuntimeError(f"Noxim binary is not executable: {noxim_binary}")

    for run in runs:
        config_path = noxim_root / run["config_file"]
        if not config_path.exists():
            raise RuntimeError(f"config file is missing: {config_path}")


def execute_runs(runs: Sequence[Dict[str, Any]], noxim_root: Path) -> int:
    env_prefix = ld_library_env(noxim_root)
    env = os.environ.copy()
    if env_prefix:
        current = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = (
            env_prefix["LD_LIBRARY_PATH"]
            if not current
            else env_prefix["LD_LIBRARY_PATH"] + os.pathsep + current
        )

    generated_luts = set()
    failed = False
    for run in runs:
        Path(run["stdout_file"]).parent.mkdir(parents=True, exist_ok=True)
        Path(run["stderr_file"]).parent.mkdir(parents=True, exist_ok=True)

        lut_command = run["lut_generator_command"]
        if lut_command:
            lut_key = tuple(lut_command)
            if lut_key not in generated_luts:
                completed_lut = subprocess.run(
                    lut_command,
                    cwd=noxim_root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                generated_luts.add(lut_key)
                if completed_lut.returncode != 0:
                    run["status"] = "lut_failed"
                    run["return_code"] = completed_lut.returncode
                    Path(run["stdout_file"]).write_text(completed_lut.stdout, encoding="utf-8", newline="\n")
                    Path(run["stderr_file"]).write_text(completed_lut.stderr, encoding="utf-8", newline="\n")
                    failed = True
                    continue

        completed = subprocess.run(
            run["simulator_command"],
            cwd=Path(run["simulator_cwd"]),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        Path(run["stdout_file"]).write_text(completed.stdout, encoding="utf-8", newline="\n")
        Path(run["stderr_file"]).write_text(completed.stderr, encoding="utf-8", newline="\n")
        run["return_code"] = completed.returncode
        run["status"] = "completed" if completed.returncode == 0 else "failed"
        failed = failed or completed.returncode != 0

    return 1 if failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if args.sim < 0:
        parser.error("--sim must be >= 0")
    if args.warmup < 0:
        parser.error("--warmup must be >= 0")
    if args.max_execute_runs < 1:
        parser.error("--max-execute-runs must be >= 1")

    noxim_root = args.noxim_root.resolve()
    output_dir = resolve_output_dir(noxim_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "stats").mkdir(parents=True, exist_ok=True)
    (output_dir / "logs").mkdir(parents=True, exist_ok=True)
    (output_dir / "luts").mkdir(parents=True, exist_ok=True)

    runs = build_runs(args, noxim_root, output_dir)
    if args.execute and len(runs) > args.max_execute_runs:
        parser.error(
            f"refusing to execute {len(runs)} runs; raise --max-execute-runs for a deliberate tiny batch"
        )

    commands_file = output_dir / "commands.sh"
    manifest_file = output_dir / "manifest.json"
    summary_file = output_dir / "summary.csv"

    manifest: Dict[str, Any] = {
        "schema": "deft_experiment_runner.v1",
        "runner": SCRIPT_NAME,
        "runner_version": RUNNER_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "execute" if args.execute else "dry_run",
        "noxim_root": noxim_root.as_posix(),
        "output_dir": output_dir.as_posix(),
        "commands_file": commands_file.as_posix(),
        "summary_file": summary_file.as_posix(),
        "run_count": len(runs),
        "safety_note": (
            "T0021 runner supports single-run and tiny dry-run comparisons only; "
            "it is not a final sweep or performance analysis artifact."
        ),
        "runs": runs,
    }

    write_commands_file(commands_file, runs, noxim_root)
    write_manifest(manifest_file, manifest)

    exit_code = 0
    if args.execute:
        try:
            ensure_execute_environment(noxim_root, runs)
            exit_code = execute_runs(runs, noxim_root)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            exit_code = 2
            for run in runs:
                run["status"] = "blocked"
        manifest["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["runs"] = runs
        write_manifest(manifest_file, manifest)

    write_summary_csv(summary_file, runs)

    print(f"mode: {manifest['mode']}")
    print(f"runs: {len(runs)}")
    print(f"manifest: {manifest_file}")
    print(f"commands: {commands_file}")
    print(f"summary: {summary_file}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
