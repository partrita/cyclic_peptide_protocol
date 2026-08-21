from __future__ import annotations

import argparse
import pathlib

import torch
from esm.models.esmfold2 import (
    CovalentBond,
    ESMFold2InputBuilder,
    ProteinInput,
    StructurePredictionInput,
)
from transformers.models.esmfold2.modeling_esmfold2 import ESMFold2Model


def read_fasta(path: pathlib.Path):
    name = None
    seq = []
    with path.open() as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if name is not None:
                    yield name, "".join(seq)
                name = line[1:].split()[0]
                seq = []
            else:
                seq.append(line)
    if name is not None:
        yield name, "".join(seq)


def fold_one(model, sequence: str, seed: int, loops: int, steps: int, samples: int):
    n = len(sequence)
    spi = StructurePredictionInput(
        sequences=[ProteinInput(id="A", sequence=sequence)],
        covalent_bonds=[
            CovalentBond(
                chain_id1="A",
                res_idx1=0,
                atom_idx1=0,  # N
                chain_id2="A",
                res_idx2=n - 1,
                atom_idx2=2,  # C
            )
        ],
    )
    return ESMFold2InputBuilder().fold(
        model,
        spi,
        num_loops=loops,
        num_sampling_steps=steps,
        num_diffusion_samples=samples,
        seed=seed,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Fold ProteinMPNN sequences with ESMFold2.")
    parser.add_argument("--model", default="biohub/ESMFold2-Fast")
    parser.add_argument("--fasta", required=True, type=pathlib.Path)
    parser.add_argument("--output-dir", required=True, type=pathlib.Path)
    parser.add_argument("--num-loops", type=int, default=3)
    parser.add_argument("--num-sampling-steps", type=int, default=50)
    parser.add_argument("--num-diffusion-samples", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cpu", action="store_true")
    args = parser.parse_args()

    device = "cpu" if args.cpu or not torch.cuda.is_available() else "cuda"
    model = ESMFold2Model.from_pretrained(args.model).to(device).eval()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for name, sequence in read_fasta(args.fasta):
        if not sequence:
            continue
        result = fold_one(
            model,
            sequence,
            args.seed,
            args.num_loops,
            args.num_sampling_steps,
            args.num_diffusion_samples,
        )
        out = args.output_dir / f"{name}.cif"
        out.write_text(result.complex.to_mmcif())
        mean_plddt = float(result.plddt.mean())
        print(f"{name}: length={len(sequence)} mean_pLDDT={mean_plddt:.3f} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
