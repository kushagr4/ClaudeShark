"""E1 feature extractor, compiled with Numba over RC-J's own board arrays (cs_core layout).

One implementation serves training (batch over positions), the pairwise tests and the runtime
speed test: the code between the RUNTIME markers is appended verbatim (with the `C.` module
prefix removed) to a scratch copy of cs_core.py, so the features the model is fitted on are
exactly the ones a search computes. It allocates nothing per call: attack maps and counts are
scalars and tuples.

Every feature is relative to the side to move: a symmetric count is (side to move) - (opponent);
the four threat features are side-to-move specific. Mirroring a position (colours and ranks
swapped, other side to move) leaves the feature vector unchanged, which the tests assert.

Board layout (cs_core.py:14-25): B[1..6] white P N B R Q K, B[7..12] black; a1 = 0, h8 = 63.
"""
import os
import sys

import numpy as np
from numba import njit

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import cs_core as C  # noqa: E402

# --- RUNTIME BEGIN
E1_NAMES = (
    "pawn", "knight", "bishop", "rook", "queen",
    "mob_knight", "mob_bishop", "mob_rook", "mob_queen",
    "doubled", "isolated", "backward", "passed", "passed_advance", "protected_passed",
    "connected_passed", "chain_links",
    "rook_open", "rook_semi_open", "rook_seventh",
    "king_shelter", "king_open_files", "king_zone_attackers", "king_zone_attacked",
    "space", "outpost", "bishop_pair",
    "hanging_us", "hanging_them", "attacked_by_lower_us", "attacked_by_lower_them",
)
E1_NF = 31
E1_NSYM = 27  # the first 27 are (side to move - opponent); the last 4 are threat counts


def _e1_i64(bb):
    return bb - (1 << 64) if bb >= (1 << 63) else bb


def _e1_bit(f, r):
    return 1 << (r * 8 + f) if 0 <= f < 8 and 0 <= r < 8 else 0


E1_FILE = np.zeros(8, dtype=np.int64)
E1_ADJ = np.zeros(8, dtype=np.int64)
E1_FRONT = np.zeros((2, 64), dtype=np.int64)
E1_PASSED_SPAN = np.zeros((2, 64), dtype=np.int64)
E1_ATTACK_SPAN = np.zeros((2, 64), dtype=np.int64)
E1_SUPPORT_SPAN = np.zeros((2, 64), dtype=np.int64)
E1_REL_RANK = np.zeros((2, 64), dtype=np.int64)
E1_SHELTER = np.zeros((2, 64, 3), dtype=np.int64)
E1_KING_FILES = np.zeros((64, 3), dtype=np.int64)
E1_RANKS = np.zeros((2, 3), dtype=np.int64)  # [side][0 space ranks, 1 seventh rank, 2 outpost ranks]
for _e1f in range(8):
    E1_FILE[_e1f] = _e1_i64(sum(_e1_bit(_e1f, r) for r in range(8)))
for _e1f in range(8):
    E1_ADJ[_e1f] = _e1_i64(sum(_e1_bit(_e1f + d, r) for r in range(8) for d in (-1, 1)))
for _e1sq in range(64):
    _e1f, _e1r = _e1sq & 7, _e1sq >> 3
    for _e1s, _e1dir in ((0, 1), (1, -1)):
        _ahead = [r for r in range(8) if (r - _e1r) * _e1dir > 0]
        _behind = [r for r in range(8) if (r - _e1r) * _e1dir <= 0]
        E1_FRONT[_e1s, _e1sq] = _e1_i64(sum(_e1_bit(_e1f, r) for r in _ahead))
        E1_ATTACK_SPAN[_e1s, _e1sq] = _e1_i64(sum(_e1_bit(_e1f + d, r) for r in _ahead for d in (-1, 1)))
        E1_PASSED_SPAN[_e1s, _e1sq] = _e1_i64(sum(_e1_bit(_e1f + d, r) for r in _ahead for d in (-1, 0, 1)))
        E1_SUPPORT_SPAN[_e1s, _e1sq] = _e1_i64(sum(_e1_bit(_e1f + d, r) for r in _behind for d in (-1, 1)))
        E1_REL_RANK[_e1s, _e1sq] = _e1r if _e1s == 0 else 7 - _e1r
        for _e1i, _e1d in enumerate((-1, 0, 1)):
            E1_SHELTER[_e1s, _e1sq, _e1i] = _e1_i64(sum(_e1_bit(_e1f + _e1d, _e1r + k * _e1dir) for k in (1, 2)))
    for _e1i, _e1d in enumerate((-1, 0, 1)):
        E1_KING_FILES[_e1sq, _e1i] = E1_FILE[_e1f + _e1d] if 0 <= _e1f + _e1d < 8 else 0
