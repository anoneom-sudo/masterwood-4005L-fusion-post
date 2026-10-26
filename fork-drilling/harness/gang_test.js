#!/usr/bin/env node
"use strict";

// Headless gang-drilling checks. No Fusion post engine.
// Evaluates the pure block inside masterwood_4005L_drill.cps, posts fixture
// patterns, and compares them with the shop side-panel stroke list.

var fs = require("fs");
var path = require("path");

var HERE = __dirname;
var ROOT = path.resolve(HERE, "..", "..");
var CPS = path.resolve(HERE, "..", "masterwood_4005L_drill.cps");
var TLF = path.resolve(ROOT, "samples", "zijkant-links", "1 2 Zijkant Links.tlf");
var EXPECTED = path.resolve(HERE, "expected");
var OUT = path.resolve(HERE, "out");

var src = fs.readFileSync(CPS, "utf8");
var begin = src.indexOf("// >>> GANG-PURE-BEGIN");
var end = src.indexOf("// >>> GANG-PURE-END");
if (begin < 0 || end < begin) {
  throw new Error("gang pure block markers missing in the drill post");
}
var pure = src.slice(begin, end);
// Strict-mode eval cannot see function declarations from the post block.
var api = new Function(
  pure +
    "\nreturn {" +
    "\n  createGangPlanner: createGangPlanner," +
    "\n  planGangStrokes: planGangStrokes," +
    "\n  renderBoringLines: renderBoringLines," +
    "\n  boringDiameterMm: boringDiameterMm" +
    "\n};"
)();
var createGangPlanner = api.createGangPlanner;
var planGangStrokes = api.planGangStrokes;
var renderBoringLines = api.renderBoringLines;
var boringDiameterMm = api.boringDiameterMm;

var failures = 0;
function check(name, ok, detail) {
  if (ok) {
    console.log("ok  " + name);
  } else {
    failures++;
    console.log("FAIL " + name + (detail ? "\n" + detail : ""));
  }
}

function planner() {
  return createGangPlanner({
    pitch: 32,
    stations: [2, 3, 4, 5, 6],
    tol: 0.01,
    maxGroups: 3
  });
}

function fmtOf(over) {
  var fmt = {
    gangEnabled: true,
    ySign: 1,
    useY911: false,
    dy: 0,
    dx: 0
  };
  var k;
  for (k in over) {
    fmt[k] = over[k];
  }
  return fmt;
}

function holesOnRow(xs, y, station, z, f) {
  var out = [];
  var i;
  for (i = 0; i < xs.length; ++i) {
    out.push({x: xs[i], y: y, z: z == null ? 13 : z, f: f == null ? 2 : f, station: station || 2});
  }
  return out;
}

function xsFrom(start, count) {
  var xs = [];
  var i;
  for (i = 0; i < count; ++i) {
    xs.push(start + 32 * i);
  }
  return xs;
}

function g100s(lines) {
  var out = [];
  var i;
  for (i = 0; i < lines.length; ++i) {
    if (lines[i].indexOf("G100 ") === 0) out.push(lines[i]);
  }
  return out;
}

