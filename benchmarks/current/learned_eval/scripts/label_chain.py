"""Run labelling steps one after another (one CPU-heavy job at a time).

    label_chain.py DATA_DIR val        validation @1M, the 300-position 4M noise subset, validation pairs @1M
    label_chain.py DATA_DIR test       test @1M, test pairs @1M (only after the model is frozen)
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def label(tasks, out, nodes, workers=10, hash_mb=32):
    print(f"STEP {os.path.basename(out)} @{nodes} start {time.strftime('%H:%M:%S')}", flush=True)
    subprocess.run([PY, os.path.join(HERE, "sf_label.py"), tasks, out, "--nodes", str(nodes), "--workers", str(workers),
                    "--hash", str(hash_mb)], check=True)
    print(f"STEP {os.path.basename(out)} done {time.strftime('%H:%M:%S')}", flush=True)


def noise_report(d):
    """Report only (DESIGN_N1.md section 3): nothing here may change a verdict, threshold or choice."""
    load = lambda f: {r["pid"]: r for r in map(json.loads, open(os.path.join(d, f), encoding="utf-8"))}  # noqa: E731
    m1, m4, k50 = load("labels_val_1m.jsonl"), load("labels_noise_4m.jsonl"), load("labels_noise_50k.jsonl")
    cat = lambda e: 2 if e >= 0.75 else 0 if e <= 0.25 else 1  # noqa: E731
    band = lambda e: abs(e - 0.5) < 0.10  # noqa: E731
    ids = [p for p in m4 if p in m1 and p in k50 and None not in (m1[p]["E"], m4[p]["E"], k50[p]["E"])]
    dE = [abs(m1[p]["E"] - m4[p]["E"]) for p in ids]
    shift = [m1[p]["E"] - k50[p]["E"] for p in ids]
    bshift = [m1[p]["E"] - k50[p]["E"] for p in ids if band(m1[p]["E"])]
    rep = dict(n=len(ids), mean_abs_dE_1m_4m=sum(dE) / len(dE), median_abs_dE_1m_4m=sorted(dE)[len(dE) // 2],
               share_abs_dE_ge_0p05=sum(x >= 0.05 for x in dE) / len(dE),
               category_agreement_1m_4m=sum(cat(m1[p]["E"]) == cat(m4[p]["E"]) for p in ids) / len(ids),
               bestmove_agreement_1m_4m=sum(m1[p]["bestmove"] == m4[p]["bestmove"] for p in ids) / len(ids),
               band_agreement_1m_4m=sum(band(m1[p]["E"]) == band(m4[p]["E"]) for p in ids) / len(ids),
               band_agreement_50k_1m=sum(band(k50[p]["E"]) == band(m1[p]["E"]) for p in ids) / len(ids),
               band_agreement_50k_4m=sum(band(k50[p]["E"]) == band(m4[p]["E"]) for p in ids) / len(ids),
               signed_shift_50k_to_1m=sum(shift) / len(shift),
               signed_shift_50k_to_1m_band=(sum(bshift) / len(bshift)) if bshift else None,
               band_n_1m=sum(band(m1[p]["E"]) for p in ids))
    rep["calibration_caveat"] = abs(rep["signed_shift_50k_to_1m"]) > 0.01 or (
        rep["signed_shift_50k_to_1m_band"] is not None and abs(rep["signed_shift_50k_to_1m_band"]) > 0.01)
    with open(os.path.join(d, "noise_1m_vs_4m.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print("NOISE", json.dumps(rep), flush=True)


def main():
    d, which = sys.argv[1], sys.argv[2]
    if which == "val":
        label(os.path.join(d, "tasks_val.jsonl"), os.path.join(d, "labels_val_1m.jsonl"), 1_000_000)
        label(os.path.join(d, "tasks_noise.jsonl"), os.path.join(d, "labels_noise_4m.jsonl"), 4_000_000)
        label(os.path.join(d, "tasks_noise.jsonl"), os.path.join(d, "labels_noise_50k.jsonl"), 50_000)
        noise_report(d)
        subprocess.run([PY, os.path.join(HERE, "pairs_n1.py"), "build", d, "val",
                        os.path.join(d, "labels_val_1m.jsonl"), "1200", os.path.join(d, "pairs")], check=True)
        label(os.path.join(d, "pairs", "val_pair_tasks.jsonl"), os.path.join(d, "pairs", "val_pair_labels.jsonl"), 1_000_000)
    elif which == "test":
        sealed = os.path.join(d, "test_sealed")
        freeze = os.path.join(sys.argv[3], "freeze.json")
        assert os.path.exists(freeze), "the freeze manifest must exist before any test label is produced"
        label(os.path.join(sealed, "tasks_test.jsonl"), os.path.join(sealed, "labels_test_1m.jsonl"), 1_000_000)
        subprocess.run([PY, os.path.join(HERE, "pairs_n1.py"), "build", d, "test",
                        os.path.join(sealed, "labels_test_1m.jsonl"), "5000", os.path.join(sealed, "pairs")], check=True)
        label(os.path.join(sealed, "pairs", "test_pair_tasks.jsonl"),
              os.path.join(sealed, "pairs", "test_pair_labels.jsonl"), 1_000_000)
    print("CHAIN DONE", which, flush=True)


if __name__ == "__main__":
    main()