for _e1s in range(2):
    _rel = (lambda r: r) if _e1s == 0 else (lambda r: 7 - r)
    E1_RANKS[_e1s, 0] = _e1_i64(sum(_e1_bit(f, _rel(r)) for f in range(8) for r in (4, 5)))
    E1_RANKS[_e1s, 1] = _e1_i64(sum(_e1_bit(f, _rel(6)) for f in range(8)))
    E1_RANKS[_e1s, 2] = _e1_i64(sum(_e1_bit(f, _rel(r)) for f in range(8) for r in (3, 4, 5)))


@njit(cache=False)
def e1_attacks(B, occ, side):
    """(all, pawn, knight, bishop, rook, queen, king) attack sets of one side."""
    sb = 6 * side
    ap = np.int64(0)
    an = np.int64(0)
    ab = np.int64(0)
    ar = np.int64(0)
    aq = np.int64(0)
    ak = np.int64(0)
    x = B[1 + sb]
    while x:
        sq = C.lsb(x)
        x &= x - 1
        ap |= C.PAWN_ATT[side, sq]
    x = B[2 + sb]
    while x:
        sq = C.lsb(x)
        x &= x - 1
        an |= C.KNIGHT_ATT[sq]
    x = B[3 + sb]
    while x:
        sq = C.lsb(x)
        x &= x - 1
        ab |= C.bishop_attacks(sq, occ)
    x = B[4 + sb]
    while x:
        sq = C.lsb(x)
        x &= x - 1
        ar |= C.rook_attacks(sq, occ)
    x = B[5 + sb]
    while x:
        sq = C.lsb(x)
        x &= x - 1
        aq |= C.rook_attacks(sq, occ) | C.bishop_attacks(sq, occ)
    if B[6 + sb]:
        ak = C.KING_ATT[C.lsb(B[6 + sb])]
    return (ap | an | ab | ar | aq | ak, ap, an, ab, ar, aq, ak)


