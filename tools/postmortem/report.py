"""Post-mortem analysis of the annotated fixed-depth diagnostic games.

Reads the games written by ``play`` and annotated by ``annotate`` and answers
the questions the v0.6 post-mortem asks: first errors, phase, structure,
conversion and defence, evaluation calibration, and the passed-pawn question.
Everything is computed for the candidate and the baseline side by side.

    uv run python -m tools.postmortem.report --games corpus/postmortem/games/annotated.jsonl
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import chess

from tools.corpus.structure import analyse_structure

BANDS = ((0, 25, "<=25"), (26, 99, "26-99"), (100, 299, "100-299"), (300, 10**9, ">=300"))
SERIOUS = 100
CATASTROPHIC = 300
SIDES = ("cand", "base")


def band(loss: int) -> str:
    for lo, hi, name in BANDS:
        if lo <= loss <= hi:
            return name
    return ">=300"


def pct(a: float, b: float) -> str:
    return f"{a / b:.1%}" if b else "n/a"


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def side_score(game: dict, side: str) -> float:
    return game["cand_score"] if side == "cand" else 1.0 - game["cand_score"]


def stm_cp(m: dict, key: str) -> int:
    cp = m[key]
    return cp if m["turn"] == "w" else -cp


# ------------------------------------------------------------------ sections


def summary(games: list[dict], arena: dict[tuple[str, bool], float], out: list[str]) -> None:
    n = len(games)
    w = sum(1 for g in games if g["cand_score"] == 1.0)
    d = sum(1 for g in games if g["cand_score"] == 0.5)
    lo = n - w - d
    out += [
        "== FIXED-DEPTH DIAGNOSTIC SET ==",
        f"{n} games  +{w} ={d} -{lo}  candidate score {(w + 0.5 * d) / n:.1%}",
        f"terminations {dict(Counter(g['termination'] for g in games))}",
        "",
    ]
    # Does the arena outcome reproduce per cluster?
    same = diff = 0
    both = []
    for g in games:
        key = (g["cluster"], g["cand_white"])
        if key in arena:
            a = arena[key]
            if a == g["cand_score"]:
                same += 1
            else:
                diff += 1
            both.append((a, g["cand_score"]))
    out.append(
        f"per-game agreement with the arena result: {same} same, {diff} different "
        f"(games are not expected to repeat; the question is whether the *direction* holds)"
    )
    if both:
        out.append(
            f"arena score on these games {statistics.mean(a for a, _ in both):.1%}, "
            f"fixed-depth score {statistics.mean(b for _, b in both):.1%}"
        )
    out.append("")


def first_errors(games: list[dict], out: list[str]) -> dict:
    out.append("== FIRST-ERROR ANALYSIS (per engine, per game) ==")
    stats = {
        s: {
            "moves": 0,
            "bands": Counter(),
            "first_serious_ply": [],
            "first_cat_ply": [],
            "games_with_serious": 0,
            "games_with_cat": 0,
            "loss_sum": 0,
        }
        for s in SIDES
    }
    first_by = Counter()
    for g in games:
        firsts = {}
        for m in g["moves"]:
            s = m["mover"]
            st = stats[s]
            st["moves"] += 1
            st["bands"][band(m["cp_loss"])] += 1
            st["loss_sum"] += min(m["cp_loss"], 500)
            if m["cp_loss"] >= SERIOUS and s not in firsts:
                firsts[s] = m["ply"]
        for s in SIDES:
            if s in firsts:
                stats[s]["games_with_serious"] += 1
                stats[s]["first_serious_ply"].append(firsts[s])
        cat = {}
        for m in g["moves"]:
            if m["cp_loss"] >= CATASTROPHIC and m["mover"] not in cat:
                cat[m["mover"]] = m["ply"]
        for s in SIDES:
            if s in cat:
                stats[s]["games_with_cat"] += 1
                stats[s]["first_cat_ply"].append(cat[s])
        if len(firsts) == 2:
            first_by["cand first" if firsts["cand"] < firsts["base"] else "base first"] += 1
        elif "cand" in firsts:
            first_by["only cand erred"] += 1
        elif "base" in firsts:
            first_by["only base erred"] += 1
        else:
            first_by["neither"] += 1
    out.append(
        f"{'':<10} {'moves':>6} {'<=25':>7} {'26-99':>7} {'100-299':>8} {'>=300':>7} "
        f"{'robust':>7} {'games w/ serious':>17} {'mean 1st serious ply':>21} {'games w/ cat':>13}"
    )
    for s in SIDES:
        st = stats[s]
        n = st["moves"]
        fs = st["first_serious_ply"]
        out.append(
            f"{s:<10} {n:>6} {pct(st['bands']['<=25'], n):>7} {pct(st['bands']['26-99'], n):>7} "
            f"{pct(st['bands']['100-299'], n):>8} {pct(st['bands']['>=300'], n):>7} "
            f"{st['loss_sum'] / n:>7.1f} {st['games_with_serious']:>17} "
            f"{(statistics.mean(fs) if fs else 0):>21.1f} {st['games_with_cat']:>13}"
        )
    out.append(f"who makes the first serious error: {dict(first_by)}")
    out.append("")
    return stats


def recovery_and_conversion(games: list[dict], out: list[str]) -> None:
    out.append(
        "== CONVERSION AND DEFENCE (Stockfish eval from the engine's side, first time a threshold is reached) =="
    )
    for s in SIDES:
        out.append(f"-- {s} --")
        for thr in (100, 200, 300):
            conv = Counter()
            dfnc = Counter()
            for g in games:
                reached_up = reached_down = False
                for m in g["moves"]:
                    # eval from side s's view before the move
                    cp_w = m["sf_cp_white_before"]
                    s_is_white = g["cand_white"] == (s == "cand")
                    cp = cp_w if s_is_white else -cp_w
                    if not reached_up and cp >= thr:
                        reached_up = True
                        conv[side_score(g, s)] += 1
                    if not reached_down and cp <= -thr:
                        reached_down = True
                        dfnc[side_score(g, s)] += 1
            nc = sum(conv.values())
            nd = sum(dfnc.values())
            out.append(
                f"  ahead >= +{thr}: n={nc:>3}  won {pct(conv[1.0], nc):>6} drew {pct(conv[0.5], nc):>6} lost {pct(conv[0.0], nc):>6}"
                f"   |   behind <= -{thr}: n={nd:>3}  held (draw or win) {pct(dfnc[0.5] + dfnc[1.0], nd):>6} lost {pct(dfnc[0.0], nd):>6}"
            )
    out.append("")
    out.append("== RECOVERY: after the OPPONENT's first serious error, does the engine convert? ==")
    for s in SIDES:
        other = "base" if s == "cand" else "cand"
        res = Counter()
        for g in games:
            opp_err = next(
                (m for m in g["moves"] if m["mover"] == other and m["cp_loss"] >= SERIOUS), None
            )
            if opp_err is not None:
                res[side_score(g, s)] += 1
        n = sum(res.values())
        out.append(
            f"  {s}: opponent erred first-seriously in {n} games -> won {pct(res[1.0], n)} drew {pct(res[0.5], n)} lost {pct(res[0.0], n)}"
        )
    out.append("")


def phase_of(board: chess.Board) -> tuple[str, int]:
    st = analyse_structure(board)
    return st.phase, st.phase24


def phase_breakdown(games: list[dict], out: list[str], cache: dict) -> None:
    out.append("== PHASE BREAKDOWN (phase of the position the move was played in) ==")
    acc = {s: defaultdict(lambda: [0, 0, 0, 0]) for s in SIDES}  # moves, serious, cat, loss
    decisive_err = {s: Counter() for s in SIDES}
    for g in games:
        for m in g["moves"]:
            ph = cache[m["fen"]][0]
            a = acc[m["mover"]][ph]
            a[0] += 1
            a[1] += m["cp_loss"] >= SERIOUS
            a[2] += m["cp_loss"] >= CATASTROPHIC
            a[3] += min(m["cp_loss"], 500)
        # the decisive error of a decisive game: the loser's largest-loss move
        if g["cand_score"] != 0.5:
            loser = "cand" if g["cand_score"] == 0.0 else "base"
            worst = max(
                (m for m in g["moves"] if m["mover"] == loser),
                key=lambda m: m["cp_loss"],
                default=None,
            )
            if worst:
                decisive_err[loser][cache[worst["fen"]][0]] += 1
    out.append(f"{'phase':<12} {'side':<6} {'moves':>6} {'serious%':>9} {'cat%':>7} {'robust':>7}")
    for ph in ("opening", "middlegame", "endgame"):
        for s in SIDES:
            a = acc[s][ph]
            if a[0]:
                out.append(
                    f"{ph:<12} {s:<6} {a[0]:>6} {pct(a[1], a[0]):>9} {pct(a[2], a[0]):>7} {a[3] / a[0]:>7.1f}"
                )
    out.append(
        f"phase of the LOSER's worst move in decisive games: cand lost -> {dict(decisive_err['cand'])}; base lost -> {dict(decisive_err['base'])}"
    )
    out.append("")


def structural(games: list[dict], out: list[str], cache: dict) -> None:
    out.append("== STRUCTURAL BREAKDOWN (tags of the position at the time of each move) ==")
    want = [
        "passed_pawn",
        "advanced_passer",
        "connected_passers",
        "protected_passer",
        "exposed_king",
        "king_in_centre",
        "closed_centre",
        "open_centre",
        "locked_pawn_chain",
        "exchange_imbalance",
        "hanging_piece",
        "opposite_side_castling",
        "same_side_castling",
        "rook_ending",
        "rook_and_minor_ending",
        "minor_piece_ending",
        "pawn_ending",
        "queenless_middlegame",
        "material_imbalance",
        "bishop_pair",
        "space_advantage",
    ]
    acc = {s: defaultdict(lambda: [0, 0, 0]) for s in SIDES}
    for g in games:
        for m in g["moves"]:
            tags = cache[m["fen"]][2]
            for t in tags:
                a = acc[m["mover"]][t]
                a[0] += 1
                a[1] += m["cp_loss"] >= SERIOUS
                a[2] += min(m["cp_loss"], 500)
    out.append(
        f"{'tag':<24} {'n cand':>7} {'ser% cand':>10} {'rob cand':>9} {'n base':>7} {'ser% base':>10} {'rob base':>9} {'delta rob':>10}"
    )
    rows = []
    for t in want:
        c, b = acc["cand"][t], acc["base"][t]
        if c[0] >= 30 and b[0] >= 30:
            rows.append((t, c, b, c[2] / c[0] - b[2] / b[0]))
    for t, c, b, dr in sorted(rows, key=lambda r: -r[3]):
        out.append(
            f"{t:<24} {c[0]:>7} {pct(c[1], c[0]):>10} {c[2] / c[0]:>9.1f} {b[0]:>7} {pct(b[1], b[0]):>10} {b[2] / b[0]:>9.1f} {dr:>+10.1f}"
        )
    out.append(
        "(positive delta = candidate loses more centipawns per move than baseline in that structure)"
    )
    out.append("")


def passers(games: list[dict], out: list[str], cache: dict) -> None:
    out.append("== PASSED-PAWN CONTRIBUTION ==")
    dec = [g for g in games if g["cand_score"] != 0.5]
    with_passer = adv = 0
    for g in dec:
        tagsets = [cache[m["fen"]][2] for m in g["moves"]]
        if any("passed_pawn" in t for t in tagsets):
            with_passer += 1
        if any("advanced_passer" in t or "connected_passers" in t for t in tagsets):
            adv += 1
    out.append(
        f"decisive games {len(dec)}: a passed pawn existed at some point in {with_passer}; an advanced/connected passer in {adv}"
    )
    # Was the loser's decisive error made in a passer position, and does the
    # oracle's best move involve the passer while the engine's did not?
    for s in SIDES:
        lost = [g for g in dec if side_score(g, s) == 0.0]
        in_passer = about_passer = 0
        for g in lost:
            worst = max(
                (m for m in g["moves"] if m["mover"] == s), key=lambda m: m["cp_loss"], default=None
            )
            if not worst:
                continue
            tags = cache[worst["fen"]][2]
            if "passed_pawn" in tags:
                in_passer += 1
                board = chess.Board(worst["fen"])
                best = chess.Move.from_uci(worst["sf_best"])
                pl = chess.Move.from_uci(worst["move"])
                bp = board.piece_type_at(best.from_square) == chess.PAWN or (
                    board.is_capture(best) and board.piece_type_at(best.to_square) == chess.PAWN
                )
                pp = board.piece_type_at(pl.from_square) == chess.PAWN or (
                    board.is_capture(pl) and board.piece_type_at(pl.to_square) == chess.PAWN
                )
                if bp and not pp:
                    about_passer += 1
        out.append(
            f"  {s} lost {len(lost)}: worst move made in a passer position {in_passer}; oracle's best was a pawn move/capture while the engine's was not {about_passer}"
        )
    # Error rate in passer vs non-passer positions
    for s in SIDES:
        a = [0, 0]
        b = [0, 0]
        for g in games:
            for m in g["moves"]:
                if m["mover"] != s:
                    continue
                tgt = a if "passed_pawn" in cache[m["fen"]][2] else b
                tgt[0] += 1
                tgt[1] += m["cp_loss"] >= SERIOUS
        out.append(
            f"  {s}: serious-error rate with passers {pct(a[1], a[0])} (n={a[0]}), without {pct(b[1], b[0])} (n={b[0]})"
        )
    out.append("")


def calibration(games: list[dict], out: list[str]) -> None:
    out.append("== EVALUATION CALIBRATION against Stockfish (all positions, white's view) ==")
    rows = []
    for g in games:
        for m in g["moves"]:
            sf = m["sf_cp_white_before"]
            if abs(sf) > 1500:
                continue
            rows.append((sf, m["cand_static"], m["base_static"], m["fen"]))
    n = len(rows)
    if n < 10:
        return

    def corr(xs, ys):
        mx, my = statistics.mean(xs), statistics.mean(ys)
        sx = sum((x - mx) ** 2 for x in xs) ** 0.5
        sy = sum((y - my) ** 2 for y in ys) ** 0.5
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / (sx * sy) if sx and sy else 0.0

    sf = [r[0] for r in rows]
    c = [r[1] for r in rows]
    b = [r[2] for r in rows]
    out.append(f"positions {n}: pearson r cand {corr(sf, c):+.3f}  base {corr(sf, b):+.3f}")

    # slope: how many static cp per Stockfish cp
    def slope(xs, ys):
        mx, my = statistics.mean(xs), statistics.mean(ys)
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / sum((x - mx) ** 2 for x in xs)

    out.append(
        f"slope static/SF: cand {slope(sf, c):.2f}  base {slope(sf, b):.2f}  (units differ; the shape matters)"
    )
    # Sign disagreement: engine thinks it is better while Stockfish says worse by >= 100
    for name, idx in (("cand", 1), ("base", 2)):
        wrong = sum(
            1 for r in rows if (r[idx] > 50 and r[0] < -100) or (r[idx] < -50 and r[0] > 100)
        )
        out.append(
            f"  {name}: sign-wrong by a margin (static beyond +-50, SF beyond -+100 the other way): {wrong} ({wrong / n:.1%})"
        )
    # Material overconfidence: positions where one side is up material but SF says <= 0 for it
    values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
    comp = []
    for r in rows:
        bd = chess.Board(r[3])
        mat = sum(values[p] * (len(bd.pieces(p, True)) - len(bd.pieces(p, False))) for p in values)
        if (mat >= 2 and r[0] <= 0) or (mat <= -2 and r[0] >= 0):
            sign = 1 if mat > 0 else -1
            comp.append((sign * r[1], sign * r[2], sign * r[0]))
    if comp:
        out.append(
            f"'compensation' positions (up >=2 pawn-units of material yet Stockfish says not better): n={len(comp)}"
        )
        out.append(
            f"   mean static from the material-up side: cand {statistics.mean(x for x, _, _ in comp):+.0f}  base {statistics.mean(y for _, y, _ in comp):+.0f}  Stockfish {statistics.mean(z for _, _, z in comp):+.0f}"
        )
    out.append("")


def trajectories(games: list[dict], clusters: list[str], out: list[str]) -> None:
    out.append(
        "== REPRESENTATIVE TRAJECTORIES (candidate losses in the clusters the arena baseline won both colours) =="
    )
    for g in games:
        if g["cluster"] not in clusters or g["cand_score"] != 0.0:
            continue
        out.append(
            f"-- cluster {g['cluster']}  candidate {'White' if g['cand_white'] else 'Black'}  {g['result']} by {g['termination']} in {g['plies']} plies"
        )
        out.append(f"   start {g['start_fen']}")
        out.append(
            f"   {'ply':>4} {'side':<5} {'move':<6} {'SF':>6} {'cand_st':>8} {'base_st':>8} {'search':>7} {'loss':>5}  note"
        )
        prev = None
        for m in g["moves"]:
            sf = m["sf_cp_white_before"]
            turning = prev is not None and abs(sf - prev) >= 80
            big = m["cp_loss"] >= 60
            if turning or big or m["ply"] % 10 == 0 or m["ply"] < 2:
                search_w = m["score_stm"] if m["turn"] == "w" else -m["score_stm"]
                note = []
                if big:
                    note.append(f"loss {m['cp_loss']} (SF best {m['sf_best']})")
                if turning:
                    note.append("turning point")
                out.append(
                    f"   {m['ply']:>4} {m['mover']:<5} {m['move']:<6} {sf:>+6} {m['cand_static']:>+8} {m['base_static']:>+8} {search_w:>+7} {m['cp_loss']:>5}  {'; '.join(note)}"
                )
            prev = sf
        out.append("")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument(
        "--arena",
        type=Path,
        default=Path("benchmarks/current/2026-09-03-v0.6-material-scale-arena.jsonl"),
    )
    parser.add_argument("--out", type=Path, default=Path("corpus/postmortem/06_report.txt"))
    parser.add_argument("--clusters", default="14,20,38,75,79")
    arguments = parser.parse_args()

    games = load(arguments.games)
    arena_rows = [json.loads(line) for line in arguments.arena.open(encoding="utf-8")]
    arena = {
        (r["cluster"], r["agent_is_white"]): r["agent_score"]
        for r in arena_rows
        if r.get("record") == "game"
    }

    cache: dict[str, tuple[str, int, list[str]]] = {}
    for g in games:
        for m in g["moves"]:
            if m["fen"] not in cache:
                st = analyse_structure(chess.Board(m["fen"]))
                cache[m["fen"]] = (st.phase, st.phase24, list(st.tags))

    out: list[str] = []
    summary(games, arena, out)
    first_errors(games, out)
    recovery_and_conversion(games, out)
    phase_breakdown(games, out, cache)
    structural(games, out, cache)
    passers(games, out, cache)
    calibration(games, out)
    trajectories(games, arguments.clusters.split(","), out)
    text = "\n".join(out)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
