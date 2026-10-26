/**
  ============================================================================
  FORK FOR DRILLING DEVELOPMENT - NOT THE LIVE POST - DO NOT WIRE INTO FUSION
  ============================================================================
  File   : fork-drilling/masterwood_4005L_drill.cps
  Forked : 2026-10-19 from ../masterwood_4005L.cps (live, untouched)
  Purpose: add MW310 vertical boring-head output (G100) for shelf-pin /
           system holes (D5 on 32 mm pitch), dowels and hinge cups.
  Spec   : fork-drilling/docs/drilling-dialect.md and fork-drilling/PLAN.md
  Test   : fork-drilling/harness/run_post.sh (headless Fusion post engine)
  Status : PROTOTYPE. One Fusion drill op can become multi-spindle G100
           (#T81/#X81/#S81 and further T8n groups) when holes sit on the
           32 mm X row. Anything that does not fit stays one G100 per hole.
           Not proven on the mill. See fork-drilling/docs/GANG-DRILLING.md.
           Do not send output to the machine without the dry-run steps in PLAN.md.
  Tool mapping in this fork:
    Fusion T1..T10 / T101..T110 -> electrospindle T41/n (unchanged, drilling
                                   cycles are expanded to G173/G101 like before)
    Fusion T201..T250           -> boring-head station n (T1..T50), G100
  ============================================================================
*/

/**
  Masterwood MW310 Project 4005L
  Native PRG: % header |1..|14 :1 G120 G172/G173 G101 G100 %
  Spindle tools T41/1..T41/10 on the G172/G173 line
  G173 … A90 C0 D0    vertical (explicit head pose; do not rely on tool change)
  G173 … A.. C.. D0   3+2
  S = rpm/1000, F = m/min, E = plunge
  Z+ into the panel (negate Fusion Z)
  Work XYZ in setup/panel WCS + A + C; no TWP; no TCP words (control TCP)
  A90 = tool down; A0 C0 = tool right; +C clockwise from above
  Pivot 184.90 mm is on the control
  3+2 only in v1

  Golden files: samples/Test.PRG, samples/test2.PRG
  Spec: AGENTS.md (STATUS scoreboard in Obsidian)

  FORKID {B3E91C70-4A5D-4F2B-9E18-7C2A1F06D4B8}
*/

description = "Masterwood 4005L MW310 - DRILL FORK (dev only)";
vendor = "Masterwood";
vendorUrl = "http://www.masterwood.com";
legal = "Copyright (C) 2012-2026 by Autodesk, Inc. Native MW310 dialect for Project 4005L.";
certificationLevel = 0;
minimumRevision = 45917;

longDescription = "Native MW310 post for Masterwood Project 4005L. Vertical and 3+2 use G173 A/C D0 (A90 C0 when the tool is down). Simultaneous 5-axis is rejected.";

extension = "prg";
setCodePage("ascii");

capabilities = CAPABILITY_MILLING | CAPABILITY_MACHINE_SIMULATION;
// Fork: drilling cycles reach onCyclePoint below.
tolerance = spatial(0.002, MM);

minimumChordLength = spatial(0.25, MM);
minimumCircularRadius = spatial(0.01, MM);
maximumCircularRadius = spatial(1000, MM);
minimumCircularSweep = toRad(0.01);
maximumCircularSweep = toRad(180);
allowHelicalMoves = true;
allowedCircularPlanes = 1 << PLANE_XY;

