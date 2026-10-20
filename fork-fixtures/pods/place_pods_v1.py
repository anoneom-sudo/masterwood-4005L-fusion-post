#!/usr/bin/env python3
"""fork-fixtures pod placer v1 (pure Python, no numpy). Low fidelity: pods = top-plate footprint boxes Z-100..0.
Inputs : scan/toolpaths.jsonl (podscan.cps), scan/outline.json (scan_setup.py), ../rails_layout.json, ../rail_map.json, place_cfg.json
Outputs: <out>/layout.json, <out>/layout.txt, <out>/layout.png
Frames : WCS = Fusion setup WCS (mm, Z+ up, origin stock top-left-front corner 'top 1').
         sim = machine-sim table frame: Z0 = pod top = panel bottom; front (operator, I stops) = sim -Y (logo side).
         rail scale M (mm) = 650 - simY  (M0 = back/park end, I-stop face M1217, front end ~M1300..1306).
         sim X = machine(ventose) X - 407.5 ; rail X in ventose.prm taken as the rail's X- edge [guess]."""
import json, math, os, sys, zlib, struct
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
# ---------- keep-out ----------
KO=[[False]*NX for _ in range(NY)]
clr=C['clearance']
def stamp(x,y,r):
    i0=max(0,int((x-r-gx0)/G)); i1=min(NX-1,int((x+r-gx0)/G)); j0=max(0,int((y-r-gy0)/G)); j1=min(NY-1,int((y+r-gy0)/G))
    r2=(r+G*0.71)**2
    for j in range(j0,j1+1):
        cy=gy0+(j+0.5)*G; row=KO[j]
        for i in range(i0,i1+1):
            cx=gx0+(i+0.5)*G
            if (cx-x)**2+(cy-y)**2<=r2: row[i]=True
ko_secs={}
for s in secs:
    R=s['D']/2; body=s['body'] or 100; HR=max(R,C['holder_radius_assumed'])
    rt,up,fw,org=s['right'],s['up'],s['fwd'],s['org']
    def g(p): return [org[k]+p[0]*rt[k]+p[1]*up[k]+p[2]*fw[k] for k in range(3)]
    a=fw; az=max(1e-6,a[2]); sinT=math.sqrt(max(0,1-az*az))
    pts=[g(m['p']) for m in s['moves'] if m['k'] in ('l','r')]
    n5=sum(1 for m in s['moves'] if m['k'] in ('l5','r5'))
    if n5: print('WARN 5-axis moves ignored in section',s['i'],n5)
    hit=0; last=None
    for k in range(1,len(pts)):
        p0,p1=pts[k-1],pts[k]
        if min(p0[2],p1[2]) - sinT*HR > zb+clr: continue
        L2=math.dist(p0,p1); ns=max(1,int(L2/1.5))
        for q in range(ns+1):
            u=q/ns; P=[p0[c]+(p1[c]-p0[c])*u for c in range(3)]
            if last and math.dist(P,last)<1.0: continue
            last=P
            # tool body samples t from tip along axis while it reaches below zb+clr
            t=0.0
            while True:
                rr=R if t<=body else HR
                zl=P[2]+a[2]*t - sinT*rr
                if zl>zb+clr or t>body+300: break
                X=P[0]+a[0]*t; Y=P[1]+a[1]*t
                sx,sy,_=w2s(X,Y)
                stamp(sx,sy,rr+clr); hit+=1
                t+=2.0
    ko_secs[s['op']]=hit
# ---------- prefix sum of "bad" cells (outside panel or keep-out) ----------
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
pcx=(px0+px1)/2; pcy=(py0+py1)/2; hw=(px1-px0)/2; hh=(py1-py0)/2
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
                area=(r[1]-r[0])*(r[3]-r[2])
                cx=(r[0]+r[1])/2; cy=(r[2]+r[3])/2
                sc=area/1000.0*(1+C['spread_weight']*(abs(cx-pcx)/max(hw,1)+abs(cy-pcy)/max(hh,1)))
                out.append(dict(ti=ti,rot=rot,b=b,rect=r,score=sc))
    out.sort(key=lambda c:c['b'])
    return out
