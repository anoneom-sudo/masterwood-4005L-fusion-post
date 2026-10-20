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

  FORK "linkhome" (2026-10-19): inside a tilted op, a Fusion link (rapid /
  high-feed moves: retract, travel) is replaced by a new G173 at the re-entry
  point when the estimated home route is faster than staying down at the
  linking feed. Plunge / lead-in / cutting moves are untouched.
  See fork-linkhome/README.md. Live post: ../masterwood_4005L.cps.

  FORKID {45056685-FFA8-4020-8F11-A2B4EC8710E9}
*/

description = "Masterwood 4005L MW310 (linkhome fork)";
vendor = "Masterwood";
vendorUrl = "http://www.masterwood.com";
legal = "Copyright (C) 2012-2026 by Autodesk, Inc. Native MW310 dialect for Project 4005L.";
certificationLevel = 0;
minimumRevision = 45917;

longDescription = "Native MW310 post for Masterwood Project 4005L. Vertical and 3+2 use G173 A/C D0 (A90 C0 when the tool is down). Simultaneous 5-axis is rejected.";

extension = "prg";
setCodePage("ascii");

capabilities = CAPABILITY_MILLING | CAPABILITY_MACHINE_SIMULATION;
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
  cSimOffset: {
    title      : "Simulate C offset (deg)",
    description: "Added only for Fusion Machine Sim (setCurrentABC / setTargetC), not on G173. Mill park C0 = Fusion C home 90. Use ±90; +90 vs -90 flips lean inside/outside (180° about vertical). Default 90 (2026-10-19, paired with cMillOffset 180; was -90 with offset 0).",
    group      : "preferences",
    type       : "number",
    value      : 90,
    scope      : "post"
  },
  linkViaHome: {
    title      : "Link via home (G173 re-entry)",
    description: "Tilted ops only. Replace a Fusion link (rapid / high-feed retract + travel) with a new G173 (same T/S/E/A/C, D0) at the re-entry point when the estimated home route is faster than staying down at the linking feed. false = live-post output.",
    group      : "linking",
    type       : "boolean",
    value      : true,
    scope      : "post"
  },
  rapidSpeedEstimate: {
    title      : "Rapid XY speed estimate (m/min) - ASSUMPTION",
    description: "ASSUMPTION, Johannes to confirm on the mill. Rapid XY speed during the G173 home move. Used only for the time decision.",
    group      : "linking",
    type       : "number",
    value      : 40,
    scope      : "post"
  },
  rapidSpeedZEstimate: {
    title      : "Rapid Z speed estimate (m/min) - ASSUMPTION",
    description: "ASSUMPTION. Z lift to home during G173. 19.2 = Syncro.prm axis W 'VEL max 19200' read as mm/min (unit not confirmed). Used only for the time decision.",
    group      : "linking",
    type       : "number",
    value      : 19.2,
    scope      : "post"
  },
  homeZEstimate: {
    title      : "Home Z above part top (mm) - ASSUMPTION",
    description: "ASSUMPTION, Johannes to confirm. Height above Fusion Z0 (stock top) the head lifts to on G173. Larger = home route costs more = fewer re-entries.",
    group      : "linking",
    type       : "number",
    value      : 150,
    scope      : "post"
  },
  minLinkLengthForHome: {
    title      : "Min link length for home route (mm)",
    description: "Links whose Fusion path (retract + travel) is shorter than this always stay down as G101.",
    group      : "linking",
    type       : "number",
    value      : 150,
    scope      : "post"
  },
  linkAccelEstimate: {
    title      : "G101 accel estimate (mm/s^2) - ASSUMPTION",
    description: "ASSUMPTION. Interpolation acceleration for the stay-down estimate (each link segment starts and stops). 200 = Syncro.prm ACC_INT read as mm/s^2 (unit not confirmed). 0 = ignore acceleration (length / feed only).",
    group      : "linking",
    type       : "number",
    value      : 200,
    scope      : "post"
  },
  linkHomeOverhead: {
    title      : "G173 overhead (s) - ASSUMPTION",
    description: "ASSUMPTION. Fixed time added to each home route (stop, G173 block handling, settle).",
    group      : "linking",
    type       : "number",
    value      : 0.5,
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
  flushLink(false);
  writeComment(text);
}