properties = {
  workField: {
    title      : "G120 work field",
    description: "Work field number for G120 Kn.",
    group      : "preferences",
    type       : "integer",
    value      : 1,
    scope      : "post"
  },
  vacuumField: {
    title      : "M61 vacuum field",
    description: "Vacuum / zone number for M61 Kn D1.",
    group      : "preferences",
    type       : "integer",
    value      : 0,
    scope      : "post"
  },
  verticalTolerance: {
    title      : "Vertical tool tolerance (deg)",
    description: "Treat the tool as vertical when the workplane Z is within this angle of setup Z.",
    group      : "preferences",
    type       : "number",
    value      : 0.1,
    scope      : "post"
  },
  headOrientHeight: {
    title      : "Head orient height",
    description: "Fusion Z above stock top where the first G173 ends (mill Z = -this). Golden test2: Z-20. The control does tool pickup + A/C swing at its own safe height, then comes down here (operator 2026-10-19).",
    group      : "preferences",
    type       : "number",
    value      : 20,
    scope      : "post"
  },
  orientFeed: {
    title      : "G173 orient feed E (m/min)",
    description: "E word on the first G173 (approach after tool call + swing). Golden test2: E2. 0 = use operation plunge feed.",
    group      : "preferences",
    type       : "number",
    value      : 2,
    scope      : "post"
  },
  cMillSign: {
    title      : "Mill C sign",
    description: "Multiply geometric C by this before writing G173 (+1 or -1). Masterwood positive sense vs Fusion atan2.",
    group      : "preferences",
    type       : "integer",
    value      : 1,
    scope      : "post"
  },
  cMillOffset: {
    title      : "Mill C offset (deg)",
    description: "Added to geometric C on G173 after sign. Default 180: 2026-10-19 slot dry run, tip leaned wrong way with 0 (C169), right with 180 (C-11). Pair with cSimOffset 90. Sim uses cSimOffset only.",
    group      : "preferences",
    type       : "number",
    value      : 180,
    scope      : "post"
  },
  yMillSign: {
    title      : "Mill Y sign",
    description: "Multiply Fusion/setup Y before writing (+1 or -1). With useY911, applies inside #911-(…). Default +1 when using #911 (do not double-flip).",
    group      : "preferences",
    type       : "integer",
    value      : 1,
    scope      : "post"
  },
  useY911: {
    title      : "Y as #911-(…)",
    description: "true: emit #902=#911-(y) then Y=#902 like goldens (Singolo / stop-edge Y). false: absolute Y. Trial 2026-09-18 after entrance DRO V≈976 vs stop I≈1889.",
    group      : "preferences",
    type       : "boolean",
    value      : true,
    scope      : "post"
  },
  boringToolBase: {
    title      : "Boring-head tool number base",
    description: "Fusion tool number = base + boring station (TAB01 bore rows 1..50). Default 200: T202 = station 2 (rijboor 5mm). Fork only.",
    group      : "preferences",
    type       : "integer",
    value      : 200,
    scope      : "post"
  },
  boringMaxOverThrough: {
    title      : "Max depth below panel bottom (mm)",
    description: "Error if a G100 depth goes deeper than panel thickness + this. Protects pods/table. Fork only.",
    group      : "preferences",
    type       : "number",
    value      : 1,
    scope      : "post"
  },
  gangDrilling: {
    title      : "Gang boring",
    description: "Group holes on the 32 mm X row into one G100 (#T81 and further groups). Off-pitch holes and other stations stay one G100 each. Fork only.",
    group      : "preferences",
    type       : "boolean",
    value      : true,
    scope      : "operation"
  },
  gangStations: {
    title      : "Gang stations along X",
    description: "Consecutive boring stations from low X to high X. TAB01 stations 2-6 are the 5 mm row bits. Fork only.",
    group      : "preferences",
    type       : "string",
    value      : "2,3,4,5,6",
    scope      : "post"
  },
  gangPitch: {
    title      : "Gang pitch (mm)",
    description: "Distance between consecutive gang stations. Offset.prm X row is 32.00 mm. Fork only.",
    group      : "preferences",
    type       : "number",
    value      : 32,
    scope      : "post"
  },
  maxGangGroups: {
    title      : "Max gang groups",
    description: "How many distinct #T8n spindle sets one program may define (shop programs use T81-T83). Further patterns are single G100. Fork only.",
    group      : "preferences",
    type       : "integer",
    value      : 3,
    scope      : "post"
  },
  checkStationDiameter: {
    title      : "Check boring diameter",
    description: "Error if the Fusion tool diameter does not match TAB01 for that station. Fork only. Turn off for Autodesk sample .cnc files.",
    group      : "preferences",
    type       : "boolean",
    value      : true,
    scope      : "post"
  },
  forceMM: {
    title      : "Force mm output (harness)",
    description: "Fork/harness only: convert an inch intermediate (Autodesk sample .cnc) to mm instead of failing.",
    group      : "preferences",
    type       : "boolean",
    value      : false,
    scope      : "post"
  },
  cSimOffset: {
    title      : "Simulate C offset (deg)",
    description: "Added only for Fusion Machine Sim (setCurrentABC / setTargetC), not on G173. Mill park C0 = Fusion C home 90. Use ±90; +90 vs -90 flips lean inside/outside (180° about vertical). Default 90 (2026-10-19, paired with cMillOffset 180; was -90 with offset 0).",
    group      : "preferences",
    type       : "number",
    value      : 90,
    scope      : "post"
  }
};

var xyzFormat = createFormat({decimals:2, forceDecimal:false, trim:true});
var abcFormat = createFormat({decimals:1, forceDecimal:false, trim:true});
var feedFormat = createFormat({decimals:1, forceDecimal:false, trim:true}); // m/min
var rpmFormat = createFormat({decimals:1, forceDecimal:false, trim:true}); // rpm/1000
var rFormat = createFormat({decimals:2, forceDecimal:false, trim:true});

var xOutput = createOutputVariable({prefix:"X"}, xyzFormat);
var yOutput = createOutputVariable({prefix:"Y"}, xyzFormat);
var zOutput = createOutputVariable({prefix:"Z"}, xyzFormat);
var feedOutput = createOutputVariable({prefix:"F"}, feedFormat);
var aOutput = createOutputVariable({prefix:"A", control:CONTROL_FORCE}, abcFormat);
var cOutput = createOutputVariable({prefix:"C", control:CONTROL_FORCE}, abcFormat);

var pendingRadiusCompensation = -1;
var routeOpen = false;
var activeA = 90; // mill G173 degrees (after cMillSign/offset)
var activeC = 0;  // mill G173 C — what the control runs
var isVerticalTool = true;
var sectionWorkPlane = new Matrix();
var receivedMachineConfiguration = false;
var machineActivated = false;
var boringSection = false; // fork: current section uses the boring head (G100)
var boringStation = 0;
var gangPlanner = null;
var boringHoles = [];

