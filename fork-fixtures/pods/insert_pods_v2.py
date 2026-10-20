# Fusion script (fusion_mcp_execute, readOnly false). THROWAWAY docs only (name must start with 'ZZ throwaway').
# Reads <out>/layout.json, (re)creates component "PODS fork-fixtures" with one box per pod (top-plate footprint, sim Z-100..0),
# sets them as the setup's fixtures, and (mode istop) shifts the setup position so the panel front edge sits on the I-stop face.
import adsk.core, adsk.cam, adsk.fusion, json, time, traceback
HERE='/Users/johannesagetorp/Documents/Vonque/Fusion Post processor/fork-fixtures/pods'
CFG=json.load(open(HERE+'/run_cfg.json')); PC=json.load(open(HERE+'/place_cfg.json'))
LAY=json.load(open(HERE+'/'+PC['out_dir']+'/layout.json'))
CNAME='PODS fork-fixtures'
def run(_c):
    R={}; app=adsk.core.Application.get()
    try:
        f=app.data.findFileById(CFG['doc_lineage']); assert f.name==CFG['doc_name'] and f.name.startswith('ZZ throwaway'), f.name
        mine=[d for d in app.documents if d.dataFile and d.dataFile.id==f.id]
        if mine and mine[0].isModified: print(json.dumps({'abort':'open throwaway has unsaved changes'})); return
        doc=mine[0] if mine else app.documents.open(f, False)
        des=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
        cam=adsk.cam.CAM.cast(doc.products.itemByProductType('CAMProductType'))
        s=[x for x in cam.setups if x.name==LAY['setup']][0]
        root=des.rootComponent
        for o in list(root.occurrences):
            if o.component.name==CNAME: o.deleteMe()
        occ=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); comp=occ.component; comp.name=CNAME
        W=s.workCoordinateSystem   # WCS -> model
        off=LAY['wcs_to_sim_offset']; tb=adsk.fusion.TemporaryBRepManager.get(); cm=0.1
        oc=adsk.core.ObjectCollection.create(); names=[]
        for i,p in enumerate(LAY['pods']):
            x0,x1,y0,y1=p['top_rect_sim']; z0,z1=p['z']
            c=adsk.core.Point3D.create(((x0+x1)/2+off[0])*cm,((y0+y1)/2+off[1])*cm,((z0+z1)/2+off[2])*cm); c.transformBy(W)
            xd=adsk.core.Vector3D.create(1,0,0); yd=adsk.core.Vector3D.create(0,1,0); xd.transformBy(W); yd.transformBy(W)
            ob=adsk.core.OrientedBoundingBox3D.create(c,xd,yd,(x1-x0)*cm,(y1-y0)*cm,(z1-z0)*cm)
            b=comp.bRepBodies.add(tb.createBox(ob)); b.name='R%d %s r%d M%.0f'%(p['rail'],p['type'].replace('VCBL-K2 ','').split(' (')[0],p['rot'],p['base_M_start'])
            names.append(b.name)
        oc.add(occ)
        s.fixtures=oc; s.fixtureEnabled=True
        R['fixtures']=[x.name for x in s.fixtures]; R['bodies']=names
        ps=s.parameters
        # FIX 15:09: with fixtures on, origin mode 'fixturePoint' put the FIXTURE box bottom-centre (pod bottoms) on the table
        # attach point -> pods Z0..+100, panel on top. Reference the STOCK box instead: stock bottom-centre -> attach (+ offsets).
        ps.itemByName('job_positionReference_origin_mode').expression="'stockPoint'"
        ps.itemByName('job_positionReference_origin_boxPoint').expression="'bottom center'"
        ps.itemByName('job_positionZOffset').expression='0 mm'
        if PC['placement_mode']!='istop':
            ps.itemByName('job_positionXOffset').expression='0 mm'; ps.itemByName('job_positionYOffset').expression='0 mm'
        if PC['placement_mode']=='istop':
            # stock bottom-centre (box point used by the setup) -> sim (cx-offx, cy-offy); setup offsets move it there
            # WCS stock box from the scan workpiece
            wp=[json.loads(l) for l in open(HERE+'/'+PC['scan_dir']+'/toolpaths.jsonl') if '"t":"wp"' in l][0]
            cx=(wp['lo'][0]+wp['hi'][0])/2-off[0]; cy=(wp['lo'][1]+wp['hi'][1])/2-off[1]
            ps.itemByName('job_positionXOffset').expression='%.3f mm'%cx
            ps.itemByName('job_positionYOffset').expression='%.3f mm'%cy
        R['position']={n:ps.itemByName(n).expression for n in ('job_positionReference_origin_mode','job_positionReference_origin_boxPoint','job_positionXOffset','job_positionYOffset','job_positionZOffset','job_fixture')}
        # verification in sim/table coords: sim = model - stock bottom-centre + offsets (setup WCS = model here)
        def bbm(b): return [b.minPoint.x*10,b.minPoint.y*10,b.minPoint.z*10,b.maxPoint.x*10,b.maxPoint.y*10,b.maxPoint.z*10]
        sx0,sx1=ps.itemByName('stockXLow').value.value*10 if False else float(ps.itemByName('stockXLow').expression),float(ps.itemByName('stockXHigh').expression)
        sy0,sy1=float(ps.itemByName('stockYLow').expression),float(ps.itemByName('stockYHigh').expression)
        sz0,sz1=float(ps.itemByName('stockZLow').expression),float(ps.itemByName('stockZHigh').expression)
        def ev(n):
            e=ps.itemByName(n).expression.replace('mm','').strip(); return float(e or 0)
        ox,oy,oz=ev('job_positionXOffset'),ev('job_positionYOffset'),ev('job_positionZOffset')
        bc=((sx0+sx1)/2,(sy0+sy1)/2,sz0)
        tos=lambda v:[round(v[0]-bc[0]+ox,1),round(v[1]-bc[1]+oy,1),round(v[2]-bc[2]+oz,1),round(v[3]-bc[0]+ox,1),round(v[4]-bc[1]+oy,1),round(v[5]-bc[2]+oz,1)]
        R['verify_sim']={'stock':tos([sx0,sy0,sz0,sx1,sy1,sz1]),'part':tos(bbm([b for b in root.bRepBodies][0].boundingBox)),'pods_all':tos(bbm(occ.boundingBox)),
                         'pods':{b.name:tos(bbm(b.boundingBox)) for b in comp.bRepBodies}}
        R['saved']=doc.save('pods: %d pod boxes as fixtures from %s/layout.json; position %s'%(len(names),PC['out_dir'],PC['placement_mode']))
        t=time.time()
        while doc.isModified and time.time()-t<60: adsk.doEvents(); time.sleep(0.5)
        if not mine: R['closed']=doc.close(False)
    except Exception: R['exc']=traceback.format_exc()[-1500:]
    R['docs']=[d.name for d in app.documents]
    print(json.dumps(R))
