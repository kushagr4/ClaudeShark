"""Build the pilot position pool: sources, holdout exclusion, frozen by-group split, sampling.

Every rule here is the one preregistered in ../DESIGN.md section 3. Outputs go to the external
data directory (large, not tracked); the manifest records input hashes and every count.

    .venv/Scripts/python.exe benchmarks/current/learned_eval/scripts/build_pool.py --out DIR
"""
import argparse
import collections
import hashlib
import json
import os
import random
import sys

import chess
import chess.pgn

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
from tools.corpus.extract import _game_id  # noqa: E402  (same TWIC game ids as corpus/candidates.jsonl)

SEED = 20260911
TWIC_DIR = "C:/Users/epick/engines/twic"
AUTOPSY = os.path.join(ROOT, "benchmarks/current/rcj_loss_autopsy")
STANDARD4 = " ".join(chess.STARTING_FEN.split()[:4])

REPO_SOURCES = {
    "PUBLIC": [
        "analysis/top50_games.jsonl",
        "analysis/refresh_2026-09-05/top50_games.jsonl",
        "analysis/competitors/659a3020_alphafish/alphafish_games.jsonl",
        "analysis/competitors/claudeshark_public/games.jsonl",
    ],
    "VS_SF": [
        "corpus/strength/c5/c5_vs_sf2300_dev_60_strict.annotated.jsonl",
        "corpus/strength/c5/c5_vs_sf2300_holdout_b_100_strict.pgn",
        "corpus/strength/c5/c5_vs_sf2400_dev2400_100_strict.annotated.jsonl",
        "corpus/strength/c5/c5_vs_sf2400_holdout2400_a_100_strict.annotated.jsonl",
        "corpus/strength/c8/c8_vs_sf2400_dev2400_60_strict.pgn",
        "corpus/strength/games/rcc_vs_sf2300_dev_100.annotated.jsonl",
        "corpus/strength/games/rcc_vs_sf2300_dev_100_strict.annotated.jsonl",
        "corpus/strength/games/rcc_vs_sf2300_holdout_a_100_strict.pgn",
        "corpus/strength/rcf/rcf_vs_sf2800_dev2400_60_strict.annotated.jsonl",
    ],
    "SELFPLAY": [
        "corpus/daily/rcc/checkext_vs_rcb_120s_100.pgn",
        "corpus/daily/rcc/speed_vs_rcb_120s_100_pc.pgn",
        "corpus/daily/time/games/c1staged_vs_ratedv1_120s.pgn",
        "corpus/daily/time/games/early16_vs_ratedv1_120s.pgn",
        "corpus/strength/c5/c5_vs_rcc_dev_60_strict.pgn",
        "corpus/strength/c5/c5_vs_rcc_val_80_strict.pgn",
        "corpus/strength/c8/c8_vs_c5_dev_60_strict.annotated.jsonl",
        "corpus/strength/c9/c9_vs_c5_dev_60_strict.pgn",
    ],
}
PER_GAME = {"TWIC": 1, "PUBLIC": 4, "VS_SF": 2, "SELFPLAY": 2}
FIRST_PLY = {"TWIC": 16, "PUBLIC": 2, "VS_SF": 2, "SELFPLAY": 2}
MIN_GAP = 10
SPLIT_PRIORITY = {"test": 0, "val": 1, "train": 2}


def fen4(fen):
    return " ".join(fen.split()[:4])


def sha1(text):
    return hashlib.sha1(text.encode()).hexdigest()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def split_of(group):
    k = int(sha1(f"{SEED}|{group}"), 16) % 10
    return "train" if k < 8 else "val" if k == 8 else "test"


def replay(start_fen, moves):
    """Moves as UCI or SAN strings -> list of chess.Move, or None if any move fails."""
    board = chess.Board(start_fen)
    out = []
    for m in moves:
        mv = None
        try:
            mv = chess.Move.from_uci(m)
            if mv not in board.legal_moves:
                mv = None
        except ValueError:
            mv = None
        if mv is None:
            try:
                mv = board.parse_san(m)
            except ValueError:
                return None
        out.append(mv)
        board.push(mv)
    return out


