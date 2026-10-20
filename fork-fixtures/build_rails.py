# Fusion script (run via Fusion MCP fusion_mcp_execute, readOnly false).
# Opens "Mockup Masterwood - rails" INVISIBLY, replaces the bodies of the Table component by 8 rail boxes
# + a reference sketch of Y-stop points, saves a new version, closes. Never touches other docs.
import adsk.core, adsk.fusion, json, time
L=json.load(open('/Users/johannesagetorp/Documents/Vonque/Fusion Post processor/fork-fixtures/rails_layout.json'))
SAVE=True
def run(_c):
    app=adsk.core.Application.get()
    f=app.data.findFileById(L['doc_lineage'])
    assert f.name==L['doc_name'], f.name
    mine=[d for d in app.documents if d.dataFile and d.dataFile.id==f.id]
    for d in mine:
        if d.isModified: print('ABORT: open copy has unsaved changes'); return
    doc=mine[0] if mine else app.documents.open(f, False)
    des=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    root=des.rootComponent
    occ=[o for o in root.occurrences if o.component.name=='Table'][0]
    comp=occ.component
    print('Table occ transform', [round(v,4) for v in occ.transform.asArray()])
    for b in list(comp.bRepBodies): print('del body', b.name); b.deleteMe()
    for s in list(comp.sketches):
        if s.name.startswith('REF'): s.deleteMe()
    tb=adsk.fusion.TemporaryBRepManager.get()
    r=L['rail']; cm=0.1
    out=[]
    for k,xm in sorted(L['rail_x_machine'].items(), key=lambda kv:int(kv[0])):
        x0=xm+L['sim_x0']; x1=x0+r['width']; ya=L['sim_y_of_M0']; yb=ya+L['sim_y_dir']*r['length']; y0=min(ya,yb); y1=max(ya,yb); z1=r['top_z']; z0=z1-r['depth']
        c=adsk.core.Point3D.create((x0+x1)/2*cm,(y0+y1)/2*cm,(z0+z1)/2*cm)
        ob=adsk.core.OrientedBoundingBox3D.create(c, adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0), r['width']*cm, r['length']*cm, r['depth']*cm)
        body=comp.bRepBodies.add(tb.createBox(ob))
        body.name='Rail%s'%k
        out.append((body.name,x0,x1,y0,y1,z0,z1))
    sk=comp.sketches.add(comp.xYConstructionPlane); sk.name='REF Y stops (no collision)'
    for k,xm in L['rail_x_machine'].items():
        xc=xm+L['sim_x0']+r['width']/2
        for nm,M in L['stops_M'].items():
            sk.sketchPoints.add(adsk.core.Point3D.create(xc*cm,(L['sim_y_of_M0']+L['sim_y_dir']*M)*cm,0))
    print('RAILS', json.dumps(out))
    bb=occ.boundingBox; print('TABLE BB mm', [round(v*10,1) for v in (bb.minPoint.x,bb.minPoint.y,bb.minPoint.z,bb.maxPoint.x,bb.maxPoint.y,bb.maxPoint.z)])
    if SAVE:
        ok=doc.save(L.get('save_note','rails rebuilt from rails_layout.json'))
        t=time.time()
        while time.time()-t<60:
            adsk.doEvents(); time.sleep(0.5)
            try:
                if not doc.isModified: break
            except: break
        print('SAVED', ok, 'modified', doc.isModified)
    df=app.data.findFileById(L['doc_lineage'])
    print('VERSION', df.versionNumber, df.latestVersionNumber, df.versionId)
    if not mine: print('CLOSE', doc.close(False))
    print('DOCS', [d.name for d in app.documents], 'ACTIVE', app.activeDocument.name)
