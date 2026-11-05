use <pg.scad>
include <params.scad>
// ---------- 공통 ----------
step = 1; cu = 0;          // cu=1 이면 그 단계의 확대 그림
floor_t=2; wall_h=30; end_wall=6; tab_t=5;
z0 = gap+b+boss_h+0.1;
tx = -t_pl-0.2; Lx = 2*t_pl+T_ring+0.4+22; zc = floor_t+H_axis;
inX = gap+b-50; outX = z0+75;
OR="DarkOrange"; GR="Gainsboro"; ST="SlateGray"; RD="Red";
// 화살표: 점 p 에서 방향 d 로 길이 l
module arrow(p, d, l=20){ dd=d/norm(d);
  translate(p) rotate([0, acos(dd[2]), atan2(dd[1],dd[0])]) color(RD){ cylinder(d=1.6,h=l-5,$fn=12); translate([0,0,l-5]) cylinder(d1=4.5,d2=0,h=5,$fn=16);} }
// 회전 화살표 (축 z 둘레)
module rot_arrow(r=10, ang=280){ color(RD){ rotate_extrude(angle=ang,$fn=48) translate([r,0]) circle(d=1.6,$fn=10);
  rotate(ang) translate([r,0,0]) rotate([90,0,0]) cylinder(d1=4.5,d2=0,h=5,$fn=16);} }
// 구입품
module bearing(){ color(ST) difference(){ union(){ cylinder(d=10,h=2.4,$fn=48); translate([0,0,2.4]) cylinder(d=11.6,h=0.6,$fn=48);} translate([0,0,-1]) cylinder(d=6,h=5,$fn=32);} }
module nut(){ color(ST) difference(){ cylinder(d=6.2,h=2.4,$fn=6); translate([0,0,-1]) cylinder(d=3,h=5,$fn=16);} }
module bolt(l=38){ color("DimGray"){ cylinder(d=3,h=l,$fn=16); translate([0,0,-3]) cylinder(d=5.5,h=3,$fn=24);} }
module motor(){ // 축이 +x, 기어박스 Ø25×21 + 모터 Ø24.4×31 (총 52)
  rotate([0,-90,0]){ color("Goldenrod") cylinder(d=25,h=21,$fn=48);
    color("Silver") translate([0,0,21]) cylinder(d=24.4,h=31,$fn=48);
    color("Black") translate([0,0,52]) cylinder(d=20,h=2,$fn=40);
    color("Goldenrod") for(s=[-1,1]) translate([s*5,0,54]) cube([1,3,4],center=true);
    color(ST) translate([0,0,-10]) difference(){ cylinder(d=4,h=10,$fn=24); translate([1.5,-3,-1]) cube([3,6,12]);} } }
