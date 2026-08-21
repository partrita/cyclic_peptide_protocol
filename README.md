# Cyclic peptide design: ProteinMPNN + ESMFold2

This repository is a modern, minimal rewrite of the old C05/Rosetta protocol.

The workflow is:

1. Start from a **pre-built cyclic-peptide backbone** in PDB format.
2. Use the official **ProteinMPNN** implementation to design amino-acid sequences for that backbone.
3. Fold each designed sequence with **ESMFold2**.
4. Score the predictions using mean pLDDT and the head-to-tail peptide-bond distance.

The old Rosetta XML/flags, Amber/tleap scripts, MD scripts, PyEMMA analysis, and generated trajectory tooling are intentionally removed from the main workflow. The historical protocol PDF is kept under `docs/archive/`.

## Repository layout

```text
.
├── configs/
│   └── example.yaml
├── docs/
│   ├── WORKFLOW.md
│   └── archive/
│       └── Protocol_capture.pdf
├── examples/
│   └── input/
│       └── c05_cyclic_backbone.pdb
├── scripts/
│   ├── design_with_proteinmpnn.py
│   ├── fold_with_esmfold2.py
│   └── evaluate_cyclic_predictions.py
├── pyproject.toml
└── README.md
```

## 1. Install

ProteinMPNN and ESMFold2 are intentionally external model repositories rather than vendored into this example.

```bash
git clone https://github.com/dauparas/ProteinMPNN.git external/ProteinMPNN
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install pyyaml gemmi torch transformers
pip install "esm @ git+https://github.com/Biohub/esm.git@main"
```

ProteinMPNN's official implementation exposes `protein_mpnn_run.py` and supports a single input PDB with `--pdb_path` and `--pdb_path_chains`. citeturn960788search0

ESMFold2's current local workflow uses `ESMFold2Model` plus `ESMFold2InputBuilder`; the model can write an mmCIF structure from the resulting molecular complex. citeturn457844search0turn206872search3

## 2. Design sequences with ProteinMPNN

```bash
python scripts/design_with_proteinmpnn.py \
  --protein-mpnn external/ProteinMPNN \
  --backbone examples/input/c05_cyclic_backbone.pdb \
  --output-dir outputs/mpnn \
  --num-sequences 32 \
  --temperature 0.1 \
  --seed 42
```

The wrapper calls the upstream `protein_mpnn_run.py` directly and leaves its generated FASTA files in `outputs/mpnn/seqs/`.

ProteinMPNN designs the sequence from the supplied backbone coordinates. It does not create a new backbone or perform Rosetta-style relaxation; the cyclic geometry therefore needs to be present in the input PDB before sequence design. This is deliberate: sequence design and structure prediction are kept as separate, inspectable stages. citeturn960788search0

## 3. Fold designed sequences with ESMFold2

```bash
python scripts/fold_with_esmfold2.py \
  --model biohub/ESMFold2-Fast \
  --fasta outputs/mpnn/seqs/seqs/c05_cyclic_backbone.fa \
  --output-dir outputs/esmfold2 \
  --num-loops 3 \
  --num-sampling-steps 50 \
  --num-diffusion-samples 1
```

The current ESMFold2 stack supports `StructurePredictionInput` and explicit `CovalentBond` objects, so the example can tell the model that the peptide is cyclic instead of pretending that the terminal residues are an ordinary open chain. citeturn206872search2turn206872search4

The example encodes the normal cyclic peptide closure as:

```text
chain A, residue 0, atom N  <->  chain A, last residue, atom C
```

For standard protein residues in ESMFold2, the backbone heavy-atom order starts with N, CA, C, O, so the example uses atom indices 0 and 2 for the closure bond. citeturn171300search0

## 4. Evaluate the folds

```bash
python scripts/evaluate_cyclic_predictions.py \
  --input-dir outputs/esmfold2 \
  --json outputs/esmfold2/summary.json
```

The evaluator reports:

- mean pLDDT when present in the ESMFold2 result,
- terminal N–C distance for the cyclic peptide bond,
- a simple pass/fail closure flag (`<= 2.0 Å` by default).

A good closure distance is a geometry check, not a guarantee of biological activity or experimental success. For real design campaigns, inspect the structures and use an independent validation pipeline as well.

## Design notes

The original repository mixed Rosetta cyclization, resfile editing, constrained relaxation, molecular dynamics, trajectory analysis, and one-off shell utilities in the repository root. The rewrite intentionally removes those legacy steps instead of preserving two competing workflows.

The recommended modern loop is:

```text
cyclic backbone
      │
      ▼
ProteinMPNN
      │  many sequences
      ▼
ESMFold2 (+ cyclic bond)
      │
      ├── confidence
      ├── head-to-tail closure
      └── manual/independent structural review
```

For a large campaign, keep the backbone set immutable, record the random seed and MPNN temperature, and save every generated sequence together with the ESMFold2 configuration used to score it.
