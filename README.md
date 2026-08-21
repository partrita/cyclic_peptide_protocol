# Cyclic Peptide Design with ProteinMPNN + ESMFold2

This repository is a modernized example for designing and screening cyclic peptides from a supplied cyclic backbone. The original repository captured a 2020 Rosetta-centered protocol; the active workflow has been replaced with a smaller, easier-to-follow pipeline based on **ProteinMPNN** for sequence design and **ESMFold2** for structure prediction.

The current workflow is:

```text
cyclic backbone PDB
        │
        ▼
   ProteinMPNN
        │
        │ candidate sequences
        ▼
     ESMFold2
        │
        │ predicted structures
        ▼
 cyclic-closure + confidence checks
```

This repository is intended as a **design and triage example**, not as a claim of experimental validation. A short terminal distance or high model confidence does not establish binding, stability, permeability, or biological activity.

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

Legacy Rosetta XML/flags/resfiles, Amber/tleap setup, molecular-dynamics scripts, PyEMMA analysis, and generated trajectory utilities are no longer part of the active example. The historical protocol is retained only as an archived reference under `docs/archive/`.

## Requirements

The example expects a working Python environment with PyTorch and the dependencies used by the wrapper scripts. ProteinMPNN and ESMFold2 are kept as external projects rather than vendored into this repository.

### ProteinMPNN

Clone the upstream ProteinMPNN repository next to this repository:

```bash
git clone https://github.com/dauparas/ProteinMPNN.git external/ProteinMPNN
```

ProteinMPNN provides the `protein_mpnn_run.py` command used by `scripts/design_with_proteinmpnn.py`.

### ESMFold2

Install the current Biohub ESM package so that the local ESMFold2 API is available:

```bash
pip install "esm @ git+https://github.com/Biohub/esm.git@main"
```

The exact model weights and runtime requirements depend on the ESMFold2 model variant you select. The wrapper accepts a model identifier rather than downloading or vendoring model weights into this repository.

## 1. Start from a cyclic backbone

The example input is:

```text
examples/input/c05_cyclic_backbone.pdb
```

The backbone must already contain the intended cyclic geometry. ProteinMPNN designs amino-acid identities from the supplied coordinates; it does not create a cyclic backbone or perform Rosetta-style relaxation.

For a new design campaign, replace the example PDB with your own cyclic backbone and keep the geometry fixed while generating sequence variants.

## 2. Design sequences with ProteinMPNN

Run the repository wrapper rather than invoking ProteinMPNN's Python entry point manually:

```bash
python scripts/design_with_proteinmpnn.py \
  --protein-mpnn external/ProteinMPNN \
  --backbone examples/input/c05_cyclic_backbone.pdb \
  --output-dir outputs/mpnn \
  --num-sequences 32 \
  --temperature 0.1 \
  --seed 42
```

The wrapper forwards the backbone and design parameters to the upstream `protein_mpnn_run.py` interface and preserves the generated FASTA files under `outputs/mpnn/`.

Recommended practice for a campaign is to record:

- backbone file and checksum,
- ProteinMPNN commit/version,
- random seed,
- sampling temperature,
- number of sequences requested.

These values determine the reproducibility of the sequence-design stage.

## 3. Predict structures with ESMFold2

Fold the generated sequences with ESMFold2:

```bash
python scripts/fold_with_esmfold2.py \
  --model biohub/ESMFold2-Fast \
  --fasta outputs/mpnn/seqs/seqs/c05_cyclic_backbone.fa \
  --output-dir outputs/esmfold2 \
  --num-loops 3 \
  --num-sampling-steps 50 \
  --num-diffusion-samples 1
```

The wrapper uses the current local ESMFold2 input API and represents the cyclic peptide closure explicitly with a `CovalentBond` between the terminal backbone atoms:

```text
N of residue 1  <->  C of the final residue
```

This is preferable to treating the sequence as an ordinary open-chain peptide when the purpose of the prediction is to inspect a cyclic topology.

The output directory contains the predicted structures and metadata needed by the evaluation step.

## 4. Evaluate cyclic closure and confidence

Run:

```bash
python scripts/evaluate_cyclic_predictions.py \
  --input-dir outputs/esmfold2 \
  --json outputs/esmfold2/summary.json
```

The evaluator reports, where available:

- mean pLDDT,
- terminal backbone N–C distance,
- a simple cyclic-closure pass/fail flag.

The default closure threshold is intentionally conservative as a **screening heuristic**, not a physical acceptance criterion. Inspect individual structures rather than ranking candidates from one scalar alone.

## Suggested screening workflow

For a small design set:

```text
1. Build or select a cyclic backbone
2. Generate sequence diversity with ProteinMPNN
3. Predict each sequence with ESMFold2
4. Reject obviously poor folds
5. Check head-to-tail closure geometry
6. Inspect top candidates manually
7. Apply an independent structural/energetic validation pipeline
```

For larger campaigns, keep the backbone set immutable, save every generated FASTA sequence, and store the exact ProteinMPNN and ESMFold2 configuration used for each prediction.

## Configuration

`configs/example.yaml` contains the parameters used by the example. It is intentionally small so that the design choices are visible rather than hidden inside a large workflow framework.

## Historical protocol

The archived PDF in `docs/archive/` documents the original C05 cyclic-peptide protocol described in the historical literature. It is retained for provenance and comparison only; it is **not** the recommended implementation for this repository.

## Limitations

The current example deliberately stops at sequence design, structure prediction, and basic screening. It does not claim to replace:

- experimental synthesis and characterization,
- independent molecular mechanics or free-energy calculations,
- explicit-solvent molecular dynamics,
- receptor-binding or functional assays.

Those tools can be added downstream when a project requires them, without reintroducing the old Rosetta-specific workflow into the core example.