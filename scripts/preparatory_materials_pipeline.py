"""Run the full preparatory materials pipeline: discover → download → extract → digest.

Executes all four steps in sequence using subprocess. Individual steps can be
skipped via --skip-* flags.

Usage:
    uv run python -m scripts.preparatory_materials_pipeline
    uv run python -m scripts.preparatory_materials_pipeline --law BGFA
    uv run python -m scripts.preparatory_materials_pipeline --law OR --max-budget 100
    uv run python -m scripts.preparatory_materials_pipeline --skip-discover --skip-download
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def run_step(name: str, cmd: list[str]) -> bool:
    """Run a subprocess step and return True on success."""
    print(f"\n{'='*60}")
    print(f"STEP: {name}")
    print(f"CMD:  {' '.join(cmd)}")
    print("=" * 60)

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\nERROR: Step '{name}' failed with exit code {result.returncode}.")
        return False

    print(f"\nOK: Step '{name}' completed successfully.")
    return True


def main() -> None:
    """Parse arguments and run the pipeline steps in sequence."""
    parser = argparse.ArgumentParser(
        description="Run the full preparatory materials pipeline",
    )
    parser.add_argument(
        "--law",
        help="Law abbreviation to process (e.g. BGFA). If omitted, all laws are processed.",
    )
    parser.add_argument(
        "--max-budget",
        type=float,
        default=50.0,
        help="Maximum spend in USD for the digest step (default: 50.0)",
    )
    parser.add_argument(
        "--skip-discover",
        action="store_true",
        help="Skip the discover step",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip the download step",
    )
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="Skip the extract step",
    )
    args = parser.parse_args()

    python = sys.executable
    steps_run = 0
    steps_failed = 0

    # Step 1: Discover
    if not args.skip_discover:
        cmd = [python, "-m", "scripts.discover_botschaften"]
        if not run_step("discover", cmd):
            steps_failed += 1
            print("Aborting pipeline due to discover failure.")
            sys.exit(1)
        steps_run += 1
    else:
        print("SKIP: discover")

    # Step 2: Download
    if not args.skip_download:
        cmd = [python, "-m", "scripts.download_botschaften"]
        if not run_step("download", cmd):
            steps_failed += 1
            print("Aborting pipeline due to download failure.")
            sys.exit(1)
        steps_run += 1
    else:
        print("SKIP: download")

    # Step 3: Extract
    if not args.skip_extract:
        cmd = [python, "-m", "scripts.extract_botschaften"]
        if not run_step("extract", cmd):
            steps_failed += 1
            print("Aborting pipeline due to extract failure.")
            sys.exit(1)
        steps_run += 1
    else:
        print("SKIP: extract")

    # Step 4: Digest (requires --law)
    if args.law:
        cmd = [
            python, "-m", "scripts.digest_botschaften",
            "--law", args.law,
            "--max-budget", str(args.max_budget),
        ]
        if not run_step("digest", cmd):
            steps_failed += 1
            sys.exit(1)
        steps_run += 1
    else:
        print(
            "\nNOTE: Skipping digest step (no --law specified). "
            "Run with --law <LAW> to also digest Botschaften per article."
        )

    print(f"\n{'='*60}")
    print(f"Pipeline complete: {steps_run} step(s) run, {steps_failed} failed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