function groups(lines) {
  var out = [];
  var i;
  for (i = 0; i < lines.length; ++i) {
    if (/^#[TXSY]8\d=/.test(lines[i])) out.push(lines[i]);
  }
  return out;
}

function post(holes, fmt, plan) {
  plan = plan || planner();
  var result = planGangStrokes(plan, holes, fmt);
  return {plan: plan, result: result, lines: renderBoringLines(result, fmt)};
}

function linBlocks(text) {
  var rows = text.split(/\r?\n/);
  var lins = [];
  var i = 0;
  while (i < rows.length) {
    if (rows[i].trim() !== "LIN") {
      i++;
      continue;
    }
    var block = {};
    i++;
    while (i < rows.length && rows[i].trim() !== "\\LIN") {
      var key = rows[i].trim();
      if ((key === "X1" || key === "Y1" || key === "X2" || key === "Y2") && i + 1 < rows.length) {
        block[key] = parseFloat(rows[i + 1]);
      }
      i++;
    }
    lins.push(block);
  }
  return lins;
}

function zijkantHoles(lins, dy) {
  // TLF Y is the program Y written by the shop CAD. Fusion Y is the flipped
  // value the routing post already uses: program Y = DY - Fusion Y.
  var holes = [];
  var i;
  for (i = 0; i < lins.length; ++i) {
    var ln = lins[i];
    var x;
    for (x = ln.X1; x <= ln.X2 + 1e-6; x += 32) {
      holes.push({x: x, y: dy - ln.Y1, z: 13, f: 2, station: 2});
    }
  }
  return holes;
}

function resolveProgram(lines, dy) {
  var last = null;
  var out = [];
  var i;
  for (i = 0; i < lines.length; ++i) {
    var set = lines[i].match(/^#902=#911-\(([-0-9.]+)\)$/);
    if (set) {
      last = dy - parseFloat(set[1]);
      continue;
    }
    var g = lines[i].match(/^G100 X([-0-9.]+) Y=#902 Z([-0-9.]+) F([-0-9.]+) T(\d+)$/);
    if (g) {
      out.push({
        x: parseFloat(g[1]),
        y: last,
        z: parseFloat(g[2]),
        f: parseFloat(g[3]),
        t: parseInt(g[4], 10)
      });
      last = null;
    }
  }
  return out;
}

function expandHoles(lines, dy) {
  var tables = {};
  var holes = [];
  var last = null;
  var i;
  for (i = 0; i < lines.length; ++i) {
    var tab = lines[i].match(/^#([TXYS])(8\d)=([0-9,]+)$/);
    if (tab) {
      var n = parseInt(tab[2], 10);
      if (!tables[n]) tables[n] = {};
      tables[n][tab[1]] = tab[3].split(",").map(function(s) { return parseInt(s, 10); });
      continue;
    }
    var set = lines[i].match(/^#902=#911-\(([-0-9.]+)\)$/);
    if (set) {
      last = dy - parseFloat(set[1]);
      continue;
    }
    var abs = lines[i].match(/^G100 X([-0-9.]+) Y([-0-9.]+) Z([-0-9.]+) F([-0-9.]+) T(\d+)$/);
    var rel = lines[i].match(/^G100 X([-0-9.]+) Y=#902 Z([-0-9.]+) F([-0-9.]+) T(\d+)$/);
    var g = rel || abs;
    if (!g) continue;
    var x = parseFloat(g[1]);
    var y = rel ? last : parseFloat(g[2]);
    var z = parseFloat(rel ? g[2] : g[3]);
    var t = parseInt(rel ? g[4] : g[5], 10);
    if (t >= 81) {
      var list = tables[t].T;
      var s;
      for (s = 0; s < list.length; ++s) {
        holes.push([x + 32 * (list[s] - list[0]), y, z]);
      }
    } else {
      holes.push([x, y, z]);
    }
    last = null;
  }
  holes.sort(function(a, b) {
    if (a[1] !== b[1]) return a[1] - b[1];
    return a[0] - b[0];
  });
  return holes;
}

function samePoints(a, b) {
  if (a.length !== b.length) return false;
  var i;
  for (i = 0; i < a.length; ++i) {
    if (Math.abs(a[i][0] - b[i][0]) > 1e-6) return false;
    if (Math.abs(a[i][1] - b[i][1]) > 1e-6) return false;
    if (Math.abs(a[i][2] - b[i][2]) > 1e-6) return false;
  }
  return true;
}

function wrapProgram(name, dx, dy, dz, body) {
  var head = [
    "%",
    "|1 " + name,
    "|2 0",
    "|3 1",
    "|4 " + dx,
    "|5 " + dz,
    "|6 " + dy,
    "|7 0 0 0 0",
    "|8 0",
    "|9 4000",
    "|10 ",
    "|11 1",
    "|12 ",
    "|13 ",
    "|14 ",
    "|44 0",
    ":1",
    "G120 K1",
    "#910=DX",
    "#911=DY",
    "M61 K0 D1"
  ];
  return head.concat(body).concat(["%"]).join("\n") + "\n";
}

function writeExpected(name, text) {
  var file = path.join(EXPECTED, name);
  if (!fs.existsSync(file)) {
    fs.writeFileSync(file, text);
    console.log("wrote " + path.relative(ROOT, file));
    return;
  }
  var prev = fs.readFileSync(file, "utf8");
  check(name + " matches expected", prev === text, prev === text ? "" : "see " + file);
}

// --- shop side panel 2445 x 561 x 18 ---------------------------------------

var DY = 561;
var lins = linBlocks(fs.readFileSync(TLF, "utf8"));
var shelf = zijkantHoles(lins, DY);
check("TLF shelf lines", lins.length === 8, "got " + lins.length);
check("TLF shelf holes", shelf.length === 122, "got " + shelf.length);

var zFmt = fmtOf({useY911: true, dy: DY, dx: 2445});
var zPlan = planner();
var zPost = post(shelf, zFmt, zPlan);
var zLines = zPost.lines;

var wantGroups = [
  "#T81=2,3,4,5,6",
  "#X81=6,5,4,3,2",
  "#S81=6,5,4,3,2",
  "#T82=2,5,6",
  "#X82=6,3,2",
  "#S82=6,3,2",
  "#T83=2,3,4",
  "#X83=6,5,4",
  "#S83=6,5,4"
];
check("zijkant group tables", groups(zLines).join("\n") === wantGroups.join("\n"), groups(zLines).join("\n"));

// Stroke list read from the shop program 1 2 Zijkant Links.PRG (not committed).
var strokeX = [173, 333, 493, 717, 877, 1037, 1197, 1357, 1517, 1677, 1837, 1997, 2157];
var strokeT = [81, 81, 81, 81, 81, 81, 82, 81, 81, 83, 81, 81, 81];
var wantStrokes = [];
var i;
for (i = 0; i < strokeX.length; ++i) wantStrokes.push({x: strokeX[i], y: 36, t: strokeT[i]});
for (i = strokeX.length - 1; i >= 0; --i) wantStrokes.push({x: strokeX[i], y: 525, t: strokeT[i]});

var gotStrokes = resolveProgram(zLines, DY);
var strokeDetail = [];
var strokesOk = gotStrokes.length === wantStrokes.length;
for (i = 0; i < Math.min(gotStrokes.length, wantStrokes.length); ++i) {
  if (gotStrokes[i].x !== wantStrokes[i].x || gotStrokes[i].y !== wantStrokes[i].y || gotStrokes[i].t !== wantStrokes[i].t || gotStrokes[i].z !== 13 || gotStrokes[i].f !== 2) {
    strokesOk = false;
    strokeDetail.push("at " + i + " got " + JSON.stringify(gotStrokes[i]) + " want " + JSON.stringify(wantStrokes[i]));
  }
}
check("zijkant 26 strokes, serpentine, T81/T82/T83", strokesOk, strokeDetail.slice(0, 8).join("\n"));
check("zijkant no warnings", zPost.result.warnings.length === 0, zPost.result.warnings.join("\n"));

var tlfPoints = [];
for (i = 0; i < lins.length; ++i) {
  var x;
  for (x = lins[i].X1; x <= lins[i].X2 + 1e-6; x += 32) {
    tlfPoints.push([x, lins[i].Y1, 13]);
  }
}
tlfPoints.sort(function(a, b) { return a[1] - b[1] || a[0] - b[0]; });
check("expanded gang holes equal the TLF", samePoints(expandHoles(zLines, DY), tlfPoints));

var again = post(shelf, zFmt, zPlan);
check("second op reuses groups", again.result.newGroups.length === 0 && groups(again.lines).length === 0, "new " + again.result.newGroups.length);

var singlePlan = planner();
var singleFmt = fmtOf({gangEnabled: false, useY911: true, dy: DY, dx: 2445});
var singleAll = post(shelf, singleFmt, singlePlan);
check("gang off is one G100 per hole", g100s(singleAll.lines).length === 122 && groups(singleAll.lines).length === 0);
check("gang off still covers the TLF holes", samePoints(expandHoles(singleAll.lines, DY), tlfPoints));
check("gang off uses station 2", g100s(singleAll.lines).every(function(line) { return / T2$/.test(line); }));

// --- smaller patterns ------------------------------------------------------

var fifteen = post(holesOnRow(xsFrom(136, 15), 37), fmtOf({}));
check("15 holes are 3 x T81", g100s(fifteen.lines).length === 3 && groups(fifteen.lines).indexOf("#T82=2,3") < 0 && g100s(fifteen.lines).every(function(line) { return / T81$/.test(line); }));

var seventeen = post(holesOnRow(xsFrom(136, 17), 37), fmtOf({useY911: true, dy: 560, dx: 720}));
check("17 holes are 3 x T81 + T82=2,3",
  groups(seventeen.lines).indexOf("#T82=2,3") >= 0 &&
  groups(seventeen.lines).indexOf("#X82=6,5") >= 0 &&
  g100s(seventeen.lines).map(function(line) { return line.split(" ").pop(); }).join(",") === "T81,T81,T81,T82");

var off = post(holesOnRow([100, 132, 164, 196, 228, 150], 10), fmtOf({}));
check("off-pitch hole stays single",
  g100s(off.lines).length === 2 &&
  / T81$/.test(g100s(off.lines)[0]) &&
  /X150 Y10 Z13 F2 T2$/.test(g100s(off.lines)[1]) &&
  off.result.warnings.length === 1);

var mixed = post(
  holesOnRow(xsFrom(0, 5), 0, 2, 13, 2).concat(holesOnRow(xsFrom(0, 5), 0, 2, 20, 2)),
  fmtOf({})
);
check("mixed depths are two strokes", g100s(mixed.lines).length === 2 && /Z13 /.test(g100s(mixed.lines)[0]) && /Z20 /.test(g100s(mixed.lines)[1]));

var column = post(holesOnRow([10, 10, 10, 10, 10], 0).map(function(h, n) { h.y = n * 32; return h; }), fmtOf({}));
check("a Y column is not an X gang", groups(column.lines).length === 0 && g100s(column.lines).length === 5);

var dowel = post(
  holesOnRow(xsFrom(0, 5), 0).concat([{x: 9, y: 0, z: 13, f: 2, station: 9}]),
  fmtOf({})
);
check("station 9 stays a single T9", g100s(dowel.lines).some(function(line) { return / T9$/.test(line); }) && g100s(dowel.lines).some(function(line) { return / T81$/.test(line); }));

var many = planner();
var manyHoles = [];
// Four different subsets on four rows. The fourth must fall back to singles.
manyHoles = manyHoles.concat(holesOnRow(xsFrom(0, 5), 0));
manyHoles = manyHoles.concat(holesOnRow([0, 32], 100));
manyHoles = manyHoles.concat(holesOnRow([0, 64], 200));
manyHoles = manyHoles.concat(holesOnRow([0, 96], 300));
var limited = post(manyHoles, fmtOf({}), many);
check("fourth subset falls back to single G100",
  limited.result.warnings.some(function(w) { return w.indexOf("spindle groups") >= 0; }) &&
  groups(limited.lines).indexOf("#T81=2,3,4,5,6") >= 0 &&
  groups(limited.lines).indexOf("#T82=2,3") >= 0 &&
  groups(limited.lines).indexOf("#T83=2,4") >= 0 &&
  groups(limited.lines).length === 9 &&
  g100s(limited.lines).filter(function(line) { return / T2$/.test(line); }).length === 2);

check("diameter table", boringDiameterMm(2) === 5 && boringDiameterMm(7) === 0 && boringDiameterMm(12) === 35 && boringDiameterMm(9) === 8);

// --- programs the checker can read -----------------------------------------

fs.mkdirSync(OUT, {recursive: true});
fs.mkdirSync(EXPECTED, {recursive: true});

var zPrg = wrapProgram("zijkant-links", 2445, 561, 18, zLines);
fs.writeFileSync(path.join(OUT, "zijkant-links-2445x561x18.prg"), zPrg);
writeExpected("zijkant-links-2445x561x18.prg", zPrg);

var b2 = seventeen.lines;
var b2Prg = wrapProgram("b2-subset", 720, 560, 18, b2);
fs.writeFileSync(path.join(OUT, "b2-17.prg"), b2Prg);
writeExpected("b2-17.prg", b2Prg);

var five = post(holesOnRow(xsFrom(136, 5), 37).concat([{x: 9, y: 280, z: 13, f: 2, station: 9}]), fmtOf({gangEnabled: false, useY911: true, dy: 560, dx: 720}));
var fivePrg = wrapProgram("single-fallback", 720, 560, 18, five.lines);
fs.writeFileSync(path.join(OUT, "single-fallback.prg"), fivePrg);
writeExpected("single-fallback.prg", fivePrg);
check("single fallback has no gang table", groups(five.lines).length === 0 && g100s(five.lines).length === 6);

// Side panel from harness/README.md Option B, Fusion coordinates.
function sidePanelHoles() {
  var holes = [];
  var ys = [37, 523];
  var yi, xi;
  for (yi = 0; yi < ys.length; ++yi) {
    var xs = xsFrom(136, 15);
    for (xi = 0; xi < xs.length; ++xi) holes.push({x: xs[xi], y: ys[yi], z: 13, f: 2, station: 2});
  }
  var dowelX = [9, 711];
  var dowelY = [37, 280, 523];
  for (yi = 0; yi < dowelY.length; ++yi) {
    for (xi = 0; xi < dowelX.length; ++xi) {
      holes.push({x: dowelX[xi], y: dowelY[yi], z: 13, f: 2, station: 9});
    }
  }
  holes.push({x: 360, y: 280, z: 13, f: 0.5, station: 12});
  return holes;
}
var side = post(sidePanelHoles(), fmtOf({useY911: true, dy: 560, dx: 720}));
var sidePrg = wrapProgram("side-panel", 720, 560, 18, side.lines);
fs.writeFileSync(path.join(OUT, "side-panel-720x560x18.prg"), sidePrg);
writeExpected("side-panel-720x560x18.prg", sidePrg);
check("side panel groups the shelf rows only",
  groups(side.lines).join("\n") === ["#T81=2,3,4,5,6", "#X81=6,5,4,3,2", "#S81=6,5,4,3,2"].join("\n") &&
  g100s(side.lines).filter(function(line) { return / T81$/.test(line); }).length === 6 &&
  g100s(side.lines).filter(function(line) { return / T9$/.test(line); }).length === 6 &&
  g100s(side.lines).filter(function(line) { return / T12$/.test(line); }).length === 1);

if (failures) {
  console.log(failures + " failed");
  process.exit(1);
}
console.log("gang tests passed");