function onPassThrough(text) {
  flushLink(false);
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

  writeG173(p, sWord, eWord, tWord);
  routeOpen = true;
}

function getOrientFusionZ(p) {
  var orientFusionZ = getProperty("headOrientHeight");
  if (p.z > orientFusionZ) {
    orientFusionZ = p.z;
  }
  return orientFusionZ;
}

function writeG173(p, sWord, eWord, tWord) {
  // Golden style: one G173 (tool + A/C) ending at approach Z above panel, then feed to the first point.
  var orientFusionZ = getOrientFusionZ(p);
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
  lastPos = new Vector(p.x, p.y, orientFusionZ);
}

// ---- linkhome fork ---------------------------------------------------------
var lastPos = undefined;      // last programmed tip position (setup WCS, Fusion Z)
var linkBuffer = [];          // buffered link moves {x,y,z,feed}
var linkStart = undefined;    // position where the buffered link starts
var linkDeferredComp = -1;    // radius comp change seen while buffering
var linkStats = {home:0, stay:0, short:0, noTravel:0, endOfSection:0};

function isLinkMovement() {
  return (movement == MOVEMENT_RAPID) || (movement == MOVEMENT_HIGH_FEED);
}

function linkBufferingActive() {
  return getProperty("linkViaHome") && routeOpen && !isVerticalTool && !currentSection.isMultiAxis();
}

function segTime(len, feedMmMin) {
  // seconds; trapezoid from stop to stop when an accel is given
  if (len <= 0 || !(feedMmMin > 0)) {
    return 0;
  }
  var v = feedMmMin / 60;
  var acc = getProperty("linkAccelEstimate");
  if (!(acc > 0)) {
    return len / v;
  }
  if (len >= v * v / acc) {
    return len / v + v / acc;
  }
  return 2 * Math.sqrt(len / acc);
}

function bufferLink(x, y, z, feed) {
  if (linkBuffer.length == 0) {
    linkStart = lastPos;
  }
  linkBuffer.push({x:x, y:y, z:z, feed:feed});
}

function replayLink(list) {
  for (var i = 0; i < list.length; ++i) {
    writeLinear(list[i].x, list[i].y, list[i].z, list[i].feed);
  }
}

function applyDeferredComp() {
  if (linkDeferredComp >= 0) {
    pendingRadiusCompensation = linkDeferredComp;
    linkDeferredComp = -1;
  }
}

