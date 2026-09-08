"""Causal replay of the positions C15-v2 repairs.

For every serious error the candidate fixes, record what each build actually
played, what the oracle wanted, and whether more depth alone would have found
it. The last column is the point: a position the baseline still fails at plus
five plies, but the candidate solves at its own depth, is a knowledge gain, not
a search accident.

usage: causal.py <compare.json> <ladder.json> <out.md>
"""
import json
import sys

COMPARE, LADDER, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

rows = json.load(open(COMPARE))
ladder = {r["fen"]: r.get("ladder", {}) for r in json.load(open(LADDER))}

repaired = [r for r in rows if r["base_loss"] >= 100 and r["cand_loss"] < 100]
worsened = [r for r in rows if r["base_loss"] < 100 and r["cand_loss"] >= 100]


def depth_note(fen):
    lad = ladder.get(fen, {})
    parts = []
    for tag in ("+2", "+5"):
        cell = lad.get(tag)
        if cell:
            parts.append(f"{tag} {'repaired' if cell['repaired'] else 'still failed'}")
    return ", ".join(parts) if parts else "not in the ladder"


with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# C15-v2 causal replay\n\n")
    fh.write(f"{len(repaired)} serious errors repaired, {len(worsened)} worsened.\n\n")
    for tag, group in (("Repaired", repaired), ("Worsened", worsened)):
        if not group:
            continue
        fh.write(f"## {tag}\n\n")
        for r in group:
            fh.write(f"### `{r['fen']}`\n\n")
            fh.write(f"* game {r['team']} ply {r['ply']}, {r['pieces']} pieces, "
                     f"{r['enemy_passers']} enemy passer(s), most advanced "
                     f"{r['enemy_passer_advance']} ranks\n")
            fh.write(f"* oracle wanted `{r['best']}`; the game played `{r['ref']}`\n")
            fh.write(f"* RC-I `{r['base_move']}` losing {r['base_loss']} cp\n")
            fh.write(f"* C15-v2 `{r['cand_move']}` losing {r['cand_loss']} cp\n")
            fh.write(f"* baseline with more depth: {depth_note(r['fen'])}\n\n")

    only_knowledge = [r for r in repaired
                      if not ladder.get(r["fen"], {}).get("+5", {}).get("repaired", False)]
    fh.write("## Repairs that extra depth does not buy\n\n")
    fh.write(f"{len(only_knowledge)} of the {len(repaired)} repaired positions are still "
             "wrong when the baseline searches five plies deeper:\n\n")
    for r in only_knowledge:
        fh.write(f"* `{r['fen']}` -- RC-I `{r['base_move']}` ({r['base_loss']} cp), "
                 f"C15-v2 `{r['cand_move']}` ({r['cand_loss']} cp)\n")

print(f"repaired {len(repaired)}, worsened {len(worsened)}, "
      f"depth-proof repairs {len(only_knowledge)} -> {OUT}")