// Two number spaces:
//   mill C  = on G173 (Masterwood). geometric from toolAnglesFromForward, then cMillSign/offset.
//   sim C   = mill C + cSimOffset for setCurrentABC / setTargetC only.
// Local mockup park: mill C0 <=> Fusion axis C home 90 ⇒ cSimOffset ±90 (sign picks inside vs outside lean).
// Fusion Simulate plays setCurrentABC, not the A/C words on G173.
// Do not use Fusion getABC (returns complement A, e.g. 4.6 for mill 85.4).

function toMillC(geomC) {
  // Wrap into (-180, 180] so mill C stays inside Syncro soft limits C -140 ... 286.8.
  var c = getProperty("cMillSign") * geomC + getProperty("cMillOffset");
  while (c > 180) {
    c -= 360;
  }
  while (c <= -180) {
    c += 360;
  }
  if (c < -140) {
    c += 360; // e.g. -150 -> 210 (still under 286.8)
  }
  return c;
}

function toSimC(millC) {
  return millC + getProperty("cSimOffset");
}

function driveSimABC(aDeg, cMillDeg) {
  var cSim = toSimC(cMillDeg);
  if (typeof setCurrentABC == "function") {
    setCurrentABC(new Vector(toRad(aDeg), 0, toRad(cSim)));
  }
}

function simulationActive() {
  return (typeof simulation != "undefined") &&
    ((typeof getSimulationStreamPath != "function") || (getSimulationStreamPath() != ""));
}

// Retract ram, then set A/C, before any XY plunge. Do not call on every G101.
function simRetractThenOrient() {
  if (!simulationActive()) {
    return;
  }
  try {
    simulation.setTWPModeOff();
    simulation.setTCPModeOff();
    var zUp = 0;
    if (typeof machineConfiguration != "undefined" && machineConfiguration.getAxisZ) {
      var zAxis = machineConfiguration.getAxisZ();
      if (zAxis.getRange && !zAxis.getRange().isNonRange()) {
        zUp = zAxis.getRange().maximum;
      }
    }
    simulation.setTargetZ(zUp);
    simulation.setMotionToRapid();
    simulation.moveToTargetInMachineCoords();
    simulation.setTargetA(toRad(activeA));
    simulation.setTargetC(toRad(toSimC(activeC)));
    simulation.moveToTargetInMachineCoords();
  } catch (e) {
  }
}

function writeBlock() {
  var words = [];
  for (var i = 0; i < arguments.length; ++i) {
    var word = arguments[i];
    if (word !== undefined && word !== "") {
      words.push(word);
    }
  }
  if (words.length) {
    writeln(words.join(" "));
  }
}

function writeComment(text) {
  if (!text) {
    return;
  }
  var line = String(text).replace(/[\(\)]/g, " ");
  writeln("( " + line + " )");
}

function onComment(text) {
  writeComment(text);
}

function onPassThrough(text) {
  writeln(text);
}

function getStockExtent(axis) {
  var upperName = "stock-upper-" + axis;
  var lowerName = "stock-lower-" + axis;
  if (hasGlobalParameter(upperName) && hasGlobalParameter(lowerName)) {
    return Math.abs(getGlobalParameter(upperName) - getGlobalParameter(lowerName));
  }
  return 0;
}

function mapSpindleTool(number) {
  if (number >= 101 && number <= 110) {
    return "41/" + (number - 100);
  }
  if (number >= 1 && number <= 10) {
    return "41/" + number;
  }
  return undefined;
}

function toMPerMin(feedMmMin) {
  if (feedMmMin == undefined) {
    return 0;
  }
  return feedMmMin / 1000;
}

function toSWord(rpm, clockwise) {
  var s = rpm / 1000;
  if (!clockwise) {
    s = -s;
  }
  return "S" + rpmFormat.format(s);
}

function getPlungeMPerMin() {
  var plunge = 2000;
  if (hasParameter("operation:tool_feedPlunge")) {
    plunge = getParameter("operation:tool_feedPlunge");
  } else if (hasParameter("operation:tool_feedEntry")) {
    plunge = getParameter("operation:tool_feedEntry");
  } else if (tool.plungeFeedrate) {
    plunge = tool.plungeFeedrate;
  }
  return toMPerMin(plunge);
}

function forceXYZ() {
  xOutput.reset();
  yOutput.reset();
  zOutput.reset();
}

function forceAny() {
  forceXYZ();
  feedOutput.reset();
}

function toPanel(x, y, z) {
  // Control has TCP (RAGGIO). Autodesk "tcp = true" pattern: after
  // setRotation(sectionWorkPlane), onLinear tip coords are already in the
  // setup/panel (part) system. Do NOT multiply by the tipped workplane again —
  // that double-warps XYZ (air toolpaths posted as Z+ into stock, wild Y).
  return new Vector(x, y, z);
}

function formatX(x) {
  return xOutput.format(x);
}

function formatY(y) {
  // Mill Y after optional sign. useY911: golden dialect #902=#911-(y); Y=#902
  // (Singolo uses #911=DY). Absolute mode: plain Y word via yOutput.
  var yy = getProperty("yMillSign") * y;
  if (getProperty("useY911")) {
    writeln("#902=#911-(" + xyzFormat.format(yy) + ")");
    yOutput.reset(); // next absolute compare (if toggled) stays clean
    return "Y=#902";
  }
  return yOutput.format(yy);
}

