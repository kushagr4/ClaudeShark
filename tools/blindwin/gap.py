"""The evaluation gap at a quiet position, per mechanism, and the representative cases.

For every blind episode the oracle is asked about the position at the end of
its own principal variation -- a quiet position by construction, where the
win is supposed to be visible -- and production's static there is set beside
Stockfish's score there. If Stockfish still says +400 and the static says
+120, the missing knowledge is whatever that position contains: which
features, in which phase, with what material.

Also prints, per mechanism, the largest-gap cases with their FEN, the
engine's move, Stockfish's best move and the PV, for hand inspection.

    uv run python -m tools.blindwin.gap --episodes corpus/blindwin/episodes.jsonl --out corpus/blindwin/03_gap.txt
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import chess

from tools.blindwin.dataset import passers
from tools.corpus.oracle import Oracle
from tools.corpus.structure import analyse_structure


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    episodes = [json.loads(line) for line in arguments.episodes.open(encoding="utf-8")]

    with Oracle() as oracle:
        for e in episodes:
            end = chess.Board(e["end_fen"])
            if end.is_game_over():
                e["sf_at_pv_end"] = 10000 if end.is_checkmate() else 0
            else:
                label = oracle.analyse(e["end_fen"], arguments.nodes)
                cp = label.cp_stm
                # From the episode mover's side.
                start_turn = e["fen"].split()[1] == "w"
                e["sf_at_pv_end"] = cp if end.turn == start_turn else -cp
            st = analyse_structure(end)
            e["end_tags"] = list(st.tags)
            e["end_phase"] = st.phase
            mover_white = e["fen"].split()[1] == "w"
            e["end_our_passers"] = len(passers(end, mover_white))
            ranks = []
            for sq in passers(end, mover_white):
                r = chess.square_rank(sq)
                ranks.append(r if mover_white else 7 - r)
            e["end_best_passer_rank"] = max(ranks) if ranks else -1
            e["gap_at_pv_end"] = min(e["sf_at_pv_end"], 2000) - e["static_at_pv_end"]

    lines = [f"== EVALUATION GAP AT THE PV END ({len(episodes)} blind episodes): Stockfish vs production static on a quiet position ==", ""]
    lines.append(f"{'mechanism':<22} {'n':>3} {'SF at PV end':>13} {'static at PV end':>17} {'gap':>6} {'passer rank>=5':>15} {'end phase':<22}")
    by = defaultdict(list)
    for e in episodes:
        by[e["mechanism"]].append(e)
    for k, es in sorted(by.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"{k:<22} {len(es):>3} {statistics.mean(min(e['sf_at_pv_end'], 2000) for e in es):>+13.0f} "
                     f"{statistics.mean(e['static_at_pv_end'] for e in es):>+17.0f} {statistics.mean(e['gap_at_pv_end'] for e in es):>+6.0f} "
                     f"{sum(e['end_best_passer_rank'] >= 5 for e in es):>15} {dict(Counter(e['end_phase'] for e in es))!s:<22}")
    lines.append("")
    lines.append("== FEATURES OF THE PV-END POSITIONS where the gap is largest (>= 300) ==")
    big = [e for e in episodes if e["gap_at_pv_end"] >= 300]
    small = [e for e in episodes if e["gap_at_pv_end"] < 150]
    tb = Counter(t for e in big for t in e["end_tags"])
    ts = Counter(t for e in small for t in e["end_tags"])
    lines.append(f"large-gap episodes {len(big)}, small-gap {len(small)}")
    rows = [(t, tb[t] / max(1, len(big)), ts[t] / max(1, len(small))) for t in set(tb) | set(ts) if tb[t] >= 8]
    for t, a, s in sorted(rows, key=lambda r: -(r[1] - r[2]))[:14]:
        lines.append(f"  {t:<28} large-gap {a:>5.0%}  small-gap {s:>5.0%}  diff {a - s:>+5.0%}")
    lines.append(f"  own passer on rank >= 5 at PV end: large-gap {sum(e['end_best_passer_rank'] >= 5 for e in big) / max(1, len(big)):.0%}, small-gap {sum(e['end_best_passer_rank'] >= 5 for e in small) / max(1, len(small)):.0%}")
    lines.append(f"  own passer on rank >= 6 at PV end: large-gap {sum(e['end_best_passer_rank'] >= 6 for e in big) / max(1, len(big)):.0%}, small-gap {sum(e['end_best_passer_rank'] >= 6 for e in small) / max(1, len(small)):.0%}")
    lines.append(f"  material from our side at PV end (mean): large-gap {statistics.mean(e['end_material'] for e in big) if big else 0:+.1f}, small-gap {statistics.mean(e['end_material'] for e in small) if small else 0:+.1f}")
    lines.append("")
    lines.append("== REPRESENTATIVE CASES, largest Stockfish-vs-root gap per mechanism ==")
    for k, es in sorted(by.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"-- {k}")
        for e in sorted(es, key=lambda e: -(min(e["sf_cp_1m"], 2000) - e["root"]))[:4]:
            lines.append(f"   cl {e['cluster']:>3} ply {e['ply']:>3}  SF {e['sf_cp_1m']:>+5} (mate {e['sf_mate']})  root {e['root']:>+5}  static {e['static']:>+5}  "
                         f"played {e['move']} (loss {e['cp_loss']})  best {e['sf_best']}  {e['horizon_or_blind'].split(' ')[0]}; PV-end static {e['static_at_pv_end']:+} vs SF {e['sf_at_pv_end']:+}")
            lines.append(f"       {e['fen']}")
            lines.append(f"       pv {' '.join(e['pv'])}")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    with arguments.out.with_suffix(".jsonl").open("w", encoding="utf-8") as fh:
        for e in episodes:
            fh.write(json.dumps(e) + "\n")
    print(text)


if __name__ == "__main__":
    main()
