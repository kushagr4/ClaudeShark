import sys, time, json, os
sys.path.insert(0, r"C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/rcf_prof")
import numpy as np, chess
import cs_core as core
from numba import njit
REPO=r"C:/Users/epick/Documents/ClaudeShark"
fens=[json.loads(l)["fen"] for l in open(os.path.join(REPO,"corpus","competition_like_v1.jsonl"),encoding="utf-8") if '"fen"' in l][:200]
B,O,M,St,U=core.new_board_arrays()
N=len(fens); BB=np.zeros((N,13),np.int64); OO=np.zeros((N,3),np.int64); MM=np.zeros((N,64),np.int64); SS=np.zeros((N,8),np.int64)
for i,f in enumerate(fens):
    core.load_board(chess.Board(f),B,O,M,St); BB[i]=B; OO[i]=O; MM[i]=M; SS[i]=St
ML=np.zeros(256,np.int64); MS=np.zeros(256,np.int64); HIST=np.zeros(8192,np.int64); GAINS=np.zeros(40,np.int64); CTL=np.zeros(16,np.int64)
MLS=np.zeros((core.STACK,256),np.int64); MSS=np.zeros((core.STACK,256),np.int64); PATH=np.zeros(core.STACK,np.int64); GK=np.zeros(1024,np.int64)
TK=np.zeros(1<<core.TT_BITS,np.int64); TV=np.zeros(1<<core.TT_BITS,np.int64); KILL=np.zeros(2*core.STACK,np.int64); TCTL=np.zeros(2,np.float64)

@njit(cache=False)
def k_score_only(BB,OO,MM,SS,ML,MS,HIST,GAINS,CTL,reps):
    acc=0
    for r in range(reps):
        for i in range(BB.shape[0]):
            n=core.gen_moves(BB[i],OO[i],MM[i],SS[i],ML,False)
            core.score_moves(BB[i],OO[i],MM[i],SS[i],ML,MS,n,0,0,0,HIST,GAINS,CTL); acc+=MS[0]
    return acc
@njit(cache=False)
def k_gen_only(BB,OO,MM,SS,ML,reps):
    acc=0
    for r in range(reps):
        for i in range(BB.shape[0]):
            acc+=core.gen_moves(BB[i],OO[i],MM[i],SS[i],ML,False)
    return acc
@njit(cache=False)
def k_pick(ML,MS,n,reps,k):
    acc=0
    for r in range(reps):
        for j in range(k):
            acc+=core.pick_next(ML,MS,n,j)
    return acc
@njit(cache=False)
def callee(B,O,M,S,U,MLS,MSS,PATH,GK,TK,TV,KILL,HIST,CTL,TCTL,GAINS,depth,alpha,beta,ply,allow):
    return depth+alpha
@njit(cache=False)
def k_calls(B,O,M,S,U,MLS,MSS,PATH,GK,TK,TV,KILL,HIST,CTL,TCTL,GAINS,reps):
    acc=0
    for r in range(reps):
        acc+=callee(B,O,M,S,U,MLS,MSS,PATH,GK,TK,TV,KILL,HIST,CTL,TCTL,GAINS,r,1,2,3,True)
    return acc
@njit(cache=False)
def callee2(B,depth,alpha):
    return depth+alpha+B[0]
@njit(cache=False)
def k_calls2(B,reps):
    acc=0
    for r in range(reps):
        acc+=callee2(B,r,1)
    return acc
def t(fn,*a):
    fn(*a); t0=time.perf_counter(); fn(*a); return time.perf_counter()-t0
REPS=200
tg=t(k_gen_only,BB,OO,MM,SS,ML,REPS); ts=t(k_score_only,BB,OO,MM,SS,ML,MS,HIST,GAINS,CTL,REPS)
n=core.gen_moves(BB[0],OO[0],MM[0],SS[0],ML,False); core.score_moves(BB[0],OO[0],MM[0],SS[0],ML,MS,n,0,0,0,HIST,GAINS,CTL)
tp_all=t(k_pick,ML.copy(),MS.copy(),n,20000,n); tp_3=t(k_pick,ML.copy(),MS.copy(),n,20000,3)
tc=t(k_calls,B,O,M,St,U,MLS,MSS,PATH,GK,TK,TV,KILL,HIST,CTL,TCTL,GAINS,20_000_000)
tc2=t(k_calls2,B,20_000_000)
print(f"score_moves per list (avg 33 moves): {(ts-tg)/(REPS*N)*1e6:.3f} us; pick_next full selection of {n} moves: {tp_all/20000*1e6:.3f} us, first 3 picks: {tp_3/20000*1e6:.3f} us")
print(f"call with 16 arrays + 5 scalars: {tc/20e6*1e9:.1f} ns per call; call with 1 array + 2 scalars: {tc2/20e6*1e9:.1f} ns per call")
