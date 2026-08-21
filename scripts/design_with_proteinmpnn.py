from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Design a cyclic-peptide backbone with ProteinMPNN.")
    parser.add_argument("--protein-mpnn", required=True, type=pathlib.Path)
    parser.add_argument("--backbone", required=True, type=pathlib.Path)
    parser.add_argument("--output-dir", required=True, type=pathlib.Path)
    parser.add_argument("--num-sequences", type=int, default=32)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--chain", default="A")
    args = parser.parse_args()

    run_script = args.protein_mpnn / "protein_mpnn_run.py"
    if not run_script.is_file():
        raise SystemExit(f"ProteinMPNN entry point not found: {run_script}")
    if not args.backbone.is_file():
        raise SystemExit(f"Backbone PDB not found: {args.backbone}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(run_script),
        "--pdb_path", str(args.backbone.resolve()),
        "--pdb_path_chains", args.chain,
        "--out_folder", str(args.output_dir.resolve()),
        "--num_seq_per_target", str(args.num_sequences),
        "--sampling_temp", str(args.temperature),
        "--batch_size", str(args.batch_size),
        "--seed", str(args.seed),
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=args.protein_mpnn, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
