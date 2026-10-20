#!/usr/bin/env python3
"""fork-fixtures pod placer v2 (pure Python, no numpy). Low fidelity: pods = top-plate footprint boxes Z-100..0.
Inputs : scan/toolpaths.jsonl (podscan.cps), scan/outline.json (scan_setup.py), ../rails_layout.json, ../rail_map.json, place_cfg.json
Outputs: <out>/layout.json, <out>/layout.txt, <out>/layout.png
Frames : WCS = Fusion setup WCS (mm, Z+ up, origin stock top-left-front corner 'top 1').
         sim = machine-sim table frame: Z0 = pod top = panel bottom; front (operator, I stops) = sim -Y (logo side).
         rail scale M (mm) = 650 - simY  (M0 = back/park end, I-stop face M1217, front end ~M1300..1306).
         sim X = machine(ventose) X - 407.5 ; rail X in ventose.prm taken as the rail's X- edge [guess]."""
import json, math, os, sys, zlib, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE=os.path.dirname(os.path.abspath(__file__)); FF=os.path.dirname(HERE)
cfgp=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,'place_cfg.json')
C=json.load(open(cfgp)); L=json.load(open(os.path.join(FF,'rails_layout.json'))); RM=json.load(open(os.path.join(FF,'rail_map.json')))
SD=os.path.join(HERE,C['scan_dir']); OD=os.path.join(HERE,C['out_dir']); os.makedirs(OD,exist_ok=True)
# ---------- scan ----------
wp=None; secs=[]; cur=None
for line in open(os.path.join(SD,'toolpaths.jsonl')):
    line=line.strip()
    if not line.startswith('{'): continue
    d=json.loads(line)
    if d['t']=='wp': wp=d
    elif d['t']=='sec': cur=dict(d,moves=[]); secs.append(cur)
    elif d['t']=='m' and cur is not None: cur['moves'].append(d)
OL=json.load(open(os.path.join(SD,'outline.json')))
zb=OL['z_bottom']
lo,hi=wp['lo'],wp['hi']
if C['placement_mode']=='setup':
    off=((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2])          # WCS point that lands on the sim origin
else:
    yst=L['sim_y_of_M0']+L['sim_y_dir']*L['stops_M']['S1_IJ_face']   # I-stop face in sim (-567)
    off=((lo[0]+hi[0])/2, lo[1]-yst, lo[2])                # front edge (WCS ymin) on the I-stop face
