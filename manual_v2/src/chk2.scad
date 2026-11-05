use <pg.scad>
include <params.scad>
use <det.scad>
floor_t=2; wall_h=30; end_wall=6;
tx=-t_pl-0.2; Lx=2*t_pl+T_ring+0.4+22; zc=floor_t+H_axis;
encL = tx-end_wall+0.5; encR = tx+Lx+0.5;
// 끝벽 나사 구멍(Ø2.5) 자리에 M3 나사(Ø3) 기둥
module SCREW(x,y){ translate([x,y,floor_t+wall_h-10]) cylinder(d=3,h=20,$fn=24); }
module BLN(c){ translate([tx-end_wall/2,c,floor_t+wall_h]) bracket_in(); }
module BR(c){ translate([tx+Lx+end_wall/2,c,floor_t+wall_h]) bracket(); }
module ENC(){ translate([encL,0,zc]) rotate([0,90,0]) encoder(); translate([encR,0,zc]) rotate([0,90,0]) encoder(); }
module MAG(){ translate([encL+5-3,9,zc]) rotate([0,90,0]) magnet(); translate([encR+5-3,9,zc]) rotate([0,90,0]) magnet(); }
module PIN(){ translate([0,0,zc]) rotate([0,90,0]) rotate([0,0,90]) translate([0,0,-t_pl]) plate(false); }
c=9; w="";
if(w=="scrL12") intersection(){ BLN(c); SCREW(tx-end_wall/2,12); }
if(w=="scrLm12") intersection(){ BLN(c); SCREW(tx-end_wall/2,-12); }
if(w=="scrR12") intersection(){ BR(c); SCREW(tx+Lx+end_wall/2,12); }
if(w=="scrRm12") intersection(){ BR(c); SCREW(tx+Lx+end_wall/2,-12); }
if(w=="magenc") intersection(){ ENC(); MAG(); }
if(w=="encpin") intersection(){ ENC(); PIN(); }
if(w=="brkenc") intersection(){ union(){BLN(c);BR(c);} ENC(); }
