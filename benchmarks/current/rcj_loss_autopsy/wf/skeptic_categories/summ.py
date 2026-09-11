import json,glob,os
for f in sorted(glob.glob('bundles/*.json')):
    d=json.load(open(f))
    dr=d['depth_repair']; dc=d['decisive']; dos=d['dossier']
    print('=====',d['position_id'],d['selection_kind'],'played',dc['played'],dc['san'],'best',dc['sf_best_scan'],'E',dc['E_before'],dc['E_after'],'clock',dc['clock_in_s'])
    print(' cls',dr['cls'],'state_dep',dr['state_dependent'],'timed',dr['cold_timed'],'ladder',[(l['depth'],l['move'],l['loss_10M'],l['tag']) for l in dr['ladder']],'rcjv',dr['rcj_values'])
    lad=d['rcj_ladder']['ladder']; print(' scores',[(l['depth'],l['move'],l['score'],l['seconds']) for l in lad])
    v=d['verification_10M']; print(' 10M best',v['best']['move'],v['best']['cp'],{k:(m['cp'],m['loss_cp']) for k,m in v['moves'].items()})
    for ln in ('played_line','best_line'):
        L=dos[ln]
        a=L['after_move'];p=L['pv_end']
        print(' ',ln,'mat',L['material_path'],'| after: mob',a['features']['mob_own'],a['features']['mob_opp'],'ko',a['features']['king_own'],'st',a['rcj_static'],'ks',a['unshipped_terms']['king_safety'],'| end: mob',p['features']['mob_own'],p['features']['mob_opp'],'ko',p['features']['king_own'],'kopp',p['features']['king_opp'],'pw',p['features']['pawns_own'],p['features']['pawns_opp'],'st',p['rcj_static'],'un',p['unshipped_terms'])
    print(' pv played',dc['sf_played_pv'],' best',dc['sf_best_pv'])
    if d.get('other_errors_ge100_while_not_lost'): print(' other',json.dumps(d['other_errors_ge100_while_not_lost'])[:600])
    for k in d:
        if k.startswith('supplementary'): print(' supp',json.dumps(d[k])[:1500])
