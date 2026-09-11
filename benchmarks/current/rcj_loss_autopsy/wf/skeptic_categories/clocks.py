import json,glob,re,chess.pgn
for f in sorted(glob.glob('bundles/*.json')):
    d=json.load(open(f))
    dc=d['decisive']; dr=d['depth_repair']
    g=chess.pgn.read_game(open(d['pgn_path'],encoding='utf-8'))
    hdr=dict(g.headers)
    node=g; prev={chess.WHITE:None,chess.BLACK:None}
    col=chess.WHITE if d['rcj_colour']=='white' else chess.BLACK
    found=None; hist=[]
    while node.variations:
        nxt=node.variations[0]; b=node.board(); mover=b.turn
        clk=nxt.clock()
        if mover==col:
            spent=None if prev[mover] is None or clk is None else prev[mover]-clk
            hist.append((b.fullmove_number, nxt.move.uci(), clk, spent))
            if b.fullmove_number==dc['move_number'] and nxt.move.uci()==dc['played']:
                found=(b.fullmove_number,nxt.move.uci(),prev[mover],clk,spent)
        prev[mover]=clk if clk is not None else prev[mover]
        node=nxt
    tc=hdr.get('TimeControl')
    sp=[h[3] for h in hist if h[3] is not None]
    print(d['position_id'],'TC',tc,'live',found,'cold_timed_s',dr['cold_timed']['seconds'],'depth',dr['cold_timed']['depth'],'| median spent',sorted(sp)[len(sp)//2] if sp else None)
