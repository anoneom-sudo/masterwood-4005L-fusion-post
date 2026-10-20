description = "dump intermediate cnc";
vendor = "tmp";
certificationLevel = 2;
minimumRevision = 45917;
extension = "txt";
setCodePage("ascii");
capabilities = CAPABILITY_MILLING | CAPABILITY_MACHINE_SIMULATION;
function onOpen() {}
function onSection() {}
function onClose() {
  var p = getIntermediatePath();
  writeln("intermediate " + p);
  FileSystem.copyFile(p, "/tmp/lh/1009.cnc");
}
