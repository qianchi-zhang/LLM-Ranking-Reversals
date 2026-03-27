from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the standardized LLM-Ranking-Reversals pipeline from Phase 1 to Phase 4. "
            "Phase 2-related options are forwarded to src/02_api_runner.py."
        )
    )
    parser.add_argument("--start-phase", type=int, choices=range(1, 5), default=1)
    parser.add_argument("--end-phase", type=int, choices=range(1, 5), default=4)
    parser.add_argument(
        "--skip-mmlu-subject-bootstrap",
        action="store_true",
        help="Skip src/04_mmlu_subject_bootstrap.py when Phase 4 is included.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them.",
    )

    # Phase 2 passthrough options
    parser.add_argument("--mode", choices=["pilot", "full"], default="full")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--input-file", type=Path, default=None)
    parser.add_argument("--output-jsonl", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--sleep-seconds", type=float, default=None)
    parser.add_argument("--models", nargs="+", default=None)
    return parser.parse_args()


def build_phase2_command(args: argparse.Namespace) -> list[str]:
    command = [sys.executable, str(SRC_DIR / "02_api_runner.py"), "--mode", args.mode]

    if args.limit is not None:
        command.extend(["--limit", str(args.limit)])
    if args.resume:
        command.append("--resume")
    if args.overwrite:
        command.append("--overwrite")
    if args.input_file is not None:
        command.extend(["--input-file", str(args.input_file)])
    if args.output_jsonl is not None:
        command.extend(["--output-jsonl", str(args.output_jsonl)])
    if args.output_csv is not None:
        command.extend(["--output-csv", str(args.output_csv)])
    if args.env_file is not None:
        command.extend(["--env-file", str(args.env_file)])
    if args.sleep_seconds is not None:
        command.extend(["--sleep-seconds", str(args.sleep_seconds)])
    if args.models:
        command.extend(["--models", *args.models])

    return command


def build_steps(args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    if args.start_phase > args.end_phase:
        raise ValueError("--start-phase cannot be greater than --end-phase.")

    steps: list[tuple[str, list[str]]] = []

    for phase in range(args.start_phase, args.end_phase + 1):
        if phase == 1:
            steps.append(("Phase 1: data preparation", [sys.executable, str(SRC_DIR / "01_data_prep.py")]))
        elif phase == 2:
            steps.append(("Phase 2: API runner", build_phase2_command(args)))
        elif phase == 3:
            steps.append(("Phase 3: scoring", [sys.executable, str(SRC_DIR / "03_scorer.py")]))
        elif phase == 4:
            steps.append(("Phase 4: main analysis", [sys.executable, str(SRC_DIR / "04_analysis.py")]))
            if not args.skip_mmlu_subject_bootstrap:
                steps.append(
                    (
                        "Phase 4: MMLU subject bootstrap",
                        [sys.executable, str(SRC_DIR / "04_mmlu_subject_bootstrap.py")],
                    )
                )

    return steps


def run_step(step_name: str, command: list[str], dry_run: bool) -> None:
    print(f"\n=== {step_name} ===")
    print(subprocess.list2cmdline(command))

    if dry_run:
        return

    subprocess.run(command, cwd=ROOT_DIR, check=True)


def main() -> None:
    args = parse_args()
    steps = build_steps(args)

    print(f"Working directory: {ROOT_DIR}")
    print(f"Selected phase range: {args.start_phase} -> {args.end_phase}")
    print(f"Dry run: {'yes' if args.dry_run else 'no'}")

    for step_name, command in steps:
        run_step(step_name, command, args.dry_run)

    print("\nPipeline finished.")


if __name__ == "__main__":
    main()
