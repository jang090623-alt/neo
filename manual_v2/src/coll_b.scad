use <det.scad>
include <params.scad>
zc=50; w="";
module BOLTS_B(){ translate([0,0,zc]) rotate([0,90,0]) rotate([0,0,90]) BOLTS(); }
module PLATES_B(){ translate([0,0,zc]) rotate([0,90,0]) rotate([0,0,90]) { P_in(); RING(); P_out(); } }
if(w=="bolt_tray") intersection(){ BOLTS_B(); TRAY(); }
if(w=="plates_tray") intersection(){ PLATES_B(); TRAY(); }