module coupling(){ color("DimGray") rotate([0,90,0]) difference(){ cylinder(d=12,h=25,$fn=40); for(z=[5,20]) translate([0,0,z]) rotate([90,0,0]) cylinder(d=2.5,h=20,center=true,$fn=12);} }
module tie(){ color("Black") rotate([0,90,0]) difference(){ cylinder(d=28.5,h=3.5,$fn=48); translate([0,0,-1]) cylinder(d=25.5,h=6,$fn=48);} }
module hall(){ color("Black") translate([-0.75,-2,-1.5]) cube([1.5,4,3]); color("Silver") for(i=[-1,0,1]) translate([0,i*1.27,0]) rotate([-90,0,0]) cylinder(d=0.45,h=11,$fn=8); }
module tsens(){ color("Silver") cylinder(d=6,h=45,$fn=24); color("Black") translate([0,0,45]) cylinder(d=3.5,h=25,$fn=16); }
module magnet(){ color("DimGray") cylinder(d=6,h=3,$fn=32); }
module syringe(){ color("White",0.8) cylinder(d=16,h=60,$fn=32); color("White") translate([0,0,60]) cylinder(d=3,h=25,$fn=12); color("White") translate([0,0,85]) cylinder(d=20,h=2,$fn=32); color("White") translate([0,0,-12]) cylinder(d1=2,d2=6,h=12,$fn=16); color("DodgerBlue",0.6) translate([0,0,1]) cylinder(d=14.5,h=30,$fn=32); }
// ---------- 프레임 A: 축 세로(출력측판이 아래) ----------
module FA(){ rotate([180,0,0]) children(); }
module P_in(){ translate([0,0,-t_pl]) render() plate(false); }
module P_out(){ translate([0,0,T_ring+t_pl]) mirror([0,0,1]) render() plate(true); }
module B_out(){ translate([0,0,T_ring+cb_h+brg_w]) mirror([0,0,1]) bearing(); }
module B_in(){ translate([0,0,-cb_h-brg_w]) bearing(); }
module SUN(){ translate([0,0,gap+b]) mirror([0,0,1]) render() sun(); }
module SH_in(){ color(ST) translate([0,0,inX]) cylinder(d=6,h=50,$fn=32); }
module SH_out(){ color(ST) translate([0,0,z0]) cylinder(d=6,h=75,$fn=32); }
module CAR(){ translate([0,0,z0+t_car]) mirror([0,0,1]) render() carrier(); }
module HUB(){ translate([0,0,z0]) render() hub(); }
module PL(){ for(i=[0:2]) rotate(i*120) translate([a,0,gap]) rotate(180/zp) render() planet(i+1); }
module RING(){ render() ring(); }
module BOLTS(){ for(x=[-1,1],y=[-1,1]) translate([x*bolt_xy,y*bolt_xy,-t_pl]) mirror([0,0,1]) mirror([0,0,1]) bolt(35); }
module NUTS(){ for(x=[-1,1],y=[-1,1]) translate([x*bolt_xy,y*bolt_xy,T_ring+t_pl-2.4]) nut(); }
// ---------- 프레임 B: 트레이 (축 = x) ----------
module GB(){ translate([0,0,zc]) rotate([0,90,0]) rotate([0,0,90]) { P_in(); RING(); P_out(); SH_in(); SH_out(); BOLTS(); NUTS(); } }
module TRAY(){ translate([tx,0,0]) render() tray(); }
lc=[-80,0,tab_t]; rc=[115,0,tab_t];
module CR(){ translate(lc) render() cradle(); translate(rc) render() cradle(); }
module SCR(){ for(p=[lc,rc]) for(dx=[-5,5]) color(ST) translate(p+[dx,0,6]) cylinder(d=3,h=10,$fn=12); }
module MOT(){ translate([inX-15+5,0,zc]) mirror([1,0,0]) translate([0,0,0]) rotate([0,0,180]) mirror([1,0,0]) motor_in(); translate([outX+15-5,0,zc]) motor_out(); }
module motor_in(){ mirror([1,0,0]) motor(); }   // 축이 +x(기어박스 쪽)
module motor_out(){ mirror([1,0,0]) motor(); }
module MOT2(){ translate([-56,0,zc]) motor(); translate([outX+16.6,0,zc]) mirror([1,0,0]) motor(); }
module TIES(){ for(p=[lc,rc]) for(dx=[-8,8]) translate([p[0]+dx-1.75,0,zc]) tie(); }
module CPL(){ translate([inX-15,0,zc]) coupling(); translate([outX-10,0,zc]) coupling(); }
encL = tx-end_wall+0.5; encR = tx+Lx+0.5;
module ENC(){ translate([encL,0,zc]) rotate([0,90,0]) render() encoder(); translate([encR,0,zc]) rotate([0,90,0]) render() encoder(); }
module MAG(){ translate([encL+5-3,9,zc]) rotate([0,90,0]) magnet(); translate([encR+5-3,9,zc]) rotate([0,90,0]) magnet(); }
// 입력측 브래킷은 몸체를 바깥으로 4 mm 옮긴 수정판
module bracket_in(){ difference(){ union(){ translate([-11,-15,0]) cube([14,30,4]); translate([-11,11,0]) cube([14,4,30]); }
  hull() for (y=[-10, 2]) translate([0,y,-1]) cylinder(d=3.4, h=6);
  hull() for (z=[8, 26]) translate([-4,10,z]) rotate([-90,0,0]) cylinder(d=3.4, h=6); } }
