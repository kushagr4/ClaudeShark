"""Build the four LMR-exemption variants that isolate the C15 slowdown.

All four compute the same predicate -- "this quiet non-promoting move is a pawn
arriving on the sixth rank or beyond, so do not reduce it" -- and therefore
search identical trees. They differ only in where the information is read from
and how long it has to stay alive across the recursive calls, which is the only
thing being measured here.

v0  RC-I, no exemption at all (control)
v1  C15 exactly: mailbox read before make_move, value live across two calls
v2  the "cheaper" rewrite: read the piece back off the bitboards after make_move
v3  C15-v2: one loop-invariant bitboard of eligible from-squares, tested inside
    the existing short-circuit chain
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

ORIGINAL_BLOCK = """        reduction = 0
        if (move_index >= LMR_START and can_reduce and not is_capture and promo == 0
                and move != killer_1 and move != killer_2):
            if move_index >= LMR_R2_INDEX and depth >= LMR_R2_DEPTH:
                reduction = 2
            else:
                reduction = 1
            if reduction > child_depth - 1:
                reduction = child_depth - 1
            if reduction > 0 and in_check(B, O, S):
                reduction = 0
"""

BODY = """            if move_index >= LMR_R2_INDEX and depth >= LMR_R2_DEPTH:
                reduction = 2
            else:
                reduction = 1
            if reduction > child_depth - 1:
                reduction = child_depth - 1
            if reduction > 0 and in_check(B, O, S):
                reduction = 0
"""

V1_BLOCK = """        reduction = 0
        if (move_index >= LMR_START and can_reduce and not is_capture and promo == 0
                and move != killer_1 and move != killer_2):
            advanced_push = False
            if mover == 1 + 6 * side:
                to_rank = (to >> 3) if side == 0 else 7 - (to >> 3)
                advanced_push = to_rank >= 5
            if not advanced_push:
""" + "".join("    " + line if line.strip() else line for line in BODY.splitlines(True))

V2_BLOCK = """        reduction = 0
        if (move_index >= LMR_START and can_reduce and not is_capture and promo == 0
                and move != killer_1 and move != killer_2):
            to_rank = (to >> 3) if side == 0 else 7 - (to >> 3)
            if to_rank < 5 or ((np.int64(1) << to) & B[1 + base]) == 0:
""" + "".join("    " + line if line.strip() else line for line in BODY.splitlines(True))

V3_BLOCK = """        reduction = 0
        if (move_index >= LMR_START and can_reduce and not is_capture and promo == 0
                and move != killer_1 and move != killer_2
                and ((np.int64(1) << (move & 63)) & adv_pawns) == 0):
""" + BODY

ADV_CONST = """
# From-squares of a quiet pawn push that lands on the sixth rank or beyond: the
# fifth and sixth ranks for White, the fourth and third for Black. A push from
# the seventh promotes, and promotions are never reduced anyway, so those
# squares are deliberately absent.
ADV_PUSH_SRC = np.array([0x0000FFFF00000000, 0x00000000FFFF0000], dtype=np.int64)

"""


def patch(path, block, *, mover_line=False, adv_pawns=False, const=False):
    src = open(path, encoding="utf-8").read()
    assert ORIGINAL_BLOCK in src, path
    src = src.replace(ORIGINAL_BLOCK, block)
    if mover_line:
        src = src.replace(
            "        is_capture = ((np.int64(1) << to) & enemy) != 0 or (flags & FLAG_EP) != 0\n",
            "        is_capture = ((np.int64(1) << to) & enemy) != 0 or (flags & FLAG_EP) != 0\n"
            "        mover = M[fr]\n", 1)
    if adv_pawns:
        src = src.replace(
            "    can_reduce = depth >= 3 and not checked\n",
            "    can_reduce = depth >= 3 and not checked\n"
            "    adv_pawns = B[1 + base] & ADV_PUSH_SRC[side]\n", 1)
    if const:
        src = src.replace("\n# ------------------------------------------------------------- bit helpers",
                          ADV_CONST + "\n# ------------------------------------------------------------- bit helpers", 1)
    open(path, "w", encoding="utf-8", newline="\r\n").write(src)


patch(os.path.join(HERE, "v1", "cs_core.py"), V1_BLOCK, mover_line=True)
patch(os.path.join(HERE, "v2", "cs_core.py"), V2_BLOCK)
patch(os.path.join(HERE, "v3", "cs_core.py"), V3_BLOCK, adv_pawns=True, const=True)
print("v1, v2, v3 patched; v0 left as the RC-I control")
