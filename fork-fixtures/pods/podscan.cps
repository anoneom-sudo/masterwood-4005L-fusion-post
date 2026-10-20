/* podscan.cps - fork-fixtures: dump toolpath geometry for the pod placer (NOT a machine post).
   One JSON object per line: {"t":"wp",...} workpiece box, {"t":"sec",...} per section, {"t":"m",...} per move.
   Arcs are linearised (allowedCircularPlanes = 0). Coordinates: section (work plane) frame + frame data to go global (WCS). */
description = "fork-fixtures pod scan (JSON dump, not for the mill)";
vendor = "fork-fixtures";
certificationLevel = 2;
minimumRevision = 45917;
extension = "jsonl";
setCodePage("ascii");
capabilities = CAPABILITY_MILLING;
tolerance = spatial(0.05, MM);
allowHelicalMoves = false;
allowedCircularPlanes = 0;
allowSpiralMoves = false;
highFeedrate = 10000;
function f(v) { return Math.round(v * 1000) / 1000; }
function vec(v) { return [f(v.x), f(v.y), f(v.z)]; }
function onOpen() {
  var wp = getWorkpiece();
  writeln(JSON.stringify({t: "wp", lo: vec(wp.lower), hi: vec(wp.upper), unit: unit == MM ? "mm" : "in"}));
}
function onSection() {
  var s = currentSection, w = s.workPlane, o = s.workOrigin;
  var d = {t: "sec", i: getCurrentSectionId(), op: s.hasParameter("operation-comment") ? s.getParameter("operation-comment") : "",
    right: vec(w.right), up: vec(w.up), fwd: vec(w.forward), org: vec(o),
    D: f(tool.diameter), CR: f(tool.cornerRadius), flute: f(tool.fluteLength), body: f(tool.bodyLength), shoulder: f(tool.shoulderLength),
    taper: f(tool.taperAngle), multi: s.isMultiAxis()};
  try { d.g0 = vec(s.getGlobalPosition(new Vector(0, 0, 0))); d.g1 = vec(s.getGlobalPosition(new Vector(1, 2, 3))); } catch (e) { d.gerr = "" + e; }
  try { d.holderD = f(tool.holderDiameter); d.holderL = f(tool.holderLength); } catch (e) {}
  writeln(JSON.stringify(d));
}
function mv(k, x, y, z) { writeln('{"t":"m","k":"' + k + '","p":[' + f(x) + "," + f(y) + "," + f(z) + "]}"); }
function onRapid(x, y, z) { mv("r", x, y, z); }
function onLinear(x, y, z, feed) { mv("l", x, y, z); }
function onRapid5D(x, y, z, a, b, c) { writeln('{"t":"m","k":"r5","p":[' + f(x) + "," + f(y) + "," + f(z) + '],"a":[' + f(a) + "," + f(b) + "," + f(c) + "]}"); }
function onLinear5D(x, y, z, a, b, c, feed) { writeln('{"t":"m","k":"l5","p":[' + f(x) + "," + f(y) + "," + f(z) + '],"a":[' + f(a) + "," + f(b) + "," + f(c) + "]}"); }
function onCircular(clockwise, cx, cy, cz, x, y, z, feed) { linearize(tolerance); }
function onCommand(c) {}
function onSectionEnd() {}
function onClose() {}