def best_set(cs,caps):
    """max-score non-overlapping subset along the rail (bases + gap), honouring per-type caps. small search with memo."""
    from functools import lru_cache
    n=len(cs); nxt=[]
    import bisect
    bs=[c['b'] for c in cs]
    for i,c in enumerate(cs): nxt.append(bisect.bisect_left(bs, c['b']+BASE+gap-1e-6))
    @lru_cache(maxsize=None)
    def f(i,used):
        if i>=n: return (0.0,())
        best=f(i+1,used)
        c=cs[i]; u=list(used)
        if u[c['ti']]<caps[c['ti']]:
            u[c['ti']]+=1; s2,sel=f(nxt[i],tuple(u)); s2+=c['score']
            if s2>best[0]+1e-9: best=(s2,(i,)+sel)
        return best
    sc,sel=f(0,tuple([0]*len(types)))
    f.cache_clear()
    return sc,[cs[i] for i in sel]
caps_full=tuple(t['count'] for t in types)
mp=C['min_pods_per_used_rail']
x0s=L['sim_x0']
field1=[(k, L['rail_x_machine'][str(k)]) for k in (1,2,3,4)]
rng=RM['rails_layout']['ventose_x_min_max']
lims={k:(rng[str(k)][0]+x0s, rng[str(k)][1]+x0s) for k in (1,2,3,4)}
gapmin={2:135.0,3:175.0,4:175.0}   # edge-to-edge (same-side edges) minimum to the previous rail
step=C['rail_x_step']
# rail score cache over x grid (only x where the rail can touch the panel matters; others score 0)
cache={}
def rail_score(x):
    key=round(x,1)
    if key in cache: return cache[key]
    if x+rw<px0 or x>px1: cache[key]=(0.0,[]); return cache[key]
    sc,sel=best_set(cands(x),caps_full)
    if len(sel)<mp: sc,sel=0.0,[]
    cache[key]=(sc,sel); return cache[key]
# DP over rails 1..4 in order: state = x of current rail
import itertools
grid={k:[lims[k][0]+i*step for i in range(int((lims[k][1]-lims[k][0])/step)+1)] for k in (1,2,3,4)}
# restrict search to region around the panel (+ parking at min)
for k in grid:
    grid[k]=[x for x in grid[k] if px0-rw-400<=x<=px1+400] or [lims[k][0]]
    if lims[k][0] not in grid[k]: grid[k]=[lims[k][0]]+grid[k]
prev={x:(rail_score(x)[0],[x]) for x in grid[1]}
for k in (2,3,4):
    cur={}
    items=sorted(prev.items())
    # prefix best over x_prev <= x - gap
    best_upto=[]; bv=(-1,None)
    for xp,v in items:
        if v[0]>bv[0]: bv=(v[0],v[1])
        best_upto.append((xp,bv))
    import bisect
    xs=[it[0] for it in best_upto]
    for x in grid[k]:
        idx=bisect.bisect_right(xs, x-gapmin[k]+1e-6)-1
        if idx<0: continue
        v=best_upto[idx][1]
        cur[x]=(v[0]+rail_score(x)[0], v[1]+[x])
    prev=cur
total,xsel=max(prev.values(), key=lambda v:v[0])
# sequential capped allocation (outer rails first) to honour the 14-pod inventory
order=sorted(range(4), key=lambda r: -abs(xsel[r]+rw/2-pcx))
caps=list(caps_full); result={}
for r in order:
    x=xsel[r]
    if x+rw<px0 or x>px1: result[r]=[]; continue
    sc,sel=best_set(cands(x),tuple(caps))
    if len(sel)<mp: sel=[]
    for c in sel: caps[c['ti']]-=1
    result[r]=sel
# ---------- output ----------
lay={'doc':OL['doc'],'setup':OL['setup'],'placement_mode':C['placement_mode'],'wcs_to_sim_offset':off,
     'frames':__doc__.split('Frames :')[1].strip(),'clearance':clr,'seal_margin':sm,
     'rails':[],'pods':[],'inventory_left':{types[i]['name']:caps[i] for i in range(len(types))}}
txt=['POD LAYOUT v1  %s / %s   (mode %s; clearance %.1f mm, seal margin %.1f mm)'%(OL['doc'],OL['setup'],C['placement_mode'],clr,sm),
     'panel bottom outline sim X %.1f..%.1f  Y %.1f..%.1f  (front = -Y = I stops)'%(px0,px1,py0,py1),'']
