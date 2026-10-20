import adsk.core, adsk.cam, json, traceback
def run(context):
    R={}
    try:
        app=adsk.core.Application.get(); d=[x for x in app.documents if x.name=='9 Bad_Component1'][0]
        cam=adsk.cam.CAM.cast(d.products.itemByProductType('CAMProductType'))
        R["ncs"]=[x.name for x in cam.ncPrograms]
        n14=[x for x in cam.ncPrograms if x.name=='NCProgram14'][0]
        R["n14_post"]={p.name:p.expression for p in n14.postParameters}
        R["n14_post_cfg"]=n14.postConfiguration.description
        try: R["n14_machine"]=n14.machine.description
        except Exception as ex: R["n14_machine"]=str(ex)[:80]
        t=[x for x in cam.ncPrograms if x.name=='TEST head swings']
        if t:
            R["test_ops"]=[o.name for o in t[0].operations]
            R["test_post"]={p.name:p.expression for p in t[0].postParameters}
        ops={o.name:o for o in cam.allOperations}
        sel=['Edge 2 end-grain B (right end) - side passes','Edge 1 end-grain A (left end) - rough','Edge 4 long A1 (top, left of step) - rough']
        R["valid"]=[[n,ops[n].isToolpathValid,ops[n].parentSetup.name,ops[n].parameters.itemByName('highFeedrateMode').expression,ops[n].parameters.itemByName('highFeedrate').expression,ops[n].parameters.itemByName('tool_feedRetract').expression] for n in sel]
        oc=adsk.core.ObjectCollection.create()
        for n in sel: oc.add(ops[n])
        pi=adsk.cam.PostProcessInput.create('1009','/tmp/lh/cncdump.cps','/tmp/lh',adsk.cam.PostOutputUnitOptions.MillimetersOutput)
        pi.isOpenInEditor=False
        try: pi.machine=n14.machine
        except Exception as ex: R["mach_err"]=str(ex)[:80]
        R["posted"]=cam.postProcess(oc,pi)
    except Exception: R["exc"]=traceback.format_exc()[-800:]
    print(json.dumps(R))