def moves_from(v):
    out = []
    for x in v:
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            out.append(x.get("move") or x.get("uci") or x.get("san"))
    return [m for m in out if m]


def load_repo_games():
    games = []
    for family, files in REPO_SOURCES.items():
        for rel in files:
            path = os.path.join(ROOT, rel)
            if rel.endswith(".pgn"):
                with open(path, encoding="utf-8", errors="replace") as fh:
                    i = 0
                    while True:
                        g = chess.pgn.read_game(fh)
                        if g is None:
                            break
                        h = g.headers
                        gid = h.get("MatchId", "") + ("#" + h.get("GameIndex") if h.get("GameIndex") else "")
                        gid = gid or f"{rel}#{i}"
                        games.append(dict(family=family, source=rel, gid=gid, start=h.get("FEN") or chess.STARTING_FEN,
                                          moves=[m.uci() for m in g.mainline_moves()]))
                        i += 1
            else:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    for ln, line in enumerate(fh):
                        try:
                            d = json.loads(line)
                        except ValueError:
                            continue
                        if not isinstance(d, dict) or not isinstance(d.get("moves"), list):
                            continue
                        start = d.get("start_fen") or d.get("starting_fen") or d.get("fen")
                        mv = moves_from(d["moves"])
                        if not start or not mv:
                            continue
                        gid = d.get("game_id") or d.get("game") or (
                            f"{d['match_id']}#{d.get('game_index')}" if d.get("match_id") else f"{rel}:{ln}")
                        games.append(dict(family=family, source=rel, gid=str(gid), start=start, moves=mv))
    return games


def load_twic(n_wanted, exclude_ids, rng):
    """Header pass over every TWIC game, then a seeded choice of eligible games parsed in full."""
    eligible = []
    total = 0
    for name in sorted(os.listdir(TWIC_DIR)):
        if not name.endswith(".pgn"):
            continue
        path = os.path.join(TWIC_DIR, name)
        with open(path, encoding="latin-1") as fh:
            while True:
                offset = fh.tell()
                h = chess.pgn.read_headers(fh)
                if h is None:
                    break
                total += 1
                if h.get("Variant") or h.get("FEN") or h.get("SetUp") == "1":
                    continue
                if h.get("Result") not in ("1-0", "0-1", "1/2-1/2"):
                    continue
                try:
                    we, be = int(h.get("WhiteElo", "0")), int(h.get("BlackElo", "0"))
                except ValueError:
                    continue
                if we < 2300 or be < 2300:
                    continue
                gid = _game_id(h, name)
                if gid in exclude_ids:
                    continue
                eligible.append((gid, path, offset))
    eligible.sort()
    rng.shuffle(eligible)
    chosen, seen = [], set()
    for gid, path, offset in eligible:
        if len(chosen) >= n_wanted:
            break
        if gid in seen:
            continue
        with open(path, encoding="latin-1") as fh:
            fh.seek(offset)
            g = chess.pgn.read_game(fh)
        moves = [m.uci() for m in g.mainline_moves()]
        if len(moves) < 24:
            continue
        seen.add(gid)
        chosen.append(dict(family="TWIC", source=os.path.basename(path), gid=gid, start=chess.STARTING_FEN, moves=moves))
    return chosen, dict(twic_games_total=total, twic_eligible_after_exclusion=len(eligible))


