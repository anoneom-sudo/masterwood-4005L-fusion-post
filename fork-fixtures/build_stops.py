# Fusion script (rw). Removes the floating 'REF Y stops' sketch(es) and puts each rail's stop marks INSIDE that rail's component
# (sketch on the rail top face, Z-100, on the rail centreline): 'R<k> stop 2' at M458 and 'R<k> I stop' at M1217 (sim Y = 650 - M).
# Each mark = its own small sketch (centre point + 20 mm cross), so they move with the rail joint. No bodies. Saves + closes. Wrapper calls run().
import adsk.core, adsk.fusion, json, time, traceback
HERE='/Users/johannesagetorp/Documents/Vonque/Fusion Post processor/fork-fixtures'
L=json.load(open(HERE+'/rails_layout.json')); CFG=json.load(open('/tmp/fxr/stops_job.json'))
def run(_c=None):
    app=adsk.core.Application.get(); R={'open_before':[d.name for d in app.documents]}; doc=None
    try:
        f=app.data.findFileById(L['doc_lineage']); R['ver_before']=f.versionNumber
        if [d for d in app.documents if d.dataFile and d.dataFile.id==f.id]: R['abort']='rails doc open'; print(json.dumps(R)); return
        doc=app.documents.open(f,False); t=time.time()
        while time.time()-t<3: adsk.doEvents(); time.sleep(0.2)
        des=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType')); R['designType']=des.designType
        root=des.rootComponent; tocc=[o for o in root.occurrences if o.component.name=='Table'][0]; T=tocc.component
        # 1) delete old stop sketches anywhere
        gone=[]
        comps=[root]+[o.component for o in root.allOccurrences]
        seen=set()
        for c in comps:
            if c.id in seen: continue
            seen.add(c.id)
            for sk in list(c.sketches):
                if 'stop' in sk.name.lower() or sk.name.startswith('REF'):
                    gone.append(c.name+'/'+sk.name); sk.deleteMe()
        R['deleted']=gone
        cm=0.1; marks=[('stop 2',L['stops_M']['S2_EF']),('I stop',L['stops_M']['S1_IJ_face'])]
        R['marks']={}
        for o in T.occurrences:
            n=o.component.name
            if not n.startswith('Rail '): continue
            k=int(n.split()[1]); C=o.component; b=C.bRepBodies.item(0)
            bb=b.boundingBox; xc=(bb.minPoint.x+bb.maxPoint.x)/2; zt=bb.maxPoint.z
            top=max([fc for fc in b.faces if abs(fc.boundingBox.minPoint.z-zt)<1e-6 and abs(fc.boundingBox.maxPoint.z-zt)<1e-6], key=lambda fc:fc.area)
            for lab,M in marks:
                y=(L['sim_y_of_M0']+L['sim_y_dir']*M)*cm
                sk=C.sketches.addWithoutEdges(top); sk.name='R%d %s'%(k,lab)
                p=sk.modelToSketchSpace(adsk.core.Point3D.create(xc,y,zt))
                sk.sketchPoints.add(p)
                ln=sk.sketchCurves.sketchLines
                for dx,dy in ((1,0),(0,1)):
                    a=sk.modelToSketchSpace(adsk.core.Point3D.create(xc-dx*1.0,y-dy*1.0,zt)); bpt=sk.modelToSketchSpace(adsk.core.Point3D.create(xc+dx*1.0,y+dy*1.0,zt))
                    l=ln.addByTwoPoints(a,bpt); l.isConstruction=False
                sk.isVisible=True
        adsk.doEvents()
        # verify in assembly context (world = sim coords)
        for o in T.occurrences:
            if not o.component.name.startswith('Rail '): continue
            op=o.createForAssemblyContext(tocc)
            for sk in o.component.sketches:
                skp=sk.createForAssemblyContext(op)
                ws=[]
                for ln_ in skp.sketchCurves.sketchLines:
                    g=ln_.worldGeometry; ws.append(adsk.core.Point3D.create((g.startPoint.x+g.endPoint.x)/2,(g.startPoint.y+g.endPoint.y)/2,(g.startPoint.z+g.endPoint.z)/2))
                cx=sum(w.x for w in ws)/len(ws)*10; cy=sum(w.y for w in ws)/len(ws)*10; cz=sum(w.z for w in ws)/len(ws)*10
                rb=op.bRepBodies.item(0).boundingBox; rail_cx=(rb.minPoint.x+rb.maxPoint.x)/2*10
                R['marks'][sk.name]={'path':op.fullPathName,'xyz_sim':[round(cx,1),round(cy,1),round(cz,1)],'M':round(L['sim_y_of_M0']-cy,1),'rail_centre_x':round(rail_cx,1),'n_pts':len(ws)}
        R['bodies_in_rails']={o.component.name:o.component.bRepBodies.count for o in T.occurrences if o.component.name.startswith('Rail ')}
        if CFG.get('dry_run'): R['closed_nosave']=doc.close(False); doc=None
        else:
            R['saved']=doc.save(CFG['save_note']); t=time.time()
            while doc.isModified and time.time()-t<60: adsk.doEvents(); time.sleep(0.5)
            R['closed']=doc.close(False); doc=None
    except Exception:
        R['exc']=traceback.format_exc()[-1800:]
        if doc is not None:
            try: R['closed_nosave_on_error']=doc.close(False)
            except Exception as e: R['close_err']=str(e)
    R['docs']=[d.name for d in app.documents]; print(json.dumps(R))