function formatZ(zFusion) {
  return zOutput.format(-zFusion);
}

function toolAnglesFromForward(forward) {
  var fx = forward.x;
  var fy = forward.y;
  var fz = forward.z;
  var mag = Math.sqrt(fx * fx + fy * fy + fz * fz);
  if (mag < 1e-8) {
    error(localize("Invalid tool axis."));
    return {vertical:true, a:90, c:0};
  }
  fx /= mag;
  fy /= mag;
  fz /= mag;

  var xy = Math.sqrt(fx * fx + fy * fy);
  var a = toDeg(Math.atan2(fz, xy)); // 90 = +Z, 0 = horizontal
  var c = 0;
  if (xy > 1e-8) {
    c = toDeg(Math.atan2(-fy, fx)); // C0 = +X, +C clockwise from above
  }
  var verticalTol = getProperty("verticalTolerance");
  var vertical = Math.abs(a - 90) <= verticalTol;
  return {vertical:vertical, a:a, c:c};
}

function radiusCompCode() {
  switch (radiusCompensation) {
  case RADIUS_COMPENSATION_LEFT:
    return "G41";
  case RADIUS_COMPENSATION_RIGHT:
    return "G42";
  default:
    return "G40";
  }
}

function writeRadiusCompensation() {
  if (pendingRadiusCompensation >= 0) {
    pendingRadiusCompensation = -1;
    writeln(radiusCompCode());
    forceXYZ();
  }
}

function startRoute(x, y, z) {
  if (routeOpen) {
    return;
  }
  var p = toPanel(x, y, z);
  var nativeTool = mapSpindleTool(tool.number);
  if (nativeTool == undefined) {
    error(subst(localize("v1 only posts electrospindle tools. Use Fusion T1–T10 or T101–T110 (maps to T41/n). Got T%1."), tool.number));
    return;
  }

  var sWord = toSWord(spindleSpeed, tool.clockwise);
  var orientE = getProperty("orientFeed");
  var eWord = "E" + feedFormat.format(orientE > 0 ? orientE : getPlungeMPerMin());
  var tWord = "T" + nativeTool;

  forceAny();
  if (isVerticalTool) {
    activeA = 90;
    activeC = 0;
  }

  simRetractThenOrient();

  // Golden style: one G173 (tool + A/C) ending at approach Z above panel, then feed to the first point.
  var orientFusionZ = getProperty("headOrientHeight");
  if (p.z > orientFusionZ) {
    orientFusionZ = p.z;
  }
  writeBlock(
    "G173",
    formatX(p.x),
    formatY(p.y),
    formatZ(orientFusionZ),
    sWord,
    eWord,
    tWord,
    aOutput.format(activeA),
    cOutput.format(activeC),
    "D0"
  );
  forceXYZ();
  routeOpen = true;
}

function writeLinear(x, y, z, feedMmMin) {
  startRoute(x, y, z);
  writeRadiusCompensation();
  var p = toPanel(x, y, z);
  var f = feedOutput.format(toMPerMin(feedMmMin));
  var xw = formatX(p.x);
  var yw = formatY(p.y);
  var zw = formatZ(p.z);
  if (xw || yw || zw) {
    writeBlock("G101", xw, yw, zw, f);
  } else if (f) {
    feedOutput.reset();
  }
}

function correctHeadHeadAxisOrder() {
  // Fusion post engine historically wants rider then carrier. Mill is C then A.
  // If the attached .mch has C as U, swap so getABC can solve.
  if (typeof machineConfiguration.isHeadConfiguration != "function") {
    return;
  }
  if (!machineConfiguration.isHeadConfiguration()) {
    return;
  }
  try {
    if (machineConfiguration.getAxisU().getCoordinate() == 2) {
      var u = machineConfiguration.getAxisU();
      var v = machineConfiguration.getAxisV();
      machineConfiguration.setAxisU(v);
      machineConfiguration.setAxisV(u);
      setMachineConfiguration(machineConfiguration);
    }
  } catch (e) {
  }
}

function defineMachine() {
  var useTCP = true; // control TCP (RAGGIO 5 A). Keep XYZ in work coords.

  if (!receivedMachineConfiguration || !machineConfiguration.isMultiAxisConfiguration()) {
    // Fallback mill kinematics if Fusion did not attach a 5-axis machine.
    // Do not overwrite a received 5-axis .mch — sim must follow that model.
    var aAxis = createAxis({
      coordinate: 0,
      table      : false,
      axis       : [0, 1, 0], // A about Y at C=0 (swings in XZ)
      range      : [-38.6, 211.4],
      preference : 1,
      tcp        : useTCP
    });
    var cAxis = createAxis({
      coordinate: 2,
      table      : false,
      axis       : [0, 0, -1], // +C clockwise from above
      range      : [-140.0, 286.8],
      cyclic     : false,
      preference : 0,
      tcp        : useTCP
    });
    machineConfiguration = new MachineConfiguration(aAxis, cAxis);
    setMachineConfiguration(machineConfiguration);
    if (receivedMachineConfiguration) {
      warning(localize("The attached machine has no rotary axes. Using mill A/C kinematics as a fallback. Simultaneous 5-axis is not tested."));
      receivedMachineConfiguration = false;
    }
  }

  correctHeadHeadAxisOrder();

  if (!receivedMachineConfiguration && machineConfiguration.isMultiAxisConfiguration()) {
    machineConfiguration.setVirtualTooltip(false);
    machineConfiguration.setMultiAxisFeedrate(
      FEED_FPM,
      9999.99,
      INVERSE_MINUTES,
      0.5,
      1.0
    );
    setMachineConfiguration(machineConfiguration);
  }
}