for r in range(4):
    k=r+1; x=xsel[r]; mx=x-x0s
    used=bool(result[r])
    lay['rails'].append({'rail':k,'x_edge_sim':round(x,1),'x_edge_machine':round(mx,1),'x_centre_sim':round(x+rw/2,1),'used':used})
    txt.append('Rail %d: X- edge machine %.1f (sim %.1f, centre sim %.1f)  %s'%(k,mx,x,x+rw/2,'' if used else '-- no pods (parked/unused)'))
    for c in sorted(result[r],key=lambda c:c['b']):
        tp=types[c['ti']]; rct=c['rect']
        pod={'rail':k,'type':tp['name'],'art':tp['art'],'rot':c['rot'],'base_M_start':c['b'],'base_M_end':c['b']+BASE,
             'top_rect_sim':[round(v,1) for v in rct],'z':[-100,0]}
        lay['pods'].append(pod)
        txt.append('   %-34s rot %3d  base M %6.1f..%6.1f  top plate sim X %.1f..%.1f Y %.1f..%.1f'%(tp['name'],c['rot'],c['b'],c['b']+BASE,*rct))
txt.append('')
txt.append('pods used: %d   by type: %s'%(len(lay['pods']), ', '.join('%s %d/%d'%(t['name'],t['count']-caps[i],t['count']) for i,t in enumerate(types))))
for k in (2,3,4): txt.append('edge spacing rail %d-%d: %.1f (min %.0f)'%(k-1,k,xsel[k-1]-xsel[k-2],gapmin[k]))
kocells=sum(map(sum,KO)); txt.append('keep-out cells (%.0f mm grid): %d; sections contributing: %d of %d'%(G,kocells,sum(1 for v in ko_secs.values() if v),len(ko_secs)))
warn=[]
for r in range(4):
    if result[r] and len(result[r])<mp: warn.append('rail %d below min pods'%(r+1))
if len(lay['pods'])<4: warn.append('fewer than 4 pods support the panel')
lay['warnings']=warn; txt+= ['WARN '+w for w in warn]
json.dump(lay,open(os.path.join(OD,'layout.json'),'w'),indent=1)
open(os.path.join(OD,'layout.txt'),'w').write('\n'.join(txt)+'\n')
# ---------- PNG (top view, 1 px = 1 mm, +Y up = back/park at the top, front/I stop at the bottom) ----------
S=1.0; W0=gx0; H0=gy0; Wd=int(NX*G); Ht=int(NY*G)
img=[[ (255,255,255) for _ in range(Wd)] for _ in range(Ht)]
def put(x,y,col):
    i=int((x-W0)/S); j=Ht-1-int((y-H0)/S)
    if 0<=i<Wd and 0<=j<Ht: img[j][i]=col
for j in range(NY):
    for i in range(NX):
        col=None
        if INS[j][i]: col=(215,215,215)
        if KO[j][i]: col=(235,90,80) if INS[j][i] else (250,190,185)
        if col:
            for dy in range(int(G)):
                for dx in range(int(G)): put(gx0+i*G+dx, gy0+j*G+dy, col)
def rect(x0,x1,y0,y1,col,fill=False):
    xa=int(x0); xb=int(x1); ya=int(y0); yb=int(y1)
    for x in range(xa,xb+1):
        for y in (ya,yb): put(x,y,col)
        if fill:
            for y in range(ya,yb+1):
                if (x+y)%3==0: put(x,y,col)
    for y in range(ya,yb+1):
        for x in (xa,xb): put(x,y,col)
for z0,z1 in zones:
    ya,yb=sorted((simY(z0),simY(z1)))
    for r in range(4): rect(xsel[r],xsel[r]+rw,ya,yb,(255,160,0),True)
for r in range(4):
    rect(xsel[r],xsel[r]+rw,simY(rlen),simY(0),(40,80,220))
    for pm in ports:
        yy=simY(pm)
        for dx in range(-4,5):
            for dy in range(-4,5):
                if dx*dx+dy*dy<=16: put(xsel[r]+rw/2+dx,yy+dy,(40,80,220))
for p in lay['pods']:
    x0_,x1_,y0_,y1_=p['top_rect_sim']; rect(x0_,x1_,y0_,y1_,(20,150,40),True); rect(x0_+1,x1_-1,y0_+1,y1_-1,(20,150,40))
for lp in loops:
    n=len(lp)
    for i in range(n):
        (xa,ya),(xb,yb)=lp[i],lp[(i+1)%n]; m=int(max(abs(xb-xa),abs(yb-ya)))+1
        for q in range(m+1): put(xa+(xb-xa)*q/m, ya+(yb-ya)*q/m,(0,0,0))
# sim origin cross
for d in range(-10,11): put(d,0,(0,0,0)); put(0,d,(0,0,0))
def png(path,img):
    h=len(img); w=len(img[0]); raw=b''.join(b'\x00'+bytes([c for px in row for c in px]) for row in img)
    def ch(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw,6))+ch(b'IEND',b''))
png(os.path.join(OD,'layout.png'),img)
print('\n'.join(txt))