def w2s(x,y,z=0): return (x-off[0],y-off[1],z-off[2])
zplane=zb-off[2]   # = 0 normally
# ---------- panel polygon(s) in sim ----------
loops=[[w2s(p[0],p[1])[:2] for p in lp['pts']] for lp in OL['loops']]
allx=[p[0] for lp in loops for p in lp]; ally=[p[1] for lp in loops for p in lp]
px0,px1,py0,py1=min(allx),max(allx),min(ally),max(ally)
G=C['grid']; MARG=150
gx0=math.floor((px0-MARG)/G)*G; gy0=math.floor((py0-MARG)/G)*G
NX=int((px1+MARG-gx0)/G)+1; NY=int((py1+MARG-gy0)/G)+1
def inside(x,y):
    c=False
    for lp in loops:
        n=len(lp)
        for i in range(n):
            (x1,y1),(x2,y2)=lp[i],lp[(i+1)%n]
            if (y1>y)!=(y2>y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1: c=not c
    return c
INS=[[inside(gx0+(i+0.5)*G, gy0+(j+0.5)*G) for i in range(NX)] for j in range(NY)]
# seal margin: erode
sm=C['seal_margin']
if sm>0:
    k=int(math.ceil(sm/G)); E=[[INS[j][i] and all(INS[jj][ii] for jj in range(max(0,j-k),min(NY,j+k+1)) for ii in range(max(0,i-k),min(NX,i+k+1))) for i in range(NX)] for j in range(NY)]; INS=E
# ---------- keep-out (soft: R + clearance; through: R + through_clearance) ----------
KO=[[0]*NX for _ in range(NY)]   # 0 none, 1 soft, 2 through
clr=C['clearance']; tclr=C['through_clearance']
def stamp(x,y,r,v):
    i0=max(0,int((x-r-gx0)/G)); i1=min(NX-1,int((x+r-gx0)/G)); j0=max(0,int((y-r-gy0)/G)); j1=min(NY-1,int((y+r-gy0)/G))
    r2=(r+G*0.71)**2
    for j in range(j0,j1+1):
        cy=gy0+(j+0.5)*G; row=KO[j]
        for i in range(i0,i1+1):
            if row[i]>=v: continue
            cx=gx0+(i+0.5)*G
            if (cx-x)**2+(cy-y)**2<=r2: row[i]=v
ko_secs={}
for s in secs:
    R=s['D']/2; body=s['body'] or 100; HR=max(R,C['holder_radius_assumed'])
    rt,up,fw,org=s['right'],s['up'],s['fwd'],s['org']
    def g(p): return [org[k]+p[0]*rt[k]+p[1]*up[k]+p[2]*fw[k] for k in range(3)]
    a=fw; az=max(1e-6,a[2]); sinT=math.sqrt(max(0,1-az*az))
    pts=[g(m['p']) for m in s['moves'] if m['k'] in ('l','r')]
    n5=sum(1 for m in s['moves'] if m['k'] in ('l5','r5'))
    if n5: print('WARN 5-axis moves ignored in section',s['i'],n5)
    hit=[0,0]; last=None
    for k in range(1,len(pts)):
        p0,p1=pts[k-1],pts[k]
        if min(p0[2],p1[2]) - sinT*HR > zb+clr: continue
        L2=math.dist(p0,p1); ns=max(1,int(L2/1.5))
        for q in range(ns+1):
            u=q/ns; P=[p0[c]+(p1[c]-p0[c])*u for c in range(3)]
            if last and math.dist(P,last)<1.0: continue
            last=P
            thru = (P[2]-sinT*R) < zb-0.05
            t=0.0
            while True:
                rr=R if t<=body else HR
                zl=P[2]+a[2]*t - sinT*rr
                if zl>zb+clr or t>body+300: break
                sx,sy,_=w2s(P[0]+a[0]*t, P[1]+a[1]*t)
                if thru: stamp(sx,sy,rr+tclr,2); hit[1]+=1
                else: stamp(sx,sy,rr+clr,1); hit[0]+=1
                t+=2.0
    ko_secs[s['op']]=hit
BAD=[[1 if (not INS[j][i]) or KO[j][i] else 0 for i in range(NX)] for j in range(NY)]
PS=[[0]*(NX+1) for _ in range(NY+1)]
for j in range(NY):
    acc=0
    for i in range(NX):
        acc+=BAD[j][i]; PS[j+1][i+1]=PS[j][i+1]+acc
def rect_bad(x0,x1,y0,y1):
    i0=int(math.floor((x0-gx0)/G)); i1=int(math.ceil((x1-gx0)/G))-1; j0=int(math.floor((y0-gy0)/G)); j1=int(math.ceil((y1-gy0)/G))-1
    if i0<0 or j0<0 or i1>=NX or j1>=NY: return True
    return PS[j1+1][i1+1]-PS[j0][i1+1]-PS[j1+1][i0]+PS[j0][i0] > 0
# ---------- rails / pods ----------
rw=L['rail']['width']; rlen=L['rail']['length']
def simY(M): return L['sim_y_of_M0']+L['sim_y_dir']*M
ports=[p['M'] for p in RM['ports']]
zones=[z['M'] for z in RM['pod_y_placement']['caution_zones_for_pod_base']]
types=[]
for t in RM['pods']['types']:
    types.append(dict(name=t['name'],art=t['art'],along=t['top_along'],across=t['top_across'],off=t['top_offset_from_port'],count=t['count']))
BASE=140.0; gap=C['pod_gap']
def windows_ok(b):
    if b<0 or b+BASE>rlen: return False
    for z0,z1 in zones:
        if b<z1 and b+BASE>z0: return False
    return any(b+13.5 <= pm-8.5+0.001 and pm+8.5 <= b+126.5+0.001 for pm in ports) or any(pm-8.5>=b+5 and pm+8.5<=b+BASE-5 for pm in ports)
bases=[]; b=0.0
while b<=rlen-BASE:
    if windows_ok(b): bases.append(b)
    b+=C['base_step']
def pod_rect(xedge,tp,rot,b):
    xc=xedge+rw/2; mc=b+BASE/2+(tp['off'] if rot==0 else -tp['off'])
    m0,m1=mc-tp['along']/2, mc+tp['along']/2
    y0,y1=sorted((simY(m0),simY(m1)))
    return (xc-tp['across']/2, xc+tp['across']/2, y0, y1)
def cands(xedge):
    out=[]
    for ti,tp in enumerate(types):
        for rot in (0,180):
            for b in bases:
                r=pod_rect(xedge,tp,rot,b)
                if r[1]<px0 or r[0]>px1 or r[3]<py0 or r[2]>py1: continue
                if rect_bad(*r): continue
                out.append(dict(ti=ti,rot=rot,b=b,rect=r,area=(r[1]-r[0])*(r[3]-r[2])))
    return out
def polyarea(lp): return abs(sum(lp[i][0]*lp[(i+1)%len(lp)][1]-lp[(i+1)%len(lp)][0]*lp[i][1] for i in range(len(lp))))/2
panel_area=sum(polyarea([tuple(p) for p in lp])*(1 if OL['loops'][i]['outer'] else -1) for i,lp in enumerate(loops))
def hull(pts):
    pts=sorted(set(pts))
    if len(pts)<3: return pts
    def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo_,up_=[],[]
    for p in pts:
        while len(lo_)>=2 and cr(lo_[-2],lo_[-1],p)<=0: lo_.pop()
        lo_.append(p)
    for p in reversed(pts):
        while len(up_)>=2 and cr(up_[-2],up_[-1],p)<=0: up_.pop()
        up_.append(p)
    return lo_[:-1]+up_[:-1]
ET=C['extreme_tolerance']
def centroid(lps):
    A=cx=cy=0.0
    for i,lp in enumerate(lps):
        sg=1 if OL['loops'][i]['outer'] else -1
        for j in range(len(lp)):
            (x0,y0),(x1,y1)=lp[j],lp[(j+1)%len(lp)]; c=x0*y1-x1*y0
            A+=sg*c; cx+=sg*(x0+x1)*c; cy+=sg*(y0+y1)*c
    return (cx/(3*A), cy/(3*A))
PC_=centroid(loops); NDIR=C.get('balance_directions',16)
DIRS=[(math.cos(2*math.pi*i/NDIR),math.sin(2*math.pi*i/NDIR)) for i in range(NDIR)]
PANEL_H=[max((q[0]-PC_[0])*u[0]+(q[1]-PC_[1])*u[1] for lp in loops for q in lp) for u in DIRS]
def balance(hp):
    """min over directions u of  h_support(u)/h_panel(u), both measured from the panel centroid.
    1 = support polygon reaches the panel edge in every direction; <=0 = centroid outside the support polygon."""
    return min(max((p[0]-PC_[0])*u[0]+(p[1]-PC_[1])*u[1] for p in hp)/PANEL_H[i] for i,u in enumerate(DIRS))
def idle_under(X,sub):
    return sum(1 for k in (1,2,3,4) if k not in sub and X[k]<px1 and X[k]+rw>px0)
def overl(c1,c2): return not (c1['b']+BASE+gap<=c2['b'] or c2['b']+BASE+gap<=c1['b'])
pick_cache={}
def rail_pick(x,kp):
    """kp pods spread along the rail: front-most, back-most (+ middle). Largest top plate near each extreme."""
    key=(round(x,1),kp)
    if key in pick_cache: return pick_cache[key]
    cs=cands(x); res=None
    if cs:
        def best_near(target_key, val, exclude):
            ok=[c for c in cs if abs(target_key(c)-val)<=ET and all(not overl(c,e) for e in exclude)]
            return max(ok,key=lambda c:(c['area'],-abs(target_key(c)-val))) if ok else None
        yfront=min(c['rect'][2] for c in cs); f=best_near(lambda c:c['rect'][2], yfront, [])
        rest=[c for c in cs if not overl(c,f)]
        if rest:
            yback=max(c['rect'][3] for c in rest); bk=best_near(lambda c:c['rect'][3], yback, [f])
            sel=[f,bk] if bk else None
            if sel and kp==3:
                ym=(f['rect'][2]+bk['rect'][3])/2
                mid=[c for c in cs if not overl(c,f) and not overl(c,bk)]
                if mid:
                    m=min(mid,key=lambda c:(abs((c['rect'][2]+c['rect'][3])/2-ym),-c['area'])); sel=[f,m,bk]
                else: sel=None
            res=sel
    pick_cache[key]=res; return res
x0s=L['sim_x0']
rng=RM['rails_layout'].get('x_travel_min_max',RM['rails_layout']['ventose_x_min_max'])  # travel limits (15:37); ventose max = crossover
lims={k:(rng[str(k)][0]+x0s, rng[str(k)][1]+x0s) for k in (1,2,3,4)}
gapmin={2:135.0,3:175.0,4:175.0}
PARK=C.get('park_mode','max_travel')
pmax={k:(C.get('park_x_machine',{}).get(str(k),rng[str(k)][1])+x0s) for k in (1,2,3,4)}
def place_all(used):
    """used: {rail:x}. Returns x for rails 1..4 or None. Unused rails: before the first used rail packed at min X;
    between used rails packed behind the previous one (they cannot leave: rails do not pass);
    after the last used rail: park_mode 'max_travel' (Johannes 15:16) = stacked at the max-travel end (last rail at its
    ventose X max / park_x_machine, the others behind it at the minimum edge spacing); 'past_panel' = v2 behaviour."""
    X={}
    ks=sorted(used)
    if PARK=='max_travel' and ks and max(ks)<4:
        tail={}
        for k in range(4,max(ks),-1):
            tail[k]=pmax[k] if k==4 else min(pmax[k], tail[k+1]-gapmin[k+1])
    else: tail={}
    for k in (1,2,3,4):
        lo_=lims[k][0] if k==1 else max(lims[k][0], X[k-1]+gapmin[k])
        if k in used:
            if used[k]<lo_-1e-6 or used[k]>lims[k][1]: return None
            X[k]=used[k]
        else:
            nxt=[u for u in ks if u>k]
            if not nxt and ks and k>max(ks) and tail:
                X[k]=tail[k]
                if X[k]<lo_-1e-6: return None
            elif not nxt and ks and k>max(ks):
                want=max(lo_, px1+5)
                X[k]=want if want<=lims[k][1] else lo_
            else:
                X[k]=lo_
        if X[k]>lims[k][1]: return None
    # check spacing to the next used rails (packed chain must fit)
    for k in (2,3,4):
        if X[k]-X[k-1]<gapmin[k]-1e-6: return None
    return X
import itertools, math as _m
target=max(C['min_pods'],min(C['max_pods'],_m.ceil(panel_area/1e6/C['area_per_pod_m2'])))
st=C['search_x_step']
xgrid={k:[lims[k][0]+i*st for i in range(int((lims[k][1]-lims[k][0])/st)+1)] for k in (1,2,3,4)}
for k in xgrid: xgrid[k]=[x for x in xgrid[k] if x+rw>=px0 and x<=px1]
best=None; tried=0
levels=sorted({nr*kp for nr in range(C['min_rails'],C['max_rails']+1) for kp in C['pods_per_rail'] if target<=nr*kp<=C['max_pods']})
for npods in levels:
    for nr in range(C['min_rails'],C['max_rails']+1):
        for kp in C['pods_per_rail']:
            if nr*kp!=npods: continue
            for sub in itertools.combinations((1,2,3,4),nr):
                for xs in itertools.product(*[xgrid[k] for k in sub]):
                    if any(xs[i+1]<=xs[i] for i in range(len(xs)-1)): continue
                    used=dict(zip(sub,xs)); X=place_all(used)
                    if X is None: continue
                    pods=[]; ok=True
                    for k in sub:
                        pk=rail_pick(used[k],kp)
                        if not pk: ok=False; break
                        pods+= [dict(c,rail=k) for c in pk]
                    if not ok: continue
                    tried+=1
                    pts=[(r[a],r[b]) for c in pods for r in [c['rect']] for a in (0,1) for b in (2,3)]
                    hp=hull(pts); ha=polyarea(hp) if len(hp)>=3 else 0
                    hx=(max(p[0] for p in pts)-min(p[0] for p in pts))/(px1-px0); hy=(max(p[1] for p in pts)-min(p[1] for p in pts))/(py1-py0)
                    if ha/panel_area<C['hull_min_fraction'] or min(hx,hy)<C['span_min_fraction']: continue
                    bal=balance(hp)
                    if bal<C.get('balance_min',0.0): continue
                    key=(-npods,int(bal/C['balance_bin']),int(hx/0.05),int(hy/0.05),-nr,sum(c['area'] for c in pods),bal)
                    if best is None or key>best[0]: best=(key,X,pods,hp,ha,hx,hy,sub,kp)
    if best: break
if not best:
    print('NO LAYOUT meets the support rules (target %d pods). Relax hull_min_fraction / span_min_fraction / max_pods.'%target); sys.exit(2)
key,X,pods,hp,ha,hx,hy,sub,kp=best
# inventory: give the largest available type at each chosen spot
caps=[t['count'] for t in types]
final=[]
for c in sorted(pods,key=lambda c:-c['area']):
    k=c['rail']
    if caps[c['ti']]>0: caps[c['ti']]-=1; final.append(c); continue
    alt=[a for a in cands(X[k]) if caps[a['ti']]>0 and abs(a['b']-c['b'])<=ET and all(not overl(a,o) for o in final if o['rail']==k)]
    if alt:
        a=max(alt,key=lambda a:a['area']); caps[a['ti']]-=1; final.append(dict(a,rail=k))
    else: print('WARN inventory: no substitute for a pod on rail',k)
pods=final
# ---------- output ----------
from font5x7 import draw_text, text_w
SHORT={0:'140X115',1:'125X75 Q',2:'120X50 Q',3:'125X75 L'}
caps_full=[t['count'] for t in types]
lay={'doc':OL['doc'],'setup':OL['setup'],'placement_mode':C['placement_mode'],'wcs_to_sim_offset':off,
     'frames':__doc__.split('Frames :')[1].strip(),'clearance':clr,'through_clearance':tclr,'seal_margin':sm,
     'target_pods':target,'support':{'balance':round(key[6],3),'balance_note':'min over %d directions of support-hull reach / panel reach from the panel centroid'%NDIR,'panel_centroid_sim':[round(v,1) for v in PC_],'hull_fraction':round(ha/panel_area,3),'span_x':round(hx,3),'span_y':round(hy,3)},
     'types':[{'name':t['name'],'across':t['across'],'along':t['along']} for t in types],'rails':[],'pods':[],'inventory_left':{types[i]['name']:caps[i] for i in range(len(types))}}
txt=['POD LAYOUT v3  %s / %s'%(OL['doc'],OL['setup']),
     'mode %s; through-cut clearance %.0f mm, other cuts R+%.0f mm, seal margin %.0f mm'%(C['placement_mode'],tclr,clr,sm),
     'panel bottom: sim X %.1f..%.1f  Y %.1f..%.1f  area %.3f m2 -> target %d pods (min %d, max %d)'%(px0,px1,py0,py1,panel_area/1e6,target,C['min_pods'],C['max_pods']),
     'frame: front (I stop / operator) = -Y; rail scale M = 650 - simY; machine X = sim X + %.1f'%(-x0s),'']
usedk=sorted({c['rail'] for c in pods})
for k in (1,2,3,4):
    x=X[k]; mine=sorted([c for c in pods if c['rail']==k],key=lambda c:c['b'])
    lay['rails'].append({'rail':k,'x_edge_sim':round(x,1),'x_edge_machine':round(x-x0s,1),'x_centre_sim':round(x+rw/2,1),'used':bool(mine)})
    st_=('%d pods'%len(mine)) if mine else ('idle UNDER the panel (between used rails, no pods)' if (x<px1 and x+rw>px0) else ('parked at max travel' if x>=pmax[k]-200 else 'parked, no pods'))
    if x+rw>2000: st_+='  [outside sim X travel +-2000 / model view]'
    lay['rails'][-1]['status']=st_
    txt.append('Rail %d: X- edge machine %.1f (sim %.1f)  %s'%(k,x-x0s,x,st_))
    for c in mine:
        tp=types[c['ti']]; r=c['rect']
        lay['pods'].append({'rail':k,'type':tp['name'],'art':tp['art'],'rot':c['rot'],'base_M_start':c['b'],'base_M_end':c['b']+BASE,'top_rect_sim':[round(v,1) for v in r],'z':[-100,0]})
        txt.append('   %-10s rot %3d  base M %6.1f..%6.1f  top plate sim X %.1f..%.1f  Y %.1f..%.1f'%(SHORT[c['ti']],c['rot'],c['b'],c['b']+BASE,*r))
txt+=['','pods: %d on %d rails (configs tried %d)   support hull %.0f%% of panel area, span X %.0f%% Y %.0f%%'%(len(pods),len(usedk),tried,100*ha/panel_area,100*hx,100*hy),
      'balance %.2f (min over %d directions of support reach / panel reach from the panel centroid sim X %.1f Y %.1f; 1 = full)'%(key[6],NDIR,PC_[0],PC_[1]),
      'by type: '+', '.join('%s %d/%d'%(SHORT[i],caps_full[i]-caps[i],caps_full[i]) for i in range(len(types)))]
for k in (2,3,4): txt.append('edge spacing rail %d-%d: %.1f (min %.0f)'%(k-1,k,X[k]-X[k-1],gapmin[k]))
txt.append('keep-out: through-cut samples %d, other %d'%(sum(v[1] for v in ko_secs.values()),sum(v[0] for v in ko_secs.values())))
json.dump(lay,open(os.path.join(OD,'layout.json'),'w'),indent=1)
open(os.path.join(OD,'layout.txt'),'w').write('\n'.join(txt)+'\n')
# ---------- PNG: top view, 2 px/mm, back (+Y) up, FRONT at the bottom ----------
S=2.0
vx0=min(px0,min(X[k] for k in usedk))-60; vx1=max(px1,max(X[k]+rw for k in usedk))+80; # parked-at-max-travel rails may sit past +-2000 and are omitted from the view
vy0=py0-140; vy1=py1+140
LEGW=330
Wd=int((vx1-vx0)*S)+LEGW; Ht=int((vy1-vy0)*S)
img=[bytearray(b'\xff\xff\xff'*Wd) for _ in range(Ht)]
def pp(i,j,col):
    if 0<=i<Wd and 0<=j<Ht: img[j][3*i:3*i+3]=bytes(col)
def put(x,y,col): pp(int((x-vx0)*S), Ht-1-int((y-vy0)*S), col)
def fillrect(x0,x1,y0,y1,col,hatch=0):
    for i in range(int((x0-vx0)*S),int((x1-vx0)*S)+1):
        for j in range(Ht-1-int((y1-vy0)*S),Ht-int((y0-vy0)*S)):
            if not hatch or (i+j)%hatch==0: pp(i,j,col)
def frame(x0,x1,y0,y1,col,w=1):
    for d in range(w):
        for x in range(int((x0-vx0)*S),int((x1-vx0)*S)+1):
            pp(x,Ht-1-int((y0-vy0)*S)-d,col); pp(x,Ht-1-int((y1-vy0)*S)+d,col)
        for y in range(Ht-1-int((y1-vy0)*S),Ht-int((y0-vy0)*S)):
            pp(int((x0-vx0)*S)+d,y,col); pp(int((x1-vx0)*S)-d,y,col)
def label(x,y,s,col,sc=2,center=True):
    i=int((x-vx0)*S); j=Ht-1-int((y-vy0)*S)
    if center: i-=text_w(s,sc)//2; j-=7*sc//2
    draw_text(pp,i,j,s,col,sc)
GREY=(215,215,215); SOFT=(250,200,195); THRU=(225,70,60); ORANGE=(255,165,0); BLUE=(40,80,220); GREEN=(20,150,40); BLACK=(0,0,0)
for j in range(NY):
    for i in range(NX):
        col=None
        if INS[j][i]: col=GREY
        if KO[j][i]==1: col=SOFT
        if KO[j][i]==2: col=THRU
        if col: fillrect(gx0+i*G,gx0+(i+1)*G-0.01,gy0+j*G,gy0+(j+1)*G-0.01,col)
park_note=[]
for k in (1,2,3,4):
    x=X[k]
    if x>vx1+5 or x+rw<vx0-5:
        park_note.append('R%d @ mach X %.0f'%(k,x-x0s)); continue
    for z0,z1 in zones:
        ya,yb=sorted((simY(z0),simY(z1))); ya=max(ya,vy0); yb=min(yb,vy1)
        if yb>ya: fillrect(x,x+rw,ya,yb,ORANGE,3)
    frame(x,x+rw,max(vy0,simY(rlen)),min(vy1-1,simY(0)),BLUE,2)
    for pm in ports:
        yy=simY(pm)
        if vy0<yy<vy1:
            for dx in range(-4,5):
                for dy in range(-4,5):
                    if dx*dx+dy*dy<=16: put(x+rw/2+dx/2,yy+dy/2,BLUE)
    fillrect(x+3,x+rw-3,vy1-52,vy1-4,(255,255,255))
    label(x+rw/2, vy1-16, 'RAIL %d'%k, BLUE if k in usedk else (120,120,120), 3)
    tag=('X %.0f'%(x-x0s)) if k in usedk else ('PARK' if x>=pmax[k]-200 else 'IDLE')
    label(x+rw/2, vy1-38, tag, (90,90,90), 2)
if park_note:
    label((vx0+vx1)/2, vy1-70, 'parked (off view, max travel): '+', '.join(park_note), (90,90,90), 2)
for lp in loops:
    n=len(lp)
    for i in range(n):
        (xa,ya),(xb,yb)=lp[i],lp[(i+1)%n]; m=int(max(abs(xb-xa),abs(yb-ya))*S)+1
        for q in range(m+1):
            for d in (0,0.5): put(xa+(xb-xa)*q/m+d, ya+(yb-ya)*q/m, BLACK)
for c in pods:
    r=c['rect']; fillrect(r[0],r[1],r[2],r[3],(120,200,130)); frame(r[0],r[1],r[2],r[3],GREEN,3)
    label((r[0]+r[1])/2,(r[2]+r[3])/2+6,SHORT[c['ti']],BLACK,2); label((r[0]+r[1])/2,(r[2]+r[3])/2-8,'ROT %d'%c['rot'],BLACK,2)
# front marker + X arrow
label((vx0+vx1)/2, vy0+22, 'FRONT - I STOP / OPERATOR', BLACK, 3)
for x in range(int(vx0*1)+20, int(vx0)+110):
    for d in (-1,0,1): put(x, vy0+60+d/2, BLACK)
for d in range(10):
    for e in range(-d,d+1): put(vx0+110-d+0, vy0+60+e/2*1.0, BLACK) if False else None
for d in range(12):
    put(vx0+110-d, vy0+60+d/2, BLACK); put(vx0+110-d, vy0+60-d/2, BLACK)
label(vx0+65, vy0+72, '+X', BLACK, 3)
for d in range(-1,2):
    for y in range(int(vy0+40),int(vy0+100)): pass
# legend
lx=int((vx1-vx0)*S)+15; ly=20
def leg(col,txt_,hatch=0):
    global ly
    for i in range(lx,lx+40):
        for j in range(ly,ly+22):
            if not hatch or (i+j)%hatch==0: pp(i,j,col)
    draw_text(pp,lx+50,ly+4,txt_,BLACK,2); ly+=34
draw_text(pp,lx,ly,'LEGEND',BLACK,3); ly+=36
leg((120,200,130),'POD TOP PLATE'); leg(THRU,'THROUGH CUT +%dMM'%int(tclr)); leg(SOFT,'OTHER CUT R+%dMM'%int(clr)); leg(GREY,'PANEL BOTTOM')
leg(ORANGE,'STOP ZONE',3); leg(BLUE,'RAIL / PORTS',4)
ly+=10
for t_ in ['%d PODS, %d RAILS'%(len(pods),len(usedk)),'HULL %d%% OF PANEL'%round(100*ha/panel_area),'SCALE 2 PX = 1 MM','TOP VIEW, BACK UP']:
    draw_text(pp,lx,ly,t_,BLACK,2); ly+=24
def png(path):
    raw=b''.join(b'\x00'+bytes(row) for row in img)
    def ch(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',Wd,Ht,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw,6))+ch(b'IEND',b''))
png(os.path.join(OD,'layout.png'))
print('\n'.join(txt))
