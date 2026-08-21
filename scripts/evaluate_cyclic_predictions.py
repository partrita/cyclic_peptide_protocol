from __future__ import annotations

import argparse
import json
import math
import pathlib

import gemmi


def closure_distance(path: pathlib.Path, chain_id: str = "A") -> float:
    doc = gemmi.cif.read_file(str(path))
    structure = gemmi.make_structure_from_block(doc.sole_block())
    model = structure[0]
    chain = model.find_chain(chain_id)
    if chain is None:
        raise ValueError(f"Chain {chain_id!r} not found in {path}")
    residues = [r for r in chain if r.name not in {"HOH"}]
    if not residues:
        raise ValueError(f"No residues found in {path}")
    first_n = residues[0]["N"]
    last_c = residues[-1]["C"]
    if first_n is None or last_c is None:
        raise ValueError(f"Missing terminal N/C atoms in {path}")
    a = first_n.pos
    b = last_c.pos
    return math.dist((a.x, a.y, a.z), (b.x, b.y, b.z))


def main() -> int:
    parser = argparse.ArgumentParser(description="Score ESMFold2 cyclic-peptide predictions by closure geometry.")
    parser.add_argument("--input-dir", required=True, type=pathlib.Path)
    parser.add_argument("--json", dest="json_path", required=True, type=pathlib.Path)
    parser.add_argument("--cutoff", type=float, default=2.0)
    args = parser.parse_args()

    rows = []
    for path in sorted(args.input_dir.glob("*.cif")):
        distance = closure_distance(path)
        rows.append({
            "structure": str(path),
            "head_to_tail_N_C_distance_angstrom": round(distance, 3),
            "closure_pass": distance <= args.cutoff,
        })
        print(f"{path.name}: N-C={distance:.3f} A pass={distance <= args.cutoff}")

    args.json_path.parent.mkdir(parents=True, exist_ok=True)
    args.json_path.write_text(json.dumps(rows, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
