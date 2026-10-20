# Fusion script (fusion_mcp_execute, readOnly false): opens a THROWAWAY doc by name invisibly, (re)generates its toolpaths
# if needed, posts setup 1 with podscan.cps and writes the panel bottom outline (WCS) -> pods/scan_<doc>/.
import adsk.core, adsk.cam, adsk.fusion, json, time, os, traceback
CFG=json.load(open('/Users/johannesagetorp/Documents/Vonque/Fusion Post processor/fork-fixtures/pods/run_cfg.json'))
HERE='/Users/johannesagetorp/Documents/Vonque/Fusion Post processor/fork-fixtures/pods'
def P(m,p): q=m.copy() if False else None; pt=adsk.core.Point3D.create(p.x,p.y,p.z); pt.transformBy(m); return [round(pt.x*10,3),round(pt.y*10,3),round(pt.z*10,3)]
def run(_c):
    R={}
    app=adsk.core.Application.get()
    try:
        f=app.data.findFileById(CFG['doc_lineage']); assert f.name==CFG['doc_name'] and f.name.startswith('ZZ throwaway'), f.name
        mine=[d for d in app.documents if d.dataFile and d.dataFile.id==f.id]
        doc=mine[0] if mine else app.documents.open(f, False)
        cam=adsk.cam.CAM.cast(doc.products.itemByProductType('CAMProductType'))
        s=[x for x in cam.setups if x.name==CFG['setup']][0] if CFG.get('setup') else cam.setups.item(0)
        R['setup']=s.name
        ops=[o for o in s.allOperations]
        bad=[o for o in ops if not (o.hasToolpath and o.isToolpathValid)]
        R['invalid_before']=len(bad)
        if bad:
            oc=adsk.core.ObjectCollection.create()
            for o in bad: oc.add(o)
            fut=cam.generateToolpath(oc); t=time.time()
            while not fut.isGenerationCompleted and time.time()-t<CFG.get('gen_timeout',600): adsk.doEvents(); time.sleep(0.5)
            R['gen_s']=round(time.time()-t,1)
        R['invalid_after']=sum(1 for o in ops if not (o.hasToolpath and o.isToolpathValid))
        out=os.path.join(HERE,'scan'); os.makedirs(out,exist_ok=True)
        oc=adsk.core.ObjectCollection.create()
        for o in ops:
            if o.hasToolpath and o.isToolpathValid and not o.isSuppressed: oc.add(o)
        pi=adsk.cam.PostProcessInput.create('toolpaths', os.path.join(HERE,'podscan.cps'), out, adsk.cam.PostOutputUnitOptions.MillimetersOutput)
        pi.isOpenInEditor=False
        R['posted']=cam.postProcess(oc,pi); R['n_ops']=oc.count
        # panel outline: bottom faces of the setup models, in WCS (mm)
        W=s.workCoordinateSystem  # WCS -> model
        Winv=W.copy(); Winv.invert()
        loops=[]; zs=[]
        bodies=[]
        for m in s.models:
            b=adsk.fusion.BRepBody.cast(m)
            if b: bodies.append(b); continue
            o=adsk.fusion.Occurrence.cast(m)
            if o: bodies+= [x for x in o.bRepBodies]
        R['bodies']=[b.name for b in bodies]
        cand=[]
        for b in bodies:
            for fc in b.faces:
                ok,n=fc.evaluator.getNormalAtPoint(fc.pointOnFace)
                nv=n.copy(); nv.transformBy(Winv)
                if nv.z<-0.999:
                    z=P(Winv,fc.pointOnFace)[2]; cand.append((z,fc))
        zmin=min(z for z,_ in cand); R['z_bottom_wcs']=zmin
        for z,fc in cand:
            if abs(z-zmin)>0.05: continue
            for lp in fc.loops:
                pts=[]
                for ce in lp.coEdges:
                    e=ce.edge; ev=e.evaluator; ok,p0,p1=ev.getParameterExtents()
                    ok,st=ev.getStrokes(p0,p1,0.01)
                    st=list(st)
                    if ce.isOpposedToEdge: st=st[::-1]
                    seg=[P(Winv,p)[:2] for p in st]
                    pts+= seg[:-1] if seg else []
                loops.append({'outer':lp.isOuter,'pts':pts})
        R['loops']=len(loops)
        bb=None
        json.dump({'z_bottom':zmin,'loops':loops,'setup':s.name,'doc':f.name}, open(os.path.join(out,'outline.json'),'w'))
        R['saved']=False
        if R['invalid_before'] and CFG.get('save_after_generate',True):
            R['saved']=doc.save('pods: regenerated toolpaths for scan'); t=time.time()
            while doc.isModified and time.time()-t<60: adsk.doEvents(); time.sleep(0.5)
        if not mine: R['closed']=doc.close(False)
    except Exception: R['exc']=traceback.format_exc()[-1500:]
    R['docs']=[d.name for d in app.documents]
    print(json.dumps(R))