def autopsy_sets():
    uuids, starts, positions, seqs = set(), set(), set(), set()
    pgn_dir = os.path.join(AUTOPSY, "pgn")
    for name in sorted(os.listdir(pgn_dir)):
        uuids.add(os.path.splitext(name)[0])
        with open(os.path.join(pgn_dir, name), encoding="utf-8") as fh:
            g = chess.pgn.read_game(fh)
        b = g.board()
        starts.add(fen4(b.fen()))
        positions.add(fen4(b.fen()))
        ucis = []
        for mv in g.mainline_moves():
            b.push(mv)
            positions.add(fen4(b.fen()))
            ucis.append(mv.uci())
        seqs.add((fen4(g.board().fen()), tuple(ucis)))
    with open(os.path.join(AUTOPSY, "data/scan_all.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            positions.add(fen4(json.loads(line)["fen"]))
    holdout = []
    for f in ("verify.json", "verify_sup.json"):
        for v in json.load(open(os.path.join(AUTOPSY, "data", f), encoding="utf-8")):
            positions.add(fen4(v["fen"]))
            holdout.append(v["id"])
    return uuids, starts, positions, seqs, holdout


def sample_game(game, positions_excluded, candidate_fens):
    rng = random.Random(sha1(f"{SEED}|sample|{game['gid']}"))
    board = chess.Board(game["start"])
    boards = []
    for ply, mv in enumerate(game["moves"], 1):
        board.push(mv)
        boards.append((ply, board.copy(stack=False)))
    first = FIRST_PLY[game["family"]]
    candidates = [(p, b) for p, b in boards[:-1] if p >= first]  # the game move after ply p is moves[p]
    rng.shuffle(candidates)
    picked, skipped = [], collections.Counter()
    for ply, b in candidates:
        if len(picked) >= PER_GAME[game["family"]]:
            break
        if any(abs(ply - q) < MIN_GAP for q, _ in picked):
            continue
        key = fen4(b.fen())
        if b.is_check() or b.is_game_over(claim_draw=False):
            skipped["check_or_over"] += 1
            continue
        if key in positions_excluded:
            skipped["autopsy_position"] += 1
            continue
        if key in candidate_fens:
            skipped["candidates_position"] += 1
            continue
        picked.append((ply, b))
    return picked, skipped


def describe(b):
    counts = {sym: len(b.pieces(chess.Piece.from_symbol(sym).piece_type, chess.Piece.from_symbol(sym).color))
              for sym in "PNBRQpnbrq"}
    phase = min(24, counts["N"] + counts["n"] + counts["B"] + counts["b"] + 2 * (counts["R"] + counts["r"])
                + 4 * (counts["Q"] + counts["q"]))
    material = "".join(f"{sym}{counts[sym]}" for sym in "QRBNPqrbnp")
    return phase, material


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--twic-games", type=int, default=4000)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rng = random.Random(SEED)

    uuids, starts, autopsy_pos, autopsy_seqs, holdout_ids = autopsy_sets()
    candidate_ids, candidate_fens = set(), set()
    with open(os.path.join(ROOT, "corpus/candidates.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if d.get("game_id"):
                candidate_ids.add(d["game_id"])
            if d.get("fen"):
                candidate_fens.add(fen4(d["fen"]))

    raw = load_repo_games()
    twic, twic_stats = load_twic(a.twic_games, candidate_ids, rng)
    counts = collections.Counter()
    games, seen = [], set()
    for g in raw + twic:
        mv = replay(g["start"], g["moves"])
        if mv is None:
            counts[f"unreplayable_{g['family']}"] += 1
            continue
        key = (fen4(g["start"]), tuple(m.uci() for m in mv))
        if key in seen:
            counts[f"duplicate_game_{g['family']}"] += 1
            continue
        seen.add(key)
        if g["gid"] in uuids or key in autopsy_seqs:
            counts[f"excluded_autopsy_game_{g['family']}"] += 1
            continue
        if fen4(g["start"]) in starts:
            counts[f"excluded_autopsy_start_family_{g['family']}"] += 1
            continue
        g["moves"] = mv
        s4 = fen4(g["start"])
        g["group"] = f"twic:{g['gid']}" if g["family"] == "TWIC" else (
            f"start:{s4}" if s4 != STANDARD4 else f"game:{g['source']}:{g['gid']}")
        g["split"] = split_of(g["group"])
        games.append(g)
        counts[f"games_{g['family']}"] += 1

    rows, skipped = [], collections.Counter()
    for g in games:
        picked, sk = sample_game(g, autopsy_pos, candidate_fens)
        skipped.update(sk)
        for ply, b in picked:
            phase, material = describe(b)
            rows.append(dict(pid=sha1(fen4(b.fen()))[:16], fen=b.fen(), fen4=fen4(b.fen()), family=g["family"],
                             source=g["source"], gid=g["gid"], group=g["group"], split=g["split"], ply=ply,
                             phase=phase, stm="w" if b.turn else "b", material=material,
                             halfmove=b.halfmove_clock, next_move=g["moves"][ply].uci()))
    rows.sort(key=lambda r: (SPLIT_PRIORITY[r["split"]], r["family"], r["gid"], r["ply"]))
    kept, by_key = [], {}
    for r in rows:
        if r["fen4"] in by_key:
            skipped[f"dedup_dropped_from_{r['split']}"] += 1
            continue
        by_key[r["fen4"]] = r
        kept.append(r)

    # Leakage audit: nothing from the holdout may survive in any split.
    leak = dict(
        uuid=sum(r["gid"] in uuids for r in kept),
        position=sum(r["fen4"] in autopsy_pos for r in kept),
        start_family=sum(1 for g in games if fen4(g["start"]) in starts),
        move_sequence=sum(1 for g in games if (fen4(g["start"]), tuple(m.uci() for m in g["moves"])) in autopsy_seqs),
    )
    assert not any(leak.values()), leak
    groups_by_split = collections.defaultdict(set)
    for r in kept:
        groups_by_split[r["split"]].add(r["group"])
    cross = {(x, y): len(groups_by_split[x] & groups_by_split[y])
             for x, y in (("train", "val"), ("train", "test"), ("val", "test"))}
    assert not any(cross.values()), cross

    with open(os.path.join(a.out, "pool.jsonl"), "w", encoding="utf-8") as fh:
        for r in kept:
            fh.write(json.dumps(r) + "\n")
    with open(os.path.join(a.out, "tasks.jsonl"), "w", encoding="utf-8") as fh:
        for r in kept:
            fh.write(json.dumps(dict(pid=r["pid"], fen=r["fen"])) + "\n")

    table = collections.Counter((r["family"], r["split"]) for r in kept)
    manifest = dict(
        seed=SEED, rule="sha1('20260911|'+group) mod 10: 0-7 train, 8 val, 9 test",
        per_game=PER_GAME, first_ply=FIRST_PLY, min_gap=MIN_GAP,
        positions=len(kept), games=len(games), groups={k: len(v) for k, v in groups_by_split.items()},
        by_family_split={f"{f}/{s}": n for (f, s), n in sorted(table.items())},
        by_split=dict(collections.Counter(r["split"] for r in kept)),
        phase_bands=dict(collections.Counter("mg>=16" if r["phase"] >= 16 else "8-15" if r["phase"] >= 8 else "<8"
                                             for r in kept)),
        game_counts=dict(counts), sampling_skips=dict(skipped), twic=twic_stats,
        holdout=dict(uuids=len(uuids), start_families=len(starts), positions=len(autopsy_pos), ids=holdout_ids),
        leakage=dict(leak, cross_split_groups={f"{x}-{y}": n for (x, y), n in cross.items()}),
        candidates_games_excluded=len(candidate_ids),
        inputs={rel: file_sha256(os.path.join(ROOT, rel)) for fam in REPO_SOURCES.values() for rel in fam},
        twic_files={n: file_sha256(os.path.join(TWIC_DIR, n)) for n in sorted(os.listdir(TWIC_DIR)) if n.endswith(".pgn")},
        pool_sha256=file_sha256(os.path.join(a.out, "pool.jsonl")),
    )
    with open(os.path.join(a.out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print(json.dumps({k: manifest[k] for k in ("positions", "games", "groups", "by_split", "by_family_split",
                                                 "phase_bands", "game_counts", "sampling_skips", "twic", "leakage")},
                     indent=1))


if __name__ == "__main__":
    main()