function activateMachine() {
  if (machineActivated) {
    return;
  }
  machineActivated = true;
  // Do not optimizeMachineAngles2 / getABC: Fusion CA-head IK uses A0 = vertical
  // and would replace mill A85.4 with A4.6. XYZ stay in panel WCS (control TCP).
}

function onOpen() {
  if (getProperty("forceMM")) {
    unit = MM; // fork/harness: let the engine convert inch sample intermediates to mm
  }
  if (unit != MM) {
    error(localize("This Masterwood post is millimetres only."));
    return;
  }

  gangPlanner = makeGangPlanner();
  boringHoles = [];

  receivedMachineConfiguration = machineConfiguration.isReceived();
  defineMachine();
  activateMachine();

  writeln("%");
  writeln("|1 " + (programName ? programName : ""));
  writeln("|2 0");
  writeln("|3 1");
  writeln("|4 " + xyzFormat.format(getStockExtent("x")));
  writeln("|5 " + xyzFormat.format(getStockExtent("z")));
  writeln("|6 " + xyzFormat.format(getStockExtent("y")));
  writeln("|7 0 0 0 0");
  writeln("|8 0");
  writeln("|9 4000");
  writeln("|10 ");
  writeln("|11 1");
  writeln("|12 ");
  writeln("|13 ");
  writeln("|14 ");
  writeln("|44 0");
  writeln(":1");
  writeln("G120 K" + getProperty("workField"));
  writeln("#910=DX");
  writeln("#911=DY");
  writeln("M61 K" + getProperty("vacuumField") + " D1");
  if (programComment) {
    writeComment(programComment);
  }
}

function onSection() {
  if (currentSection.isMultiAxis()) {
    error(localize("Simultaneous 5-axis is not supported in v1. Use operation Tool Orientation (3+2)."));
    return;
  }

  activateMachine();

  sectionWorkPlane = currentSection.workPlane;
  // TCP / part coordinates: setRotation(W) so tip XYZ stay in setup WCS.
  // A/C still come from sectionWorkPlane.forward. See toPanel().
  setRotation(sectionWorkPlane);

  var angles = toolAnglesFromForward(sectionWorkPlane.forward);
  isVerticalTool = angles.vertical;
  activeA = isVerticalTool ? 90 : angles.a;
  activeC = isVerticalTool ? 0 : toMillC(angles.c);

  driveSimABC(activeA, activeC);

  routeOpen = false;
  pendingRadiusCompensation = -1;
  forceAny();

  boringStation = getBoringStation(tool.number);
  boringSection = boringStation > 0;
  if (boringSection && !isVerticalTool) {
    error(localize("Fork: boring-head tools (T201..T250) are vertical only. Use a top-down setup / tool orientation."));
    return;
  }
  if (boringSection && getProperty("checkStationDiameter")) {
    var expectedDia = boringDiameterMm(boringStation);
    if (expectedDia > 0 && tool.diameter && Math.abs(tool.diameter - expectedDia) > 0.15) {
      error(subst(
        localize("Fork: tool diameter %1 mm does not match boring station %2 (%3 mm in TAB01)."),
        tool.diameter,
        boringStation,
        expectedDia
      ));
      return;
    }
  }

  writeComment(getParameter("operation-comment", ""));
  // Mill A/C for this section are applied on the first G173 at headOrientHeight.
}

function onRadiusCompensation() {
  pendingRadiusCompensation = radiusCompensation;
}

function onRapid(x, y, z) {
  if (boringSection) {
    return; // fork: G100 positions itself; ignore Fusion linking rapids
  }
  var feed = 0;
  if (hasParameter("operation:tool_feedRetract")) {
    feed = getParameter("operation:tool_feedRetract");
  } else if (hasParameter("operation:tool_feedEntry")) {
    feed = getParameter("operation:tool_feedEntry");
  } else {
    feed = 2000;
  }
  writeLinear(x, y, z, feed);
}

function onLinear(x, y, z, feed) {
  if (boringSection) {
    error(localize("Fork: boring-head tool used in a non-drilling operation."));
    return;
  }
  writeLinear(x, y, z, feed);
}

function onCircular(clockwise, cx, cy, cz, x, y, z, feed) {
  if (pendingRadiusCompensation >= 0) {
    error(localize("Radius compensation cannot change on an arc."));
    return;
  }
  startRoute(x, y, z);
  if (getCircularPlane() != PLANE_XY) {
    linearize(tolerance);
    return;
  }
  var end = toPanel(x, y, z);
  var f = feedOutput.format(toMPerMin(feed));
  writeBlock(
    clockwise ? "G102" : "G103",
    formatX(end.x),
    formatY(end.y),
    formatZ(end.z),
    "R" + rFormat.format(getCircularRadius()),
    f
  );
}

