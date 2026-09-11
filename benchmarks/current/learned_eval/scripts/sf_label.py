"""Resumable Stockfish labeller for the learned-evaluation project (offline tool only).

Input  : JSONL tasks, one per line: {"pid": str, "fen": str, "searchmoves": [uci, ...] (optional)}
Output : JSONL labels appended by ONE writer (this process). A pid already present in the
         output is never relabelled, so an interrupted run resumes where it stopped.

Each worker process owns one Stockfish (Threads=1, fixed Hash, UCI_ShowWDL) and, for every
position, sends `ucinewgame` so no search state carries over between positions, then
`go nodes N`. The label is the LAST info line that carries an exact score (no lowerbound /
upperbound) - the same convention as the RC-J loss autopsy.

Sign conventions (Stockfish, side to move):
  score cp X    : X centipawns for the side to move
  score mate N  : N > 0 side to move mates in N moves; N < 0 side to move is mated;
                  N == 0 only for a position that is already checkmate (side to move mated)
  wdl W D L     : per-mille win / draw / loss for the side to move
  E = (W + D/2) / 1000 is the expected score for the side to move, in [0, 1].

Usage:
  python sf_label.py TASKS.jsonl OUT.jsonl --nodes 100000 --workers 10 [--hash 16] [--limit N]
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import subprocess
import sys
import time

SF_DEFAULT = "C:/Users/epick/engines/stockfish/stockfish-windows-x86-64-avx2.exe"

_sf = None
_cfg = None


class Engine:
    def __init__(self, path, hash_mb):
        self.p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.send("uci")
        self.wait_for("uciok")
        for name, value in (("Threads", 1), ("Hash", hash_mb), ("UCI_ShowWDL", "true")):
            self.send(f"setoption name {name} value {value}")
        self.send("isready")
        self.wait_for("readyok")

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def wait_for(self, token):
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("stockfish exited")
            if line.startswith(token):
                return line

    def label(self, fen, nodes, searchmoves=None):
        self.send("ucinewgame")
        self.send("isready")
        self.wait_for("readyok")
        self.send(f"position fen {fen}")
        go = f"go nodes {nodes}"
        if searchmoves:
            go += " searchmoves " + " ".join(searchmoves)
        self.send(go)
        last = None
        t0 = time.perf_counter()
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("stockfish exited")
            if line.startswith("info ") and " score " in line:
                tok = line.split()
                if "lowerbound" in tok or "upperbound" in tok:
                    continue
                if "multipv" in tok and tok[tok.index("multipv") + 1] != "1":
                    continue
                last = tok
            elif line.startswith("bestmove"):
                best = line.split()[1]
                break
        return parse(last, best, time.perf_counter() - t0)

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def parse(tok, best, seconds):
    out = dict(bestmove=None if best in ("(none)", "0000") else best, seconds=round(seconds, 4))
    if tok is None:
        out.update(depth=0, nodes=0, cp=None, mate=None, wdl=None, E=None, pv=[])
        return out

    def after(key, n=1, cast=int):
        i = tok.index(key)
        vals = tok[i + 1:i + 1 + n]
        return cast(vals[0]) if n == 1 else [cast(v) for v in vals]

    out["depth"] = after("depth") if "depth" in tok else None
    out["seldepth"] = after("seldepth") if "seldepth" in tok else None
    out["nodes"] = after("nodes") if "nodes" in tok else None
    i = tok.index("score")
    kind, val = tok[i + 1], int(tok[i + 2])
    out["cp"] = val if kind == "cp" else None
    out["mate"] = val if kind == "mate" else None
    out["wdl"] = after("wdl", 3) if "wdl" in tok else None
    if out["wdl"]:
        w, d, l = out["wdl"]
        out["E"] = round((w + d / 2) / 1000, 4)
    elif out["mate"] is not None:
        out["E"] = 1.0 if out["mate"] > 0 else 0.0
    elif out["bestmove"] is None and out["cp"] == 0:
        out["E"] = 0.5  # no legal move and not mated: stalemate
    else:
        out["E"] = None
    out["pv"] = tok[tok.index("pv") + 1:tok.index("pv") + 5] if "pv" in tok else []
    return out


def _init(cfg):
    global _sf, _cfg
    _cfg = cfg
    _sf = Engine(cfg["sf"], cfg["hash"])


def _work(task):
    lab = _sf.label(task["fen"], _cfg["nodes"], task.get("searchmoves"))
    lab["pid"] = task["pid"]
    lab["fen"] = task["fen"]
    if task.get("searchmoves"):
        lab["searchmoves"] = task["searchmoves"]
    lab["budget_nodes"] = _cfg["nodes"]
    return lab


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks")
    ap.add_argument("out")
    ap.add_argument("--nodes", type=int, required=True)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--hash", type=int, default=16)
    ap.add_argument("--sf", default=SF_DEFAULT)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    done = set()
    if os.path.exists(a.out):
        with open(a.out, encoding="utf-8") as fh:
            for line in fh:
                try:
                    done.add(json.loads(line)["pid"])
                except (ValueError, KeyError):
                    pass  # a torn final line from an interrupted run is ignored and relabelled
    tasks = []
    with open(a.tasks, encoding="utf-8") as fh:
        for line in fh:
            t = json.loads(line)
            if t["pid"] not in done:
                tasks.append(t)
    if a.limit:
        tasks = tasks[:a.limit]
    meta = dict(sf=a.sf, sf_sha256=sha256(a.sf), nodes=a.nodes, hash=a.hash, workers=a.workers,
                tasks_file=a.tasks, already_done=len(done), to_do=len(tasks),
                started=time.strftime("%Y-%m-%d %H:%M:%S"))
    with open(a.out + ".meta.json", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(meta) + "\n")
    print(json.dumps(meta), flush=True)
    if not tasks:
        return 0
    cfg = dict(sf=a.sf, hash=a.hash, nodes=a.nodes)
    t0 = time.perf_counter()
    n = 0
    with mp.Pool(a.workers, initializer=_init, initargs=(cfg,)) as pool, \
            open(a.out, "a", encoding="utf-8") as out:
        for lab in pool.imap_unordered(_work, tasks, chunksize=4):
            out.write(json.dumps(lab) + "\n")
            n += 1
            if n % 200 == 0:
                out.flush()
                el = time.perf_counter() - t0
                print(f"PROGRESS {n}/{len(tasks)} {n / el:.1f} pos/s elapsed {el:.0f}s "
                      f"eta {(len(tasks) - n) / (n / el):.0f}s", flush=True)
    el = time.perf_counter() - t0
    print(f"DONE {n} positions in {el:.1f}s = {n / el:.2f} pos/s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