@njit(cache=False)
def e1_side_counts(B, s, occ, A, OA):
    """Raw counts of side s (A its attack sets, OA the opponent's); indices follow E1_NAMES,
    with the two side-specific threat counts at 27 (hanging) and 29 (attacked by a lower piece)."""
    o = 1 - s
    base, obase = 6 * s, 6 * o
    own_p, opp_p = B[1 + base], B[1 + obase]
    own_occ = B[1 + base] | B[2 + base] | B[3 + base] | B[4 + base] | B[5 + base] | B[6 + base]

    safe = ~own_occ & ~OA[1]
    mob_n = np.int64(0)
    mob_b = np.int64(0)
    mob_r = np.int64(0)
    mob_q = np.int64(0)
    x = B[2 + base]
    while x:
        sq = C.lsb(x)
        x &= x - 1
        mob_n += C.popcount(C.KNIGHT_ATT[sq] & safe)
    x = B[3 + base]
    while x:
        sq = C.lsb(x)
        x &= x - 1
        mob_b += C.popcount(C.bishop_attacks(sq, occ) & safe)
    x = B[4 + base]
    while x:
        sq = C.lsb(x)
        x &= x - 1
        mob_r += C.popcount(C.rook_attacks(sq, occ) & safe)
    x = B[5 + base]
    while x:
        sq = C.lsb(x)
        x &= x - 1
        mob_q += C.popcount((C.rook_attacks(sq, occ) | C.bishop_attacks(sq, occ)) & safe)

    doubled = np.int64(0)
    isolated = np.int64(0)
    backward = np.int64(0)
    passed = np.int64(0)
    advance = np.int64(0)
    protected = np.int64(0)
    connected = np.int64(0)
    links = np.int64(0)
    passers = np.int64(0)
    x = own_p
    while x:
        sq = C.lsb(x)
        x &= x - 1
        bit = np.int64(1) << sq
        if E1_FRONT[s, sq] & own_p:
            doubled += 1
        iso = (E1_ADJ[sq & 7] & own_p) == 0
        if iso:
            isolated += 1
        stop = sq + 8 if s == 0 else sq - 8
        if (not iso) and (E1_SUPPORT_SPAN[s, sq] & own_p) == 0 and 0 <= stop < 64 \
                and (C.PAWN_ATT[s, stop] & opp_p):
            backward += 1
        if (E1_PASSED_SPAN[s, sq] & opp_p) == 0 and (E1_FRONT[s, sq] & own_p) == 0:
            passed += 1
            rr = E1_REL_RANK[s, sq]
            if rr > 1:
                advance += rr - 1
            if A[1] & bit:
                protected += 1
            passers |= bit
        if A[1] & bit:
            links += 1
    x = passers
    while x:
        sq = C.lsb(x)
        x &= x - 1
        if E1_ADJ[sq & 7] & passers:
            connected += 1

    r_open = np.int64(0)
    r_semi = np.int64(0)
    r_seventh = np.int64(0)
    x = B[4 + base]
    while x:
        sq = C.lsb(x)
        x &= x - 1
        fm = E1_FILE[sq & 7]
        if (fm & own_p) == 0:
            if (fm & opp_p) == 0:
                r_open += 1
            else:
                r_semi += 1
        if E1_RANKS[s, 1] & (np.int64(1) << sq):
            r_seventh += 1

    shelter = np.int64(0)
    k_open = np.int64(0)
    z_att = np.int64(0)
    z_sq = np.int64(0)
    if B[6 + base]:
        k = C.lsb(B[6 + base])
        for i in range(3):
            if E1_SHELTER[s, k, i] & own_p:
                shelter += 1
            if E1_KING_FILES[k, i] != 0 and (E1_KING_FILES[k, i] & own_p) == 0:
                k_open += 1
        zone = C.KING_ATT[k] | (np.int64(1) << k)
        y = B[2 + obase]
        while y:
            sq = C.lsb(y)
            y &= y - 1
            if C.KNIGHT_ATT[sq] & zone:
                z_att += 1
        y = B[3 + obase]
        while y:
            sq = C.lsb(y)
            y &= y - 1
            if C.bishop_attacks(sq, occ) & zone:
                z_att += 1
        y = B[4 + obase]
        while y:
            sq = C.lsb(y)
            y &= y - 1
            if C.rook_attacks(sq, occ) & zone:
                z_att += 1
        y = B[5 + obase]
        while y:
            sq = C.lsb(y)
            y &= y - 1
            if (C.rook_attacks(sq, occ) | C.bishop_attacks(sq, occ)) & zone:
                z_att += 1
        z_sq = C.popcount(zone & (OA[2] | OA[3] | OA[4] | OA[5]))

    space = C.popcount(own_p & E1_RANKS[s, 0])
    outpost = np.int64(0)
    x = (B[2 + base] | B[3 + base]) & E1_RANKS[s, 2] & A[1]
    while x:
        sq = C.lsb(x)
        x &= x - 1
        if (E1_ATTACK_SPAN[s, sq] & opp_p) == 0:
            outpost += 1
    bpair = np.int64(1) if C.popcount(B[3 + base]) >= 2 else np.int64(0)

    hanging = np.int64(0)
    lower = np.int64(0)
    minor_threat = OA[1]
    rook_threat = OA[1] | OA[2] | OA[3]
    queen_threat = rook_threat | OA[4]
    for pt in range(2, 6):
        y = B[pt + base]
        while y:
            sq = C.lsb(y)
            y &= y - 1
            bit = np.int64(1) << sq
            if (OA[0] & bit) and not (A[0] & bit):
                hanging += 1
            if pt <= 3:
                cheaper = minor_threat
            elif pt == 4:
                cheaper = rook_threat
            else:
                cheaper = queen_threat
            if cheaper & bit:
                lower += 1
    zero = np.int64(0)
    return (C.popcount(B[1 + base]), C.popcount(B[2 + base]), C.popcount(B[3 + base]),
            C.popcount(B[4 + base]), C.popcount(B[5 + base]),
            mob_n, mob_b, mob_r, mob_q,
            doubled, isolated, backward, passed, advance, protected, connected, links,
            r_open, r_semi, r_seventh,
            shelter, k_open, z_att, z_sq,
            space, outpost, bpair,
            hanging, zero, lower, zero)


