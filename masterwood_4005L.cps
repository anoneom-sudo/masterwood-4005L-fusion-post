/**
  Masterwood MW310 Project 4005L
  Native PRG: % header |1..|14 :1 G120 G172/G173 G101 G100 %
  Spindle tools T41/1..T41/10 on the G172/G173 line
  G172 … J90          vertical
  G173 … A.. C.. D0   3+2
  S = rpm/1000, F = m/min, E = plunge
  Z+ into the panel (negate Fusion Z)
  Work XYZ + A + C; no TWP; no TCP output
  A90 = tool down; A0 C0 = tool right; +C clockwise from above
  Pivot 184.90 mm is on the control
  3+2 only in v1

  Golden files: samples/Test.PRG, samples/test2.PRG
  Spec: FUSION_MASTERWOOD_4005L_POST_HANDOFF.md

  FORKID {B3E91C70-4A5D-4F2B-9E18-7C2A1F06D4B8}
*/

description = "Masterwood 4005L MW310";
vendor = "Masterwood";
vendorUrl = "http://www.masterwood.com";
legal = "Copyright (C) 2012-2026 by Autodesk, Inc. Native MW310 dialect for Project 4005L.";
certificationLevel = 0;
minimumRevision = 45917;

longDescription = "Native MW310 post for Masterwood Project 4005L. Emits G172/G173 and T41/n. 3+2 first; simultaneous 5-axis is rejected.";

extension = "prg";
setCodePage("ascii");

capabilities = CAPABILITY_MILLING;
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
    description: "Treat the tool as vertical (G172 J90) when the workplane Z is within this angle of setup Z.",
    group      : "preferences",
    type       : "number",
    value      : 0.1,
    scope      : "post"
  }
};

var xyzFormat = createFormat({decimals:2, type:FORMAT_REAL});
var abcFormat = createFormat({decimals:1, type:FORMAT_REAL});
var feedFormat = createFormat({decimals:1, type:FORMAT_REAL}); // m/min
var rpmFormat = createFormat({decimals:1, type:FORMAT_REAL}); // rpm/1000
var rFormat = createFormat({decimals:2, type:FORMAT_REAL});

var xOutput = createOutputVariable({prefix:"X"}, xyzFormat);
var yOutput = createOutputVariable({prefix:"Y"}, xyzFormat);
var zOutput = createOutputVariable({prefix:"Z"}, xyzFormat);
var feedOutput = createOutputVariable({prefix:"F"}, feedFormat);

var pendingRadiusCompensation = -1;
var routeOpen = false;
var activeA = 90;
var activeC = 0;
var isVerticalTool = true;
var sectionWorkPlane = new Matrix();

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
  return sectionWorkPlane.multiply(new Vector(x, y, z));
}

function formatX(x) {
  return xOutput.format(x);
}

function formatY(y) {
  return yOutput.format(y);
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
  var eWord = "E" + feedFormat.format(getPlungeMPerMin());
  var tWord = "T" + nativeTool;

  forceAny();
  if (isVerticalTool) {
    writeBlock(
      "G172",
      formatX(p.x),
      formatY(p.y),
      formatZ(p.z),
      sWord,
      eWord,
      tWord,
      "J90"
    );
  } else {
    writeBlock(
      "G173",
      formatX(p.x),
      formatY(p.y),
      formatZ(p.z),
      sWord,
      eWord,
      tWord,
      "A" + abcFormat.format(activeA),
      "C" + abcFormat.format(activeC),
      "D0"
    );
  }
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

function onOpen() {
  if (unit != MM) {
    error(localize("This Masterwood post is millimetres only."));
    return;
  }

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

  sectionWorkPlane = currentSection.workPlane;
  setRotation(sectionWorkPlane);

  var angles = toolAnglesFromForward(sectionWorkPlane.forward);
  isVerticalTool = angles.vertical;
  activeA = angles.a;
  activeC = angles.c;
  routeOpen = false;
  pendingRadiusCompensation = -1;
  forceAny();

  writeComment(getParameter("operation-comment", ""));
}

function onRadiusCompensation() {
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
  writeLinear(x, y, z, feed);
}

function onLinear(x, y, z, feed) {
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
  if (radiusCompensation != RADIUS_COMPENSATION_OFF) {
    writeln("G40");
  }
  routeOpen = false;
  forceAny();
}

function onClose() {
  writeln("%");
}