// ---------------------------------------------------------------------------
// Fork: vertical boring (G100) and gang grouping.
// The block between the GANG-PURE markers is plain JavaScript. The node
// harness evaluates that block alone, so it must not call the Fusion post API.
// ---------------------------------------------------------------------------
// >>> GANG-PURE-BEGIN
function gangFormatNum(n, decimals) {
  if (typeof n != "number" || isNaN(n)) {
    return "0";
  }
  var s = n.toFixed(decimals);
  if (s.indexOf(".") >= 0) {
    s = s.replace(/0+$/, "").replace(/\.$/, "");
  }
  if (s == "-0") {
    return "0";
  }
  return s;
}

function gangSame(a, b, tol) {
  return Math.abs(a - b) <= tol;
}

function gangIndexOf(arr, value) {
  var i;
  for (i = 0; i < arr.length; ++i) {
    if (arr[i] === value) {
      return i;
    }
  }
  return -1;
}

function gangMirrorList(stations, rowFirst, rowLast) {
  var out = [];
  var i;
  for (i = 0; i < stations.length; ++i) {
    out.push(rowFirst + rowLast - stations[i]);
  }
  return out;
}

function gangProgramY(fusionY, fmt) {
  var y = (fmt.ySign || 1) * fusionY;
  if (fmt.useY911 && fmt.dy > 0) {
    return fmt.dy - y;
  }
  return y;
}

function gangCluster(items, valueOf, tol) {
  var clusters = [];
  var i;
  for (i = 0; i < items.length; ++i) {
    var v = valueOf(items[i]);
    var placed = false;
    var c;
    for (c = 0; c < clusters.length; ++c) {
      if (gangSame(clusters[c].anchor, v, tol)) {
        clusters[c].items.push(items[i]);
        placed = true;
        break;
      }
    }
    if (!placed) {
      clusters.push({anchor:v, items:[items[i]]});
    }
  }
  return clusters;
}

// Diameters from TAB01.DAT (same file as MW310 PARAM.zip Param/TAB01.DAT).
// The diameter column is 0.01 mm. Station 10 is left out: the name says
// Drevelboor 57x6 while the field is 700. Station 7 is empty.
function boringDiameterMm(station) {
  switch (station) {
  case 1:
    return 3;
  case 2:
  case 3:
  case 4:
  case 5:
  case 6:
    return 5;
  case 8:
    return 4.5;
  case 9:
    return 8;
  case 12:
    return 35;
  case 13:
    return 10;
  default:
    return 0;
  }
}

function createGangPlanner(opts) {
  return {
    pitch: opts.pitch,
    stations: opts.stations,
    tol: opts.tol,
    maxGroups: opts.maxGroups,
    groups: {},
    groupOrder: [],
    emitted: {},
    limitWarned: false
  };
}

function gangPushWarn(warnings, text) {
  if (warnings.length < 12) {
    warnings.push(text);
  }
}

function gangCheckPoint(planner, fmt, x, y, warnings) {
  if (!(fmt.dx > 0) || !(fmt.dy > 0)) {
    return;
  }
  var py = gangProgramY(y, fmt);
  if (x < -planner.tol || x > fmt.dx + planner.tol || py < -planner.tol || py > fmt.dy + planner.tol) {
    gangPushWarn(warnings, "Gang: drilled point X" + gangFormatNum(x, 2) + " Y" + gangFormatNum(py, 2) + " is outside the panel.");
  }
}

function gangDefine(planner, subset) {
  var key = subset.join(",");
  if (planner.groups[key]) {
    return planner.groups[key].n;
  }
  var fullKey = planner.stations.join(",");
  var n;
  if (key == fullKey) {
    n = 81;
  } else {
    var used = {};
    var i;
    for (i = 0; i < planner.groupOrder.length; ++i) {
      used[planner.groups[planner.groupOrder[i]].n] = true;
    }
    n = 82;
    while (used[n]) {
      n++;
    }
  }
  if (n > 80 + planner.maxGroups) {
    return 0;
  }
  planner.groups[key] = {
    n: n,
    stations: subset.slice(),
    mirror: gangMirrorList(subset, planner.stations[0], planner.stations[planner.stations.length - 1])
  };
  planner.groupOrder.push(key);
  return n;
}

function gangSingleStroke(h) {
  return {kind:"single", x:h.x, y:h.y, z:h.z, f:h.f, t:h.station};
}