@njit(cache=False)
def e1_phase(B):
    p = C.popcount(B[2] | B[8] | B[3] | B[9]) + 2 * C.popcount(B[4] | B[10]) + 4 * C.popcount(B[5] | B[11])
    return p if p < 24 else 24


@njit(cache=False)
def e1_counts(B, stm):
    occ = B[1] | B[2] | B[3] | B[4] | B[5] | B[6] | B[7] | B[8] | B[9] | B[10] | B[11] | B[12]
    aw = e1_attacks(B, occ, 0)
    ab = e1_attacks(B, occ, 1)
    if stm == 0:
        fs = e1_side_counts(B, 0, occ, aw, ab)
        fo = e1_side_counts(B, 1, occ, ab, aw)
    else:
        fs = e1_side_counts(B, 1, occ, ab, aw)
        fo = e1_side_counts(B, 0, occ, aw, ab)
    return fs, fo


@njit(cache=False)
def e1_correction(B, stm, W):
    """E1 correction in centipawns, side to move's view. W: [2*E1_NF + 2] float64 = the middlegame
    weights, the endgame weights, then the middlegame and endgame intercepts."""
    fs, fo = e1_counts(B, stm)
    mg = W[2 * E1_NF]
    eg = W[2 * E1_NF + 1]
    for j in range(E1_NSYM):
        d = fs[j] - fo[j]
        mg += W[j] * d
        eg += W[E1_NF + j] * d
    mg += W[27] * fs[27] + W[28] * fo[27] + W[29] * fs[29] + W[30] * fo[29]
    eg += W[E1_NF + 27] * fs[27] + W[E1_NF + 28] * fo[27] + W[E1_NF + 29] * fs[29] + W[E1_NF + 30] * fo[29]
    ph = e1_phase(B)
    return (mg * ph + eg * (24 - ph)) / 24.0
# --- RUNTIME END

NAMES = E1_NAMES
NF = E1_NF
N_SYM = E1_NSYM
phase_of = e1_phase
correction = e1_correction


@njit(cache=False)
def features(B, stm, x):
    """x[0..NF-1] <- stm-relative features of the position in B (stm 0 white, 1 black)."""
    fs, fo = e1_counts(B, stm)
    for j in range(E1_NSYM):
        x[j] = fs[j] - fo[j]
    x[27] = fs[27]
    x[28] = fo[27]
    x[29] = fs[29]
    x[30] = fo[29]


@njit(cache=False)
def features_batch(BB, STM, X, PH):
    x = np.zeros(E1_NF, dtype=np.int64)
    for n in range(BB.shape[0]):
        features(BB[n], STM[n], x)
        for j in range(E1_NF):
            X[n, j] = x[j]
        PH[n] = e1_phase(BB[n])


@njit(cache=False)
def e0_batch(BB, SS, OUT):
    for n in range(BB.shape[0]):
        OUT[n] = C.evaluate(BB[n], SS[n])


def arrays_from_boards(boards):
    """python-chess boards -> (B[N,13], S[N,8], stm[N]) in cs_core layout."""
    n = len(boards)
    BB = np.zeros((n, 13), dtype=np.int64)
    SS = np.zeros((n, 8), dtype=np.int64)
    B, O, M, S, _ = C.new_board_arrays()
    for i, b in enumerate(boards):
        C.load_board(b, B, O, M, S)
        BB[i] = B
        SS[i] = S
    return BB, SS, SS[:, 0].copy()


def extract(boards):
    """-> X[N,NF] int64 stm-relative features, phase[N], e0[N] (RC-J eval, stm cp)."""
    BB, SS, STM = arrays_from_boards(boards)
    X = np.zeros((len(boards), NF), dtype=np.int64)
    PH = np.zeros(len(boards), dtype=np.int64)
    E0 = np.zeros(len(boards), dtype=np.int64)
    features_batch(BB, STM, X, PH)
    e0_batch(BB, SS, E0)
    return X, PH, E0


def runtime_source():
    """The RUNTIME block with the module prefix removed, for appending to a copy of cs_core.py."""
    text = open(__file__, encoding="utf-8").read()
    block = text.split("# --- RUNTIME BEGIN", 1)[1].split("# --- RUNTIME END", 1)[0]
    return block.replace("C.", "")
