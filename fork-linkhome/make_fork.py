# Builds masterwood_4005L_linkhome.cps from the live post by exact-text patches.
import sys
# usage: make_fork.py <live.cps> <out.cps> [--live]
#   --live: keep the live FORKID and description (result becomes the live post)
src = sys.argv[1]; dst = sys.argv[2]
LIVE = "--live" in sys.argv[3:]
s = open(src, encoding='utf-8').read()
def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (c, a[:80])
    s = s.replace(a, b)

if LIVE:
    rep("""  Golden files: samples/Test.PRG, samples/test2.PRG
  Spec: AGENTS.md (STATUS scoreboard in Obsidian)
""", """  Golden files: samples/Test.PRG, samples/test2.PRG
  Spec: AGENTS.md (STATUS scoreboard in Obsidian)

  Linkhome (live 2026-10-19): inside a tilted op, a Fusion link (rapid /
  high-feed travel after the retract to the part top) is replaced by a new
  G173 at the re-entry point when the estimated home route is faster than
  staying down at the linking feed (property linkViaHome). Plunge / lead-in /
  cutting moves are untouched. See fork-linkhome/README.md.
""")
else:
    rep("""  Golden files: samples/Test.PRG, samples/test2.PRG
  Spec: AGENTS.md (STATUS scoreboard in Obsidian)

  FORKID {B3E91C70-4A5D-4F2B-9E18-7C2A1F06D4B8}""",
"""  Golden files: samples/Test.PRG, samples/test2.PRG
  Spec: AGENTS.md (STATUS scoreboard in Obsidian)

  FORK "linkhome" (2026-10-19): inside a tilted op, a Fusion link (rapid /
  high-feed moves: retract, travel) is replaced by a new G173 at the re-entry
  point when the estimated home route is faster than staying down at the
  linking feed. Plunge / lead-in / cutting moves are untouched.
  See fork-linkhome/README.md. Live post: ../masterwood_4005L.cps.

  FORKID {45056685-FFA8-4020-8F11-A2B4EC8710E9}""")

    rep('description = "Masterwood 4005L MW310";', 'description = "Masterwood 4005L MW310 (linkhome fork)";')

rep("""    value      : 90,
    scope      : "post"
  }
};""", """    value      : 90,
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
};""")

# G173 writer shared by first entry and link re-entry (same words, same order).
rep("""  forceAny();
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
""", """  forceAny();
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
""")

rep("""  if (xw || yw || zw) {
    writeBlock("G101", xw, yw, zw, f);
  } else if (f) {
    feedOutput.reset();
  }
}""", """  if (xw || yw || zw) {
    writeBlock("G101", xw, yw, zw, f);
  } else if (f) {
    feedOutput.reset();
  }
  lastPos = new Vector(x, y, z);
}""")

rep("""  routeOpen = false;
  pendingRadiusCompensation = -1;
  forceAny();

  writeComment(getParameter("operation-comment", ""));""", """  routeOpen = false;
  pendingRadiusCompensation = -1;
  linkBuffer = [];
  linkStart = undefined;
  linkDeferredComp = -1;
  lastPos = undefined;
  forceAny();

  writeComment(getParameter("operation-comment", ""));""")

rep("""function onRadiusCompensation() {
  pendingRadiusCompensation = radiusCompensation;
}

function onRapid(x, y, z) {""", """function onRadiusCompensation() {
  if (linkBuffer.length > 0) {
    linkDeferredComp = radiusCompensation; // applied after the buffered link is written
    return;
  }
  pendingRadiusCompensation = radiusCompensation;
}

function onRapid(x, y, z) {""")

rep("""    feed = 2000;
  }
  writeLinear(x, y, z, feed);
}

function onLinear(x, y, z, feed) {
  writeLinear(x, y, z, feed);
}""", """    feed = 2000;
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
}""")

rep("""    error(localize("Radius compensation cannot change on an arc."));
    return;
  }
  startRoute(x, y, z);""", """    error(localize("Radius compensation cannot change on an arc."));
    return;
  }
  flushLink(true);
  if (pendingRadiusCompensation >= 0) {
    error(localize("Radius compensation cannot change on an arc."));
    return;
  }
  startRoute(x, y, z);""")

rep("""    "R" + rFormat.format(getCircularRadius()),
    f
  );
}""", """    "R" + rFormat.format(getCircularRadius()),
    f
  );
  lastPos = new Vector(x, y, z);
}""")

rep("""function onComment(text) {
  writeComment(text);
}

function onPassThrough(text) {
  writeln(text);
}""", """function onComment(text) {
  flushLink(false);
  writeComment(text);
}

function onPassThrough(text) {
  flushLink(false);
  writeln(text);
}""")

rep("""function onDwell(seconds) {
}""", """function onDwell(seconds) {
  flushLink(false);
}""")

rep("""function onSectionEnd() {
  if (radiusCompensation""", """function onSectionEnd() {
  flushLink(false);
  if (radiusCompensation""")

rep("""function onClose() {
  writeln("%");
}""", """function onClose() {
  if (getProperty("linkViaHome")) {
    log("linkhome: " + linkStats.home + " links via G173 home, " + linkStats.stay + " stayed (time), " +
      linkStats.short + " stayed (short), " + linkStats.noTravel + " stayed (never above part top, or no travel after the retract), " + linkStats.endOfSection + " end-of-section kept");
  }
  writeln("%");
}""")
open(dst, 'w', encoding='utf-8', newline='').write(s)
print("ok", dst)
