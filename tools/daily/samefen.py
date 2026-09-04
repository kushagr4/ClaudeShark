"""Repeated organiser starting positions as natural experiments.

The competition reuses starting positions: 114 distinct FENs across 143 public
games, with 23 used more than once. When two engines are handed the same
position and diverge, the divergence is a controlled comparison in a way that
self-play is not -- same start, different player, observable result.

The question asked here is deliberately narrow. It is **not** "what heuristic
does that bot use", which cannot be answered from moves and would be guesswork
dressed as analysis. It is "what chess capability separates the line the
stronger side took from the line ClaudeShark takes".

Two phases, because the second is expensive and the first is free:

    parse   group the games by exact start FEN, find the first ply where the
            games of a family diverge, and rank the families by how much is
            riding on that divergence. No engine, no oracle. **The ranking is
            screening only.** A differing result is not evidence that one move
            was better -- it is downstream of every later decision -- and a
            leaderboard rating is a snapshot, not the player's strength at game
            time. Neither is used as a proxy for move quality anywhere.
    score   establish move quality independently. The first *literal*
            divergence is often several interchangeable opening moves, so the
            oracle scores every observed move there and, when it does not
            materially separate them, the walk continues until it does. Two
            plies are therefore recorded: the first literal divergence and the
            **first meaningful oracle divergence**. A ClaudeShark snapshot is
            then asked what it plays at that point.

Every observation carries an explicit evidence level:

    OBSERVATIONAL           different engines made different choices
    ORACLE-SUPPORTED        the oracle materially separates those choices
    CLAUDESHARK-ACTIONABLE  and rated-v1 takes the inferior line, or reads the
                            position hundreds of centipawns wrong

Nothing goes from observational divergence straight to a feature. The
independence unit is the **start-FEN family**, not the game: a four-game family
is one family, and its trajectories count separately only once they have
genuinely diverged. Both counts are reported.

Hypothesis formation is restricted to the diagnostic split by default, so the
validation and holdout families stay unexamined.

    uv run python -m tools.daily.samefen parse --games analysis/top50_games.jsonl --split corpus/daily/splits/competition_diagnostic_fens.txt --out corpus/daily/samefen_families.txt
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter
from pathlib import Path

import chess
import chess.pgn


def mainline(row: dict) -> list[chess.Move]:
    game = chess.pgn.read_game(io.StringIO(row.get("pgn") or ""))
    return list(game.mainline_moves()) if game else []


def team(row: dict, colour: str) -> dict:
    side = row.get(colour) or {}
    return {"name": side.get("team_name"), "rank": side.get("rank"), "rating": side.get("rating")}


def score_for(row: dict, colour: str) -> float:
    winner = row.get("winner_colour")
    if winner not in ("white", "black"):
        return 0.5
    return 1.0 if winner == colour else 0.0


def first_divergence(games: list[dict]) -> tuple[int, dict[str, list[str]]]:
    """The first ply at which not every game of the family plays the same move."""
    lines = {g["game_id"]: mainline(g) for g in games}
    depth = min((len(v) for v in lines.values()), default=0)
    for ply in range(depth):
        chosen = {gid: moves[ply].uci() for gid, moves in lines.items()}
        if len(set(chosen.values())) > 1:
            grouped: dict[str, list[str]] = {}
            for gid, move in chosen.items():
                grouped.setdefault(move, []).append(gid)
            return ply, grouped
    return -1, {}


def parse(arguments: argparse.Namespace) -> None:
    rows = {r["game_id"]: r for r in (json.loads(line) for line in arguments.games.open(encoding="utf-8"))}
    allowed: set[str] | None = None
    if arguments.split:
        allowed = {line.strip() for line in arguments.split.read_text(encoding="utf-8").splitlines() if line.strip()}
    families: dict[str, list[dict]] = {}
    for r in rows.values():
        fen = r.get("starting_fen")
        if not fen or not mainline(r):
            continue
        if allowed is not None and fen not in allowed:
            continue
        families.setdefault(fen, []).append(r)
    repeated = {f: gs for f, gs in families.items() if len(gs) > 1}

    entries = []
    for fen, games in repeated.items():
        ply, grouped = first_divergence(games)
        board = chess.Board(fen)
        outcomes = Counter(g.get("winner_colour") for g in games)
        ratings = [t["rating"] for g in games for t in (team(g, "white"), team(g, "black")) if t["rating"]]
        # Screening only, to decide where to spend oracle time. Differing
        # outcomes and higher ratings are NOT evidence that one move is better:
        # a result is downstream of every later decision, and a leaderboard
        # rating is a snapshot rather than the player's strength at game time.
        # Move quality is established in the scoring phase or not at all.
        value = (len(games)
                 + (3 if len(outcomes) > 1 else 0)
                 + (2 if ply >= 0 and ply < 6 else 1 if ply >= 0 else 0)
                 + (2 if len(grouped) >= 3 else 0))
        entries.append({
            "fen": fen, "games": len(games), "value": value,
            "side_to_move": "w" if board.turn == chess.WHITE else "b",
            "fullmove": board.fullmove_number,
            "outcomes": dict(outcomes),
            "divergence_ply": ply,
            "divergence_moves": {m: len(v) for m, v in grouped.items()},
            "max_rating": max(ratings) if ratings else None,
            "min_rating": min(ratings) if ratings else None,
            "detail": [{
                "game_id": g["game_id"],
                "white": team(g, "white"), "black": team(g, "black"),
                "result": g.get("canonical_result"), "winner": g.get("winner_colour"),
                "first_move": mainline(g)[0].uci() if mainline(g) else None,
                "divergence_move": mainline(g)[ply].uci() if ply >= 0 and len(mainline(g)) > ply else None,
                "plies": len(mainline(g)),
                "termination": g.get("termination"),
            } for g in games],
        })
    entries.sort(key=lambda e: (-e["value"], -e["games"]))

    lines = ["== REPEATED ORGANISER START POSITIONS AS NATURAL EXPERIMENTS ==",
             f"source {arguments.games}"
             + (f", restricted to {arguments.split.name}" if arguments.split else ", whole population"),
             f"{len(families)} families with moves, {len(repeated)} used more than once, "
             f"covering {sum(len(g) for g in repeated.values())} games", ""]
    for i, e in enumerate(entries, start=1):
        lines.append(f"{i:>2}. value {e['value']:>2}  {e['games']} games  outcomes {e['outcomes']}  "
                     f"start move {e['fullmove']} {'White' if e['side_to_move'] == 'w' else 'Black'} to move")
        lines.append(f"    {e['fen']}")
        if e["divergence_ply"] >= 0:
            lines.append(f"    first divergence at ply {e['divergence_ply'] + 1}: {e['divergence_moves']}")
        else:
            lines.append("    the games never diverge inside their common length")
        for d in e["detail"]:
            lines.append(f"      {d['white']['name']} ({d['white']['rating']}) vs {d['black']['name']} ({d['black']['rating']})"
                         f"  {d['result']}  {d['plies']} plies  {d['termination']}"
                         f"  first {d['first_move']}  at divergence {d['divergence_move']}")
        lines.append("")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps(entries, indent=1) + "\n", encoding="utf-8")
    # Team names are user-chosen and some contain emoji; the file is UTF-8
    # either way, but a Windows console in cp1252 cannot print them.
    encoding = sys.stdout.encoding or "utf-8"
    print(text.encode(encoding, errors="replace").decode(encoding))


SEPARATION = 50    # cp: below this the oracle has not distinguished the observed moves
SCORE_ERROR = 200  # cp: a rated-v1 root this far from the oracle is a world-model error


def score(arguments: argparse.Namespace) -> None:
    from tools.corpus.oracle import MATE_CP, Oracle
    from tools.postmortem.play import Engine

    entries = json.loads(arguments.families.read_text(encoding="utf-8"))[: arguments.families_limit]
    rows = {r["game_id"]: r for r in (json.loads(line) for line in arguments.games.open(encoding="utf-8"))}
    oracle = Oracle()
    engine = Engine(arguments.engine, arguments.depth)
    results = []
    try:
        for e in entries:
            lines = {d["game_id"]: mainline(rows[d["game_id"]]) for d in e["detail"]}
            board = chess.Board(e["fen"])
            meaningful = None
            trail = []
            depth = min(len(v) for v in lines.values())
            for ply in range(min(depth, arguments.max_ply)):
                observed: dict[str, list[str]] = {}
                for gid, moves in lines.items():
                    observed.setdefault(moves[ply].uci(), []).append(gid)
                if len(observed) > 1:
                    fen = board.fen()
                    label = oracle.analyse(fen, arguments.nodes, multipv=arguments.multipv)
                    best_value = label.cp_stm
                    scored = {}
                    for move in observed:
                        after = oracle.score_after(fen, move, arguments.nodes)
                        # score_after is from the point of view of whoever moves
                        # next, so negate it to get the mover's view.
                        value = max(-MATE_CP, min(MATE_CP, -after.cp_stm))
                        scored[move] = {"value": value, "loss": max(0, best_value - value),
                                        "games": len(observed[move])}
                    spread = max(v["loss"] for v in scored.values())
                    engine.ask("new")
                    ours = engine.ask(f"go {fen}")
                    our_move = ours["move"]
                    if our_move and our_move not in scored:
                        after = oracle.score_after(fen, our_move, arguments.nodes)
                        value = max(-MATE_CP, min(MATE_CP, -after.cp_stm))
                        scored[our_move] = {"value": value, "loss": max(0, best_value - value), "games": 0}
                    step = {
                        "ply": ply, "fen": fen, "oracle_best": label.best, "oracle_cp": best_value,
                        "observed": scored, "spread": spread,
                        "our_move": our_move, "our_root": ours["score"],
                        "our_loss": scored.get(our_move, {}).get("loss"),
                        "score_gap": abs(ours["score"] - best_value),
                    }
                    trail.append(step)
                    if spread >= arguments.separation:
                        meaningful = step
                    break
                board.push(next(iter(lines.values()))[ply])
            classification = "NEITHER"
            level = "OBSERVATIONAL"
            if meaningful is not None:
                level = "ORACLE-SUPPORTED"
                move_error = (meaningful["our_loss"] or 0) >= arguments.separation
                score_error = meaningful["score_gap"] >= SCORE_ERROR
                classification = ("BOTH" if move_error and score_error else
                                  "MOVE ERROR" if move_error else
                                  "SCORE ERROR" if score_error else "NEITHER")
                if move_error or score_error:
                    level = "CLAUDESHARK-ACTIONABLE"
            results.append({**e, "meaningful_divergence": meaningful, "trail": trail,
                            "classification": classification, "evidence_level": level})
            print(f"  {e['fen'][:46]}  {level}  {classification}", flush=True)
        provenance = oracle.provenance()
    finally:
        engine.close()
        oracle.close()

    out = [f"== SAME-FEN DIVERGENCES, SCORED BY THE ORACLE ({len(results)} families) ==",
           f"engine {arguments.engine} at depth {arguments.depth}; oracle at {arguments.nodes} nodes, multipv {arguments.multipv}",
           f"a divergence counts as separated only when the observed moves differ by at least {arguments.separation} cp;",
           f"a score error is a rated-v1 root at least {SCORE_ERROR} cp from the oracle.",
           "Game results and leaderboard ratings are never used as evidence of move quality.", ""]
    for r in results:
        out.append(f"[{r['evidence_level']}] {r['classification']}   {r['games']} games   {r['fen']}")
        out.append(f"   first literal divergence at ply {r['divergence_ply'] + 1}: {r['divergence_moves']}")
        m = r["meaningful_divergence"]
        if m is None:
            out.append(f"   the oracle did not separate the observed moves by {arguments.separation} cp: "
                       "interchangeable choices, not a capability difference")
            if r["trail"]:
                t = r["trail"][0]
                out.append(f"      spread was only {t['spread']} cp; oracle prefers {t['oracle_best']} at {t['oracle_cp']:+}")
        else:
            same = "the same ply" if m["ply"] == r["divergence_ply"] else f"ply {m['ply'] + 1}"
            out.append(f"   first MEANINGFUL oracle divergence at {same}: spread {m['spread']} cp, "
                       f"oracle prefers {m['oracle_best']} at {m['oracle_cp']:+}")
            for move, d in sorted(m["observed"].items(), key=lambda kv: kv[1]["loss"]):
                tag = "  <- rated-v1 plays this" if move == m["our_move"] else ""
                out.append(f"      {move}  oracle value {d['value']:>+6}  loss {d['loss']:>4}  "
                           f"in {d['games']} public game(s){tag}")
            out.append(f"      rated-v1 root {m['our_root']:+}, oracle {m['oracle_cp']:+}, gap {m['score_gap']}")
        out.append("")
    supported = [r for r in results if r["evidence_level"] != "OBSERVATIONAL"]
    actionable = [r for r in results if r["evidence_level"] == "CLAUDESHARK-ACTIONABLE"]
    out.append("== INDEPENDENCE ==")
    out.append(f"   start-FEN families examined      {len(results)}")
    out.append(f"   games inside them                {sum(r['games'] for r in results)}")
    out.append(f"   ORACLE-SUPPORTED families        {len(supported)}")
    out.append(f"   CLAUDESHARK-ACTIONABLE families  {len(actionable)}")
    out.append("   The family is the independence unit. A four-game family is one family, not four")
    out.append("   confirmations, and its games count separately only once their trajectories diverge.")
    out.append("")
    out.append(f"oracle provenance: {provenance['engine']}, {provenance['limit']}")
    text = "\n".join(out)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    encoding = sys.stdout.encoding or "utf-8"
    print(text.encode(encoding, errors="replace").decode(encoding))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="phase", required=True)
    p = sub.add_parser("parse", help="group and rank repeated-FEN families; no engine or oracle")
    p.add_argument("--games", type=Path, required=True)
    p.add_argument("--split", type=Path, default=None, help="restrict to the FEN list of one split")
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(func=parse)
    q = sub.add_parser("score", help="establish move quality with the oracle; CPU heavy")
    q.add_argument("--families", type=Path, required=True, help="the .json written by the parse phase")
    q.add_argument("--games", type=Path, required=True)
    q.add_argument("--engine", type=Path, default=Path("champions/rated_v1"))
    q.add_argument("--depth", type=int, default=6)
    q.add_argument("--nodes", type=int, default=1_000_000)
    q.add_argument("--multipv", type=int, default=6)
    q.add_argument("--separation", type=int, default=SEPARATION)
    q.add_argument("--max-ply", type=int, default=30)
    q.add_argument("--families-limit", type=int, default=14)
    q.add_argument("--out", type=Path, required=True)
    q.set_defaults(func=score)
    arguments = parser.parse_args()
    arguments.func(arguments)


if __name__ == "__main__":
    main()
