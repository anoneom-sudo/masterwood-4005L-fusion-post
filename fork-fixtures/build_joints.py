# Fusion script (fusion_mcp_execute, readOnly false). ONE-TIME BUILD helper; normal use needs no script (drag the joints).
# Opens "Mockup Masterwood - rails" INVISIBLY (aborts if open/modified), and inside the Table component:
#  - 'Table frame' (grounded, no bodies) = joint anchor
#  - Rail 1..8 components (existing Rail bodies moved in) with as-built SLIDER joints along machine X,
#    zero = as-modelled X (ventose min), limits = x_travel_min_max (rail 4 max 2700 measured); default pose from joints_cfg.json
#  - v8: per rail a pod set (joints_cfg pod_sets) = plain boxes (top plate at rot 0, Z-100..0) with Y SLIDER joints on that rail,
#    parked in a row behind the rail back end beyond the X-gantry legs (value 0), sliding to the front limit M_front_limit.
#    If the rails already exist (v7+), only the pods are rebuilt (old pod sets + their joints removed).
# Saves a new version and closes. Wrapper calls run().
import adsk.core, adsk.fusion, json, time, traceback, os
HERE='/Users/johannesagetorp/Documents/Vonque/Fusion Post processor/fork-fixtures'
L=json.load(open(HERE+'/rails_layout.json')); J=json.load(open(HERE+'/joints_cfg.json'))
def run(_c=None):
    app=adsk.core.Application.get(); R={'open_before':[d.name for d in app.documents]}
    try:
        f=app.data.findFileById(L['doc_lineage']); assert f.name==L['doc_name']
        R['version_before']=f.versionNumber
        if f.versionNumber!=J['expect_version']: R['abort']='version %d != expected %d'%(f.versionNumber,J['expect_version']); print(json.dumps(R)); return
        if [d for d in app.documents if d.dataFile and d.dataFile.id==f.id]: R['abort']='rails doc is open in Fusion; not touching it'; print(json.dumps(R)); return
        doc=app.documents.open(f,False)
        t=time.time()
        while time.time()-t<3: adsk.doEvents(); time.sleep(0.2)
        des=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType')); R['designType']=des.designType
        if des.designType!=adsk.fusion.DesignTypes.ParametricDesignType:
            R['abort']='rails doc v%d is not parametric (designType %d)'%(f.versionNumber,des.designType); R['closed']=doc.close(False); R['docs']=[d.name for d in app.documents]; print(json.dumps(R)); return
        root=des.rootComponent; tocc=[o for o in root.occurrences if o.component.name=='Table'][0]; T=tocc.component
        cm=0.1; x0s=L['sim_x0']; rw=L['rail']['width']; rl=L['rail']['length']
        if J.get('make_parametric') and des.designType==0: des.designType=adsk.fusion.DesignTypes.ParametricDesignType; R['designType_now']=des.designType
        I=adsk.core.Matrix3D.create()
        have_rails=any(o.component.name=='Rail 1' for o in T.occurrences)   # v7+: rails + joints already exist -> only rebuild pods
        R['mode']='pods only (rails kept)' if have_rails else 'full build'
        if not have_rails:
            fr=root.occurrences.addNewComponent(I); fr.component.name='Table frame (joint anchor, no bodies)'; fr.isGrounded=True
            frs=fr.component.sketches.add(fr.component.xYConstructionPlane); frs.name='anchor'; frs.sketchPoints.add(adsk.core.Point3D.create(0,0,0))
        tb=adsk.fusion.TemporaryBRepManager.get()
        def box(comp,x0,x1,y0,y1,z0,z1,name):
            c=adsk.core.Point3D.create((x0+x1)/2*cm,(y0+y1)/2*cm,(z0+z1)/2*cm)
            ob=adsk.core.OrientedBoundingBox3D.create(c,adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)*cm,(y1-y0)*cm,(z1-z0)*cm)
            bf=comp.features.baseFeatures.add(); bf.name=name; bf.startEdit()
            b=comp.bRepBodies.add(tb.createBox(ob),bf); bf.finishEdit()
            b=comp.bRepBodies.item(comp.bRepBodies.count-1); b.name=name; return b
        def shift(o,dx,axis='x'):
            op=o.createForAssemblyContext(tocc)   # transform overrides only on root-level proxies
            m=op.transform2; t=m.translation; setattr(t,axis,getattr(t,axis)+dx*cm); m.translation=t; op.transform2=m
        rails={}; R['joints']=[]
        rng=J['rail_x_machine_min_max']
        def slider(name,occ1,occ2,body_in_occ1,axis,lo,hi,ctx=None):
            ctx=ctx or T
            o1=occ1 if ctx is T else occ1.createForAssemblyContext(tocc)
            nat=body_in_occ1.nativeObject or body_in_occ1
            v=nat.createForAssemblyContext(o1).vertices.item(0)
            g=adsk.fusion.JointGeometry.createByPoint(v)
            ji=ctx.asBuiltJoints.createInput(o1,occ2,g)
            ji.setAsSliderJointMotion(axis)
            j=ctx.asBuiltJoints.add(ji); j.name=name
            sl=j.jointMotion.slideLimits
            sl.isMinimumValueEnabled=True; sl.minimumValue=lo*cm; sl.isMaximumValueEnabled=True; sl.maximumValue=hi*cm
            R['joints'].append({'name':name,'limits_mm':[lo,hi]}); return j
        def bbx(b): return [round(v*10,1) for v in (b.minPoint.x,b.minPoint.y,b.minPoint.z,b.maxPoint.x,b.maxPoint.y,b.maxPoint.z)]
        def pbb(o):  # world bbox of the occurrence's bodies, via the root-level proxy
            op=o.createForAssemblyContext(tocc); bs=[x for x in op.bRepBodies]
            if not bs: return None
            B=bs[0].boundingBox.copy()
            for x in bs[1:]: B.combine(x.boundingBox)
            return bbx(B)
        if not have_rails:
            bodies={b.name:b for b in T.bRepBodies}
            # rails: own component, moved to the DEFAULT pose first (hidden doc: joint values can't be driven), then joint zero = default
            tmp={}
            for k in range(1,9):
                b=bodies['Rail%d'%k]
                o=T.occurrences.addNewComponent(I); o.component.name='Rail %d'%k
                nb=b.moveToComponent(o)
                x_mod=L['rail_x_machine'][str(k)]
                assert abs(nb.boundingBox.minPoint.x*10-(x_mod+x0s))<0.5, ('rail not at modelled X',k,nb.boundingBox.minPoint.x*10)
                xd=J['default_rail_x_machine'].get(str(k),x_mod)
                if abs(xd-x_mod)>1e-6:
                    shift(o,xd-x_mod); adsk.doEvents()
                    if des.snapshots.hasPendingSnapshot: des.snapshots.add()   # capture each move (pending overrides replace each other)
                    adsk.doEvents()
                tmp[k]=(o,nb,xd)
            for k,(o,nb,xd) in tmp.items():
                tmin,tmax=rng[str(k)]
                slider('Rail %d X (machine X- edge = %d + value)'%(k,xd),o,fr,nb,adsk.fusion.JointDirections.XAxisJointDirection,tmin-xd,tmax-xd,ctx=root)
        rails={int(o.component.name.split()[1]):o for o in T.occurrences if o.component.name.startswith('Rail ')}
        R['rails_bb_before_pods']={'Rail %d'%k:pbb(o) for k,o in sorted(rails.items())}
        # remove any previous pod set (v7: 'Pod nn ...'; v8: 'Rn ...') with its joints
        import re
        isPod=lambda n: n.startswith('Pod ') or re.match(r'^R\d ',n) is not None
        nj=0
        for j in list(T.asBuiltJoints):
            if isPod(j.name): j.deleteMe(); nj+=1
        no=0
        for o in list(T.occurrences):
            if isPod(o.component.name): o.deleteMe(); no+=1
        R['removed']={'pod_joints':nj,'pod_occurrences':no}
        adsk.doEvents()
        # v8 pod sets: every rail gets the same set, parked in a row BEHIND the rail back end (sim +Y), beyond the X-gantry legs
        P=J['pod_sets']; types=P['types']; y0p=P['park_y_start_sim']; gap=P['park_gap']; Mfront=P['M_front_limit']
        pods=[]
        for k in sorted(rails):
            o=rails[k]; rb=pbb(o); xc=(rb[0]+rb[3])/2
            y=y0p
            for key,suf in P['set']:
                t=types[key]; ya,yb=y,y+t['along']; y=yb+gap
                yc=(ya+yb)/2; Mp=L['sim_y_of_M0']+L['sim_y_dir']*0  # placeholder
                Mp=(L['sim_y_of_M0']-yc)/(-L['sim_y_dir'])          # rail scale M of the parked top-plate centre (negative = behind the back end)
                nm='R%d %s %s'%(k,t['short'],suf)
                po=T.occurrences.addNewComponent(I); po.component.name=nm
                pb=box(po.component,xc-t['across']/2,xc+t['across']/2,ya,yb,-100,0,nm)
                # value 0 = parked; M(centre) = Mpark - value  -> slide to the front: value down to Mpark - M_front_limit
                pj=slider('%s Y (parked M %.0f; M = %.0f - value)'%(nm,Mp,Mp),po,o,pb,adsk.fusion.JointDirections.YAxisJointDirection,round(Mp-Mfront,1),0)
                pods.append((po,pb,pj,nm,Mp))
        adsk.doEvents()
        try: des.computeAll()
        except Exception as e: R['compute_err']=str(e)
        adsk.doEvents()
        R['rails_bb_sim']={'Rail %d'%k:pbb(o) for k,o in sorted(rails.items())}
        R['rails_unchanged']=R['rails_bb_sim']==R['rails_bb_before_pods']
        R['pods_bb_sim']={nm:pbb(po) for po,pb,pj,nm,Mp in pods}
        R['n_pods']=len(pods)
        R['n_joints_total']=root.asBuiltJoints.count+T.asBuiltJoints.count
        R['pod_limits_read']={nm:[round(pj.jointMotion.slideLimits.minimumValue*10,1),round(pj.jointMotion.slideLimits.maximumValue*10,1)] for po,pb,pj,nm,Mp in pods[:8]}
        if J.get('dry_run'):
            R['closed_nosave']=doc.close(False); R['docs']=[d.name for d in app.documents]; print(json.dumps(R)); return
        R['saved']=doc.save(J['save_note'])
        t=time.time()
        while doc.isModified and time.time()-t<60: adsk.doEvents(); time.sleep(0.5)
        R['closed']=doc.close(False)
        f2=app.data.findFileById(L['doc_lineage']); R['version_after']=f2.versionNumber
    except Exception:
        R['exc']=traceback.format_exc()[-2000:]
        try:
            for d in list(app.documents):
                if not d.isVisible and d.name.startswith(L['doc_name']): R['closed_on_error']=d.close(False)
        except Exception as e: R['close_err']=str(e)
    R['docs']=[d.name for d in app.documents]
    print(json.dumps(R))