// reEntry: true when a non-link move follows in the same section.
function flushLink(reEntry) {
  if (linkBuffer.length == 0) {
    return;
  }
  var list = linkBuffer;
  var start = linkStart;
  linkBuffer = [];
  linkStart = undefined;

  var useHome = false;
  var why = "";
  var end = list[list.length - 1];
  // Safety: the G173 lift to home is assumed to be straight up (machine Z), not along
  // the tilted tool axis. Keep Fusion's own retract moves (G101) until the tip is at
  // or above the part top (Fusion Z0 = stock top), and only replace the rest.
  var keep = -1;
  for (var k = 0; k < list.length; ++k) {
    if (list[k].z >= 0) {
      keep = k;
      break;
    }
  }
  var prefix = (keep >= 0) ? list.slice(0, keep + 1) : list;
  var rest = (keep >= 0) ? list.slice(keep + 1) : [];
  if (!reEntry || start == undefined) {
    linkStats.endOfSection++;
    why = "no re-entry in this section";
  } else if (rest.length == 0) {
    linkStats.noTravel++;
    why = "never above part top, or nothing after the retract";
    log("link stay (" + why + ")");
  } else {
    start = new Vector(prefix[prefix.length - 1].x, prefix[prefix.length - 1].y, prefix[prefix.length - 1].z);
    list = rest;
    var pathLen = 0;
    var stay = 0;
    var prev = start;
    for (var i = 0; i < list.length; ++i) {
      var d = Vector.diff(new Vector(list[i].x, list[i].y, list[i].z), prev).length;
      pathLen += d;
      stay += segTime(d, list[i].feed);
      prev = new Vector(list[i].x, list[i].y, list[i].z);
    }
    var homeZ = getProperty("homeZEstimate");
    var orientZ = getOrientFusionZ(new Vector(end.x, end.y, end.z));
    var vXY = getProperty("rapidSpeedEstimate") * 1000 / 60;
    var vZ = getProperty("rapidSpeedZEstimate") * 1000 / 60;
    var orientE = getProperty("orientFeed");
    var vE = (orientE > 0 ? orientE : getPlungeMPerMin()) * 1000 / 60;
    var dxy = Math.sqrt((end.x - start.x) * (end.x - start.x) + (end.y - start.y) * (end.y - start.y));
    var home = Math.max(0, homeZ - start.z) / vZ +
      dxy / vXY +
      Math.max(0, homeZ - orientZ) / vE +
      segTime(Math.max(0, orientZ - end.z), end.feed) +
      getProperty("linkHomeOverhead");
    if (pathLen < getProperty("minLinkLengthForHome")) {
      linkStats.short++;
      why = "short " + xyzFormat.format(pathLen) + "mm";
    } else if (home < stay) {
      useHome = true;
      linkStats.home++;
    } else {
      linkStats.stay++;
    }
    log("link " + (useHome ? "HOME" : "stay") + " len=" + xyzFormat.format(pathLen) +
      " stay=" + rFormat.format(stay) + "s home=" + rFormat.format(home) + "s " + why);
  }

  if (!useHome) {
    replayLink(prefix.concat(rest));
    applyDeferredComp();
    return;
  }
  replayLink(prefix); // Fusion retract up to the part top, unchanged

  // Home route: the control lifts to home, rapids, (re)orients and drops at E
  // to the orient height above the re-entry point. Same words as the first G173.
  var nativeTool = mapSpindleTool(tool.number);
  var sWord = toSWord(spindleSpeed, tool.clockwise);
  var eWord = "E" + feedFormat.format(orientE > 0 ? orientE : getPlungeMPerMin());
  var tWord = "T" + nativeTool;
  forceAny();
  simRetractThenOrient();
  writeG173(toPanel(end.x, end.y, end.z), sWord, eWord, tWord);
  // Continue from the orient height to the link end at the linking feed (explicit F),
  // exactly like the move after the first G173 of a section.
  writeLinear(end.x, end.y, end.z, end.feed);
  applyDeferredComp();
}
// ---------------------------------------------------------------------------

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
  lastPos = new Vector(x, y, z);
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
  if (unit != MM) {
    error(localize("This Masterwood post is millimetres only."));
    return;
  }

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
  linkBuffer = [];
  linkStart = undefined;
  linkDeferredComp = -1;
  lastPos = undefined;
  forceAny();

  writeComment(getParameter("operation-comment", ""));
  // Mill A/C for this section are applied on the first G173 at headOrientHeight.
}

function onRadiusCompensation() {
  if (linkBuffer.length > 0) {
    linkDeferredComp = radiusCompensation; // applied after the buffered link is written
    return;
  }
  pendingRadiusCompensation = radiusCompensation;
}

function onRapid(x, y, z) {
  var feed = 0;
  if (hasParameter("operation:tool_feedRetract")) {
    feed = getParameter("operation:tool_feedRetract");
  } else if (hasParameter("operation:tool_feedEntry")) {
    feed = getParameter("operation:tool_feedEntry");
  } else {
    feed = 2000;
  }
  if (linkBufferingActive()) {
    bufferLink(x, y, z, feed);
    return;
  }
  writeLinear(x, y, z, feed);
}

function onLinear(x, y, z, feed) {
  if (isLinkMovement() && linkBufferingActive()) {
    bufferLink(x, y, z, feed);
    return;
  }
  flushLink(true);
  writeLinear(x, y, z, feed);
}

function onCircular(clockwise, cx, cy, cz, x, y, z, feed) {
  if (pendingRadiusCompensation >= 0) {
    error(localize("Radius compensation cannot change on an arc."));
    return;
  }
  flushLink(true);
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
  lastPos = new Vector(x, y, z);
}

function onDwell(seconds) {
  flushLink(false);
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
  flushLink(false);
  if (radiusCompensation != RADIUS_COMPENSATION_OFF) {
    writeln("G40");
  }
  routeOpen = false;
  forceAny();
}

function onClose() {
  if (getProperty("linkViaHome")) {
    log("linkhome: " + linkStats.home + " links via G173 home, " + linkStats.stay + " stayed (time), " +
      linkStats.short + " stayed (short), " + linkStats.noTravel + " stayed (never above part top, or no travel after the retract), " + linkStats.endOfSection + " end-of-section kept");
  }
  writeln("%");
}
