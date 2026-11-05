use <pg.scad>
include <params.scad>
use <det.scad>
floor_t=2; wall_h=30; end_wall=6;
tx=-t_pl-0.2; Lx=2*t_pl+T_ring+0.4+22; zc=floor_t+H_axis;
module PIN(){ translate([0,0,zc]) rotate([0,90,0]) rotate([0,0,90]) translate([0,0,-t_pl]) plate(false); }
module POUT(){ translate([0,0,zc]) rotate([0,90,0]) rotate([0,0,90]) translate([0,0,T_ring+t_pl]) mirror([0,0,1]) plate(true); }
module RNG(){ translate([0,0,zc]) rotate([0,90,0]) rotate([0,0,90]) ring(); }
module BL(){ translate([tx-end_wall/2,9,floor_t+wall_h]) bracket(); }
module BLN(){ translate([tx-end_wall/2,9,floor_t+wall_h]) bracket_in(); }
module BR(){ translate([tx+Lx+end_wall/2,9,floor_t+wall_h]) bracket(); }
module TR(){ translate([tx,0,0]) tray(); }
w="old";
if(w=="old") intersection(){ PIN(); BL(); }
if(w=="new") intersection(){ PIN(); BLN(); }
if(w=="new_tray") intersection(){ TR(); BLN(); }
if(w=="out_pout") intersection(){ POUT(); BR(); }
if(w=="out_ring") intersection(){ RNG(); BR(); }
if(w=="out_tray") intersection(){ TR(); BR(); }
if(w=="new_ring") intersection(){ RNG(); BLN(); }
