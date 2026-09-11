import sys
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/wf/R101-29b_R102-10w')
from board_probe2 import files, st, mat, game, sqinfo
import chess
d, gb = game('R102-10w')
b = chess.Board(d['decisive']['fen'])
for u in d['decisive']['sf_best_pv']: b.push_uci(u)
print('best-line pv_end files', files(b)); print(b)
p = gb[(20, chess.WHITE)]
print('game before 20.Bb1 (after 19...Re2):'); print(p); print('static W view', st(p, chess.WHITE), 'mat', mat(p, chess.WHITE), sqinfo(p, 'e2'), sqinfo(p,'f2'))
