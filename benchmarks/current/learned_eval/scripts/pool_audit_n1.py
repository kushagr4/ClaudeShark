"""Frozen pool hygiene for N1, run before any validation or test label exists (DESIGN_N1.md section 2).

  1. Near-duplicate rule: a validation or test position that is one piece displacement away from any
     train position (same placement after removing one piece of the same colour and type from each,
     side to move ignored) is dropped from evaluation. Exact placement repeats are included.
  2. Task files: tasks_train.jsonl (unchanged), tasks_val.jsonl, and the test tasks sealed in
     test_sealed/tasks_test.jsonl; the 4M noise subset (300 validation positions) is redrawn from
     the filtered validation split.
  3. Pilot overlap (report only): N1 validation/test groups and positions that appeared in the pilot.
  4. SHA-256 of each split's sorted pid list, for the committed design.

    pool_audit_n1.py N1_DATA_DIR PILOT_DATA_DIR
"""
import collections
import hashlib
import json
import os
import random
import sys

import chess


def placement_keys(fen):
    board = chess.Board(fen)
    items = sorted((sq, pc.symbol()) for sq, pc in board.piece_map().items())
    keys = []
    for i, (sq, sym) in enumerate(items):
        rest = items[:i] + items[i + 1:]
        h = hashlib.blake2b((sym + "|" + ";".join(f"{s}{p}" for s, p in rest)).encode(), digest_size=8).digest()
        keys.append(h)
    return keys


def pid_hash(pids):
    return hashlib.sha256("\n".join(sorted(pids)).encode()).hexdigest()


def main():
    d, pilot = sys.argv[1], sys.argv[2]
    rows = [json.loads(l) for l in open(os.path.join(d, "pool.jsonl"), encoding="utf-8")]
    train_keys = set()
    for r in rows:
        if r["split"] == "train":
            train_keys.update(placement_keys(r["fen"]))
    drop = {}
    for r in rows:
        if r["split"] in ("val", "test") and any(k in train_keys for k in placement_keys(r["fen"])):
            drop[r["pid"]] = dict(split=r["split"], family=r["family"], ply=r["ply"])
    keep = [r for r in rows if r["pid"] not in drop]
    by = collections.defaultdict(list)
    for r in keep:
        by[r["split"]].append(r)

    sealed = os.path.join(d, "test_sealed")
    os.makedirs(sealed, exist_ok=True)
    for split, path in (("train", os.path.join(d, "tasks_train.jsonl")), ("val", os.path.join(d, "tasks_val.jsonl")),
                        ("test", os.path.join(sealed, "tasks_test.jsonl"))):
        with open(path, "w", encoding="utf-8") as fh:
            for r in by[split]:
                fh.write(json.dumps(dict(pid=r["pid"], fen=r["fen"])) + "\n")
    stale = os.path.join(d, "tasks_test.jsonl")
    if os.path.exists(stale):
        os.remove(stale)
    val = list(by["val"])
    random.Random("N1-20260911|noise").shuffle(val)
    with open(os.path.join(d, "tasks_noise.jsonl"), "w", encoding="utf-8") as fh:
        for r in val[:300]:
            fh.write(json.dumps(dict(pid=r["pid"], fen=r["fen"])) + "\n")
    old_noise = os.path.join(d, "tasks_noise4m.jsonl")
    if os.path.exists(old_noise):
        os.remove(old_noise)

    prow = []
    for name in ("pool.jsonl",):
        prow = [json.loads(l) for l in open(os.path.join(pilot, name), encoding="utf-8")]
    pilot_groups = {r["group"]: r["split"] for r in prow}
    pilot_pos = {r["fen4"]: r["split"] for r in prow}
    overlap = {}
    for split in ("val", "test"):
        g = collections.Counter(pilot_groups[r["group"]] for r in by[split] if r["group"] in pilot_groups)
        p = collections.Counter(pilot_pos[r["fen4"]] for r in by[split] if r["fen4"] in pilot_pos)
        overlap[split] = dict(groups_seen_in_pilot=dict(g), positions_seen_in_pilot=dict(p),
                              positions_in_pilot_seen_groups=sum(1 for r in by[split] if r["group"] in pilot_groups))
    pilot_seen = sorted({r["pid"] for s in ("val", "test") for r in by[s] if r["group"] in pilot_groups})
    res = dict(near_duplicate_rule="one piece displacement from a train position (placement minus one same-type piece)",
               dropped=len(drop), dropped_by_split=dict(collections.Counter(v["split"] for v in drop.values())),
               dropped_by_family=dict(collections.Counter(v["family"] for v in drop.values())),
               dropped_ply_le_30=sum(1 for v in drop.values() if v["ply"] <= 30),
               sizes={s: len(v) for s, v in by.items()}, pid_sha256={s: pid_hash([r["pid"] for r in v]) for s, v in by.items()},
               pool_sha256=hashlib.sha256(open(os.path.join(d, "pool.jsonl"), "rb").read()).hexdigest(),
               noise_subset=300, pilot_overlap=overlap, pilot_seen_group_pids=len(pilot_seen))
    with open(os.path.join(d, "pool_audit.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(res, dropped_pids=sorted(drop), pilot_seen_group_eval_pids=pilot_seen), fh, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