module BRK(){ translate([tx-end_wall/2,9,floor_t+wall_h]) render() bracket_in(); translate([tx+Lx+end_wall/2,9,floor_t+wall_h]) render() bracket(); }
module HALL(){ translate([encL-2.5,9,zc]) rotate([0,0,0]) hall(); translate([encR+5+2.5,9,zc]) hall(); }
module TS(){ translate([tx+Lx-6,32,floor_t+4]) tsens(); }
module OIL(){ color("DodgerBlue",0.5) translate([tx,-(S+0.6)/2,floor_t]) cube([Lx,S+0.6,15]); }
module baseB(n){ // n 단계까지 끝난 상태
  color(GR) TRAY(); color("Silver") GB();
  if(n>=14){ color(GR) CR(); SCR(); }
  if(n>=15){ MOT2(); TIES(); }
  if(n>=16) CPL();
  if(n>=17){ color(GR) ENC(); MAG(); }
  if(n>=18){ color(GR) BRK(); HALL(); }
  if(n>=19) TS();
  if(n>=20) OIL();
}
// ---------- 단계 ----------
if (cu==0) {
 if(step==1){ color(GR) render() plate(true); color(OR) translate([0,0,30]) bearing(); arrow([0,0,27],[0,0,-1],20); }
 if(step==2){ color(GR) render() plate(false); color(OR) translate([0,0,30]) bearing(); arrow([0,0,27],[0,0,-1],20); }
 if(step==3){ FA(){ color(GR) SUN(); color(OR) translate([0,0,-45]) SH_in(); } arrow([10,0,95],[0,0,-1],25); }
 if(step==4){ FA(){ color(GR) CAR(); color(OR) translate([0,0,45]) { HUB(); SH_out(); } } arrow([12,0,-60],[0,0,1],25); }
 if(step==5){ FA(){ color(GR){ CAR(); HUB(); } SH_out(); color(OR) translate([0,0,-30]) PL(); } for(i=[0:2]) rotate(-i*120) arrow([a,0,28],[0,0,-1],18); }
 if(step==6){ FA(){ color(GR) P_out(); B_out(); color(OR) translate([0,0,-40]) RING(); } arrow([60,0,42],[0,0,-1],25); }
 if(step==7){ FA(){ color(GR){ P_out(); RING(); } B_out(); color(OR) translate([0,0,-40]){ CAR(); HUB(); PL(); SH_out(); } } arrow([0,0,62],[0,0,-1],22); }
 if(step==8){ FA(){ color(GR){ P_out(); RING(); CAR(); HUB(); PL(); } B_out(); SH_out(); color(OR) translate([0,0,-35]) { SUN(); SH_in(); } } arrow([12,0,75],[0,0,-1],22); }
 if(step==9){ FA(){ color(GR){ P_out(); RING(); CAR(); HUB(); PL(); SUN(); } B_out(); SH_out(); SH_in(); color(OR) translate([0,0,-35]) { P_in(); } translate([0,0,-35]) B_in(); } arrow([30,0,55],[0,0,-1],22); }
 if(step==10){ FA(){ color(GR){ P_out(); RING(); P_in(); } B_out(); B_in(); SH_out(); SH_in(); translate([0,0,-30]) BOLTS(); } for(x=[-1,1],y=[-1,1]) arrow([x*bolt_xy,-y*bolt_xy,62],[0,0,-1],15); }
 if(step==11){ color(GR){ P_out(); RING(); P_in(); } B_out(); SH_out(); SH_in(); BOLTS(); translate([0,0,20]) NUTS(); for(x=[-1,1],y=[-1,1]) arrow([x*bolt_xy,y*bolt_xy,T_ring+t_pl+30],[0,0,-1],12); }
 if(step==12){ FA(){ color(GR){ P_out(); RING(); P_in(); } B_out(); B_in(); SH_out(); SH_in(); BOLTS(); NUTS(); } translate([0,0,30]) rot_arrow(9,300); translate([0,0,-70]) rot_arrow(9,75); }
 if(step==13){ color(GR) TRAY(); color(OR) translate([0,0,45]) GB(); arrow([12,-60,105],[0,0,-1],25); }
 if(step==14){ baseB(13); color(OR) translate([0,0,25]){ CR(); SCR(); } for(p=[lc,rc]) arrow(p+[0,-28,60],[0,0,-1],18); }
 if(step==15){ baseB(14); translate([0,0,30]) MOT2(); TIES(); for(p=[lc,rc]) arrow(p+[0,-25,85],[0,0,-1],18); }
 if(step==16){ baseB(15); color(OR) CPL(); arrow([inX-45,-20,zc],[1,0,0],18); arrow([outX+35,-20,zc],[-1,0,0],18); }
 if(step==17){ baseB(16); color(OR){ ENC(); } MAG(); }
 if(step==18){ baseB(17); color(OR) translate([0,0,20]) BRK(); HALL(); arrow([tx-end_wall/2,40,75],[0,0,-1],18); arrow([tx+Lx+end_wall/2,40,75],[0,0,-1],18); }
 if(step==19){ baseB(18); color(OR) translate([0,0,30]) TS(); arrow([tx+Lx-6,45,110],[0,0,-1],18); }
 if(step==20){ baseB(19); OIL(); translate([tx+Lx-12,-25,45]) syringe(); }
 if(step==21){ baseB(20); }
} else {
 // ---------- 확대 그림 ----------
 if(step==1||step==2) intersection(){ union(){ color(GR) render() plate(step==1); translate([0,0,1.5]) bearing(); } translate([-16,-20,-1]) cube([32,20,12]); }
 if(step==3) intersection(){ FA(){ color(GR) SUN(); SH_in(); } translate([-15,-15,-2]) cube([30,15,30]); }
 if(step==4) intersection(){ FA(){ color(GR){ CAR(); HUB(); } SH_out(); } translate([-15,-15,-12]) cube([30,15,30]); }
 if(step==5) color(OR) render() planet(2);
 if(step==6) intersection(){ FA(){ color(GR) P_out(); color(OR) RING(); } translate([-36,-46,-27]) cube([12,18,20]); }
 if(step==11) intersection(){ color(GR) P_out(); BOLTS(); NUTS(); translate([bolt_xy-8,bolt_xy-8,T_ring]) cube([16,8,12]); }
 if(step==15) intersection(){ union(){ color(GR) translate(lc) render() cradle(); MOT2(); TIES(); } translate([lc[0]-20,-20,0]) cube([40,20,70]); }
 if(step==17) { color(OR) render() encoder(); translate([9,0,8]) magnet(); arrow([9,0,20],[0,0,-1],10); }
 if(step==18) intersection(){ union(){ color(GR) ENC(); MAG(); HALL(); color(GR) BRK(); } translate([encL-12,-2,zc-10]) cube([24,30,22]); }
 if(step==20) intersection(){ color(GR) TRAY(); translate([tx+Lx-3,10,0]) cube([6,30,25]); }
}