function gangGreedyRow(planner, rowHoles, fmt, warnings) {
  var remaining = rowHoles.slice().sort(function(a, b) {
    return a.x - b.x;
  });
  var originalCount = remaining.length;
  var strokes = [];
  var stations = planner.stations;
  var nGang = stations.length;
  while (remaining.length) {
    var x0 = remaining[0].x;
    var chosen = [];
    var used = {};
    var k;
    var j;
    for (k = 0; k < nGang; ++k) {
      var target = x0 + planner.pitch * k;
      var best = -1;
      var bestDist = planner.tol + 1;
      for (j = 0; j < remaining.length; ++j) {
        if (used[j]) {
          continue;
        }
        var dist = Math.abs(remaining[j].x - target);
        if (dist <= planner.tol && dist < bestDist) {
          best = j;
          bestDist = dist;
        }
      }
      if (best >= 0) {
        used[best] = true;
        chosen.push({hole:remaining[best], station:stations[k]});
      }
    }
    var next = [];
    for (j = 0; j < remaining.length; ++j) {
      if (!used[j]) {
        next.push(remaining[j]);
      }
    }
    remaining = next;
    if (chosen.length <= 1) {
      var alone = chosen[0].hole;
      if (originalCount > 1) {
        gangPushWarn(
          warnings,
          "Gang: hole X" + gangFormatNum(alone.x, 2) + " Y" + gangFormatNum(gangProgramY(alone.y, fmt), 2) + " does not share the " + planner.pitch + " mm pitch; posted as single T" + alone.station + "."
        );
      }
      gangCheckPoint(planner, fmt, alone.x, alone.y, warnings);
      strokes.push(gangSingleStroke(alone));
      continue;
    }
    var subset = [];
    for (k = 0; k < chosen.length; ++k) {
      subset.push(chosen[k].station);
    }
    var groupNumber = gangDefine(planner, subset);
    if (!groupNumber) {
      if (!planner.limitWarned) {
        planner.limitWarned = true;
        warnings.push("Gang: more than " + planner.maxGroups + " spindle groups; extra holes posted as single G100.");
      }
      for (k = 0; k < chosen.length; ++k) {
        gangCheckPoint(planner, fmt, chosen[k].hole.x, chosen[k].hole.y, warnings);
        strokes.push(gangSingleStroke(chosen[k].hole));
      }
      continue;
    }
    var anchor = chosen[0].hole;
    for (k = 0; k < subset.length; ++k) {
      var idx = gangIndexOf(stations, subset[k]);
      gangCheckPoint(planner, fmt, anchor.x + planner.pitch * idx, anchor.y, warnings);
    }
    strokes.push({kind:"gang", x:anchor.x, y:anchor.y, z:anchor.z, f:anchor.f, t:groupNumber});
  }
  return strokes;
}

function planGangStrokes(planner, holes, fmt) {
  var warnings = [];
  var eligible = [];
  var singles = [];
  var i;
  for (i = 0; i < holes.length; ++i) {
    var h = holes[i];
    if (fmt.gangEnabled && gangIndexOf(planner.stations, h.station) >= 0) {
      eligible.push(h);
    } else {
      gangCheckPoint(planner, fmt, h.x, h.y, warnings);
      singles.push(gangSingleStroke(h));
    }
  }
  var rows = [];
  var yClusters = gangCluster(eligible, function(item) {
    return item.y;
  }, planner.tol);
  var yc;
  for (yc = 0; yc < yClusters.length; ++yc) {
    var zClusters = gangCluster(yClusters[yc].items, function(item) {
      return item.z;
    }, planner.tol);
    var zc;
    for (zc = 0; zc < zClusters.length; ++zc) {
      var fClusters = gangCluster(zClusters[zc].items, function(item) {
        return item.f;
      }, 0.001);
      var fc;
      for (fc = 0; fc < fClusters.length; ++fc) {
        rows.push(fClusters[fc].items);
      }
    }
  }
  rows.sort(function(a, b) {
    var py = gangProgramY(a[0].y, fmt) - gangProgramY(b[0].y, fmt);
    if (Math.abs(py) > planner.tol) {
      return py;
    }
    var pz = a[0].z - b[0].z;
    if (Math.abs(pz) > planner.tol) {
      return pz;
    }
    return a[0].f - b[0].f;
  });
  var gangs = [];
  var loose = singles.slice();
  var r;
  for (r = 0; r < rows.length; ++r) {
    var produced = gangGreedyRow(planner, rows[r], fmt, warnings);
    if (r % 2 == 1) {
      produced.reverse();
    }
    var p;
    for (p = 0; p < produced.length; ++p) {
      if (produced[p].kind == "gang") {
        gangs.push(produced[p]);
      } else {
        loose.push(produced[p]);
      }
    }
  }
  loose.sort(function(a, b) {
    var py = gangProgramY(a.y, fmt) - gangProgramY(b.y, fmt);
    if (Math.abs(py) > planner.tol) {
      return py;
    }
    var pz = a.z - b.z;
    if (Math.abs(pz) > planner.tol) {
      return pz;
    }
    if (Math.abs(a.x - b.x) > planner.tol) {
      return a.x - b.x;
    }
    return a.t - b.t;
  });
  var fresh = [];
  for (i = 0; i < planner.groupOrder.length; ++i) {
    var g = planner.groups[planner.groupOrder[i]];
    if (!planner.emitted[g.n]) {
      fresh.push(g);
      planner.emitted[g.n] = true;
    }
  }
  fresh.sort(function(a, b) {
    return a.n - b.n;
  });
  return {strokes:gangs.concat(loose), newGroups:fresh, warnings:warnings};
}

function renderBoringLines(plan, fmt) {
  var lines = [];
  var ySign = fmt.ySign || 1;
  var i;
  for (i = 0; i < plan.newGroups.length; ++i) {
    var g = plan.newGroups[i];
    lines.push("#T" + g.n + "=" + g.stations.join(","));
    lines.push("#X" + g.n + "=" + g.mirror.join(","));
    lines.push("#S" + g.n + "=" + g.mirror.join(","));
  }
  for (i = 0; i < plan.strokes.length; ++i) {
    var st = plan.strokes[i];
    var shown = ySign * st.y;
    var yWord;
    if (fmt.useY911) {
      lines.push("#902=#911-(" + gangFormatNum(shown, 2) + ")");
      yWord = "Y=#902";
    } else {
      yWord = "Y" + gangFormatNum(shown, 2);
    }
    lines.push("G100 X" + gangFormatNum(st.x, 2) + " " + yWord + " Z" + gangFormatNum(st.z, 2) + " F" + gangFormatNum(st.f, 1) + " T" + st.t);
  }
  return lines;
}
// >>> GANG-PURE-END

function getBoringStation(number) {
  var base = getProperty("boringToolBase");
  if (number > base && number <= base + 50) {
    return number - base;
  }
  return 0;
}

function readGangStations() {
  var parts = String(getProperty("gangStations")).split(",");
  var stations = [];
  var i;
  for (i = 0; i < parts.length; ++i) {
    var n = parseInt(parts[i], 10);
    if (!isNaN(n)) {
      stations.push(n);
    }
  }
  if (stations.length < 2) {
    error(localize("Fork: gangStations needs at least two stations, low X to high X."));
    return [2, 3, 4, 5, 6];
  }
  for (i = 1; i < stations.length; ++i) {
    if (stations[i] !== stations[i - 1] + 1) {
      error(localize("Fork: gangStations must be consecutive along X, for example 2,3,4,5,6."));
      break;
    }
  }
  return stations;
}

function makeGangPlanner() {
  var pitch = getProperty("gangPitch");
  if (!(pitch > 0)) {
    error(localize("Fork: gang pitch must be greater than 0."));
    pitch = 32;
  }
  var maxGroups = getProperty("maxGangGroups");
  if (!(maxGroups >= 1)) {
    error(localize("Fork: max gang groups must be at least 1."));
    maxGroups = 3;
  }
  return createGangPlanner({
    pitch: pitch,
    stations: readGangStations(),
    tol: 0.01,
    maxGroups: maxGroups
  });
}

function flushBoringHoles() {
  if (!boringHoles.length) {
    return;
  }
  var holes = boringHoles;
  boringHoles = [];
  if (!gangPlanner) {
    error(localize("Fork: gang planner was not initialised."));
    return;
  }
  var fmt = {
    gangEnabled: !!getProperty("gangDrilling"),
    ySign: getProperty("yMillSign"),
    useY911: !!getProperty("useY911"),
    dy: getStockExtent("y"),
    dx: getStockExtent("x")
  };
  var plan = planGangStrokes(gangPlanner, holes, fmt);
  var i;
  for (i = 0; i < plan.warnings.length; ++i) {
    warning(plan.warnings[i]);
  }
  var lines = renderBoringLines(plan, fmt);
  for (i = 0; i < lines.length; ++i) {
    writeln(lines[i]);
  }
  yOutput.reset();
}

function onCycle() {
}

function onCyclePoint(x, y, z) {
  if (!boringSection) {
    expandCyclePoint(x, y, z); // electrospindle drill: same G173/G101 output as live post
    return;
  }
  switch (cycleType) {
  case "drilling":
  case "counter-boring":
    break;
  case "chip-breaking":
  case "deep-drilling":
    if (isFirstCyclePoint()) {
      warning(localize("Fork: G100 has no peck. Pecking ignored, single stroke to full depth."));
    }
    break;
  default:
    error(subst(localize("Fork: cycle '%1' is not supported on the boring head."), cycleType));
    return;
  }
  var depth = -z; // hole bottom; mill Z+ into the panel
  var thickness = getStockExtent("z");
  if (depth <= 0) {
    error(localize("Fork: hole bottom is not below the panel top."));
    return;
  }
  if (thickness > 0 && depth > thickness + getProperty("boringMaxOverThrough")) {
    error(subst(localize("Fork: G100 depth %1 is deeper than panel %2 + limit."), xyzFormat.format(depth), xyzFormat.format(thickness)));
    return;
  }
  var p = toPanel(x, y, z);
  boringHoles.push({
    x: p.x,
    y: p.y,
    z: depth,
    f: toMPerMin(cycle.feedrate),
    station: boringStation
  });
}

function onCycleEnd() {
  if (boringSection) {
    flushBoringHoles();
  }
}

function onDwell(seconds) {
}

function onSpindleSpeed(spindleSpeed) {
}

function onCommand(command) {
  switch (command) {
  case COMMAND_STOP:
  case COMMAND_OPTIONAL_STOP:
  case COMMAND_END:
  case COMMAND_SPINDLE_CLOCKWISE:
  case COMMAND_SPINDLE_COUNTERCLOCKWISE:
  case COMMAND_START_SPINDLE:
  case COMMAND_STOP_SPINDLE:
  case COMMAND_LOAD_TOOL:
  case COMMAND_COOLANT_ON:
  case COMMAND_COOLANT_OFF:
  case COMMAND_LOCK_MULTI_AXIS:
  case COMMAND_UNLOCK_MULTI_AXIS:
    return;
  }
}

function onSectionEnd() {
  if (boringSection) {
    flushBoringHoles();
  }
  if (radiusCompensation != RADIUS_COMPENSATION_OFF) {
    writeln("G40");
  }
  routeOpen = false;
  boringSection = false;
  forceAny();
}

function onClose() {
  writeln("%");
}
