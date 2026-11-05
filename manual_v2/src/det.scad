use <pg.scad>
include <params.scad>
// ---------- 공통 ----------
step = 1; cu = 0; th = ""; left_arrow = true;   // 기본 시점에서 왼쪽이 가려지는 그림은 false          // cu=1 이면 그 단계의 확대 그림
floor_t=2; wall_h=30; end_wall=6; tab_t=5;
z0 = gap+b+boss_h+0.1;
tx = -t_pl-0.2; Lx = 2*t_pl+T_ring+0.4+22; zc = floor_t+H_axis;
inX = gap+b-50; outX = z0+75;
OR="DarkOrange"; GR="Gainsboro"; ST="SlateGray"; RD="Red";
// 화살표: 점 p 에서 방향 d 로 길이 l
AS = (step>=13 && cu==0) ? 2.2 : 1;   // 트레이 장면은 그림이 작아지므로 화살표를 굵게
module arrow(p, d, l=20){ dd=d/norm(d); k=AS;
  translate(p) rotate([0, acos(dd[2]), atan2(dd[1],dd[0])]) color(RD){ cylinder(d=1.6*k,h=l-5*k,$fn=12); translate([0,0,l-5*k]) cylinder(d1=4.5*k,d2=0,h=5*k,$fn=16);} }
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
// m=-1: 모터(Ø4 축)가 -x 쪽, m=1: +x 쪽. 나머지 반은 Ø6 막대 구멍
module coupling(m=-1){ color("DimGray") rotate([0,90,0]) difference(){ cylinder(d=12,h=25,$fn=40); for(z=[5,20]) translate([0,0,z]) rotate([90,0,0]) cylinder(d=2.5,h=20,center=true,$fn=12);
  translate([0,0,m<0?-1:12.5]) cylinder(d=4,h=13.5,$fn=24); translate([0,0,m<0?12.5:-1]) cylinder(d=6,h=13.5,$fn=32);} }
module tie(){ color("Black") rotate([0,90,0]) difference(){ cylinder(d=28.5,h=3.5,$fn=48); translate([0,0,-1]) cylinder(d=25.5,h=6,$fn=48);} }
module hall(){ color("Black") translate([-0.75,-2,-1.5]) cube([1.5,4,3]); color("Silver") for(i=[-1,0,1]) translate([0,0,i*1.27]) rotate([-90,0,0]) cylinder(d=0.45,h=11,$fn=8); }
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
// M3 나사 (머리 Ø5.5×2, 몸통 Ø3×10): 머리가 위, 몸통이 아래로
module screw(){ color(ST){ cylinder(d=3,h=10,$fn=16); translate([0,0,10]) cylinder(d=5.5,h=2,$fn=24); } }
// 레일 구멍 x(트레이 기준 -71+5i, Lx+11+5i)를 받침 긴 구멍 안에서 고름: 왼쪽 -80.2, 오른쪽 113.4 (README 나사 4개 = 받침 1 + 브래킷 1, 양쪽)
module SCR(){ for(x=[tx-71, tx+Lx+11+55]) translate([x,0,tab_t+6-10]) screw(); }
module BSCR(){ for(x=[tx-end_wall/2, tx+Lx+end_wall/2]) translate([x,12,floor_t+wall_h+4-10]) screw(); }
module MOT(){ translate([inX-15+5,0,zc]) mirror([1,0,0]) translate([0,0,0]) rotate([0,0,180]) mirror([1,0,0]) motor_in(); translate([outX+15-5,0,zc]) motor_out(); }
module motor_in(){ mirror([1,0,0]) motor(); }   // 축이 +x(기어박스 쪽)
module motor_out(){ mirror([1,0,0]) motor(); }
module MOT2(d=0){ translate([-56-d,0,zc]) motor(); translate([outX+16.6+d,0,zc]) mirror([1,0,0]) motor(); }   // d: 바깥으로 민 거리
// 케이블타이: 모터 위를 감고 받침 바깥 옆면으로 내려와 통로(받침 바닥에서 28.5~30.7)를 지남
module tie2(){ color("Black") translate([-1.75,0,0]){ zt=tab_t+28.5+0.6;
  translate([0,0,zc]) rotate([0,90,0]) rotate([0,0,90]) rotate_extrude(angle=180,$fn=48) translate([12.5,0]) square([1,3.5]);
  for(s=[-1,1]){ translate([0,s>0?12.5:-21,zc]) cube([3.5,8.5,1]); translate([0,s>0?20:-21,zt]) cube([3.5,1,zc+1-zt]); }
  translate([0,-21,zt]) cube([3.5,42,1]); } }
module TIES(){ for(p=[lc,rc]) for(dx=[-8,8]) translate([p[0]+dx,0,0]) tie2(); }
module CPL(d=0){ translate([inX-15-d,0,zc]) coupling(-1); translate([outX-10+d,0,zc]) coupling(1); }
encL = tx-end_wall+0.5; encR = tx+Lx+0.5;
// 원판은 막대에 끼워 자유롭게 돌 수 있으므로, 자석 홈이 y=+9(홀센서 쪽)에 오고 홈이 바깥을 보게 돌려 놓음
module ENC(d=0){ translate([encL-d,0,zc]) rotate([90,0,0]) rotate([0,90,0]) translate([0,0,5]) rotate([180,0,0]) render() encoder(); translate([encR+d,0,zc]) rotate([90,0,0]) rotate([0,90,0]) render() encoder(); }
module MAG(d=0){ translate([encL-d,9,zc]) rotate([0,90,0]) magnet(); translate([encR+5-3+d,9,zc]) rotate([0,90,0]) magnet(); }
// 입력측 브래킷은 몸체를 바깥으로 4 mm 옮긴 수정판
module bracket_in(){ difference(){ union(){ translate([-11,-15,0]) cube([14,30,4]); translate([-11,11,0]) cube([14,4,30]); }
  hull() for (y=[-10, 2]) translate([0,y,-1]) cylinder(d=3.4, h=6);
  hull() for (z=[8, 26]) translate([-4,10,z]) rotate([-90,0,0]) cylinder(d=3.4, h=6); } }
brk_c = 10;  // 바닥 긴 구멍(y -10~2)이 끝벽 나사 구멍 y=+12에 걸리는 가장 안쪽 위치
module BRK_L(){ translate([tx-end_wall/2,brk_c,floor_t+wall_h]) bracket_in(); }
module BRK(){ translate([tx-end_wall/2,brk_c,floor_t+wall_h]) render() bracket_in(); translate([tx+Lx+end_wall/2,brk_c,floor_t+wall_h]) render() bracket(); }
hall_gap = 2.5;  // 홀센서 면 ~ 원판(자석) 면 간격 (README: 2~3 mm)
module HALL(){ translate([encL-hall_gap-0.75,9,zc]) hall(); translate([encR+5+hall_gap+0.75,9,zc]) hall(); }
module TS(){ translate([tx+Lx-6,32,floor_t+4]) tsens(); }
module OIL(){ color("DodgerBlue",0.5) translate([tx,-(S+0.6)/2,floor_t]) cube([Lx,S+0.6,15]); }
// 기어 상자(트레이 좌표). c: 출력 부품 색. 산 물건(막대·볼트·너트·베어링)은 항상 실제 색
module GBc(c=GR){ translate([0,0,zc]) rotate([0,90,0]) rotate([0,0,90]) {
  color(c){ P_in(); RING(); P_out(); CAR(); HUB(); PL(); SUN(); } B_in(); B_out(); SH_in(); SH_out(); BOLTS(); NUTS(); } }
module baseB(n){ // n 단계까지 끝난 상태 (15 자석 원판 → 16 모터 → 17 커플링 순서)
  color(GR) TRAY(); GBc(GR);
  if(n>=14){ color(GR) CR(); SCR(); }
  if(n>=15){ color(GR) ENC(); MAG(); }
  if(n>=16){ MOT2(); TIES(); }
  if(n>=17) CPL();
  if(n>=18){ color(GR) BRK(); HALL(); BSCR(); }
  if(n>=19) TS();
  if(n>=20) OIL();
}
// 단면: 부품 하나를 render() 한 뒤 상자로 잘라 색을 입힘 (children(0)=부품, children(1)=상자)
module sec(c){ color(c) render() intersection(){ children(0); children(1); } }
module INNER(){ CAR(); HUB(); PL(); SUN(); }
// ---------- 단계 ----------
if (cu==0) {
 if(step==1){ color(GR) render() plate(true); translate([0,0,30]) bearing(); arrow([0,0,27],[0,0,-1],20); }
 if(step==2){ color(GR) render() plate(false); translate([0,0,30]) bearing(); arrow([0,0,27],[0,0,-1],20); }
 if(step==3){ FA(){ color(GR) SUN(); translate([0,0,-45]) SH_in(); } arrow([10,0,95],[0,0,-1],25); }
 if(step==4){ FA(){ color(GR) CAR(); translate([0,0,45]) { color(OR) HUB(); SH_out(); } } arrow([14,0,-62],[0,0,1],25); }
 if(step==5){ FA(){ color(GR){ CAR(); HUB(); } SH_out(); color(OR) translate([0,0,-30]) PL(); } for(i=[0:2]) rotate(-i*120) arrow([a,0,17],[0,0,-1],14); }
 if(step==6){ FA(){ color(GR) P_out(); B_out(); color(OR) translate([0,0,-40]) RING(); } arrow([60,0,42],[0,0,-1],25); }
 if(step==7){ FA(){ color(GR){ P_out(); RING(); } B_out(); translate([0,0,-40]){ color(OR){ CAR(); HUB(); PL(); } SH_out(); } } arrow([0,0,64],[0,0,-1],22); }
 if(step==8){ FA(){ color(GR){ P_out(); RING(); CAR(); HUB(); PL(); } B_out(); SH_out(); translate([0,0,-35]) { color(OR) SUN(); SH_in(); } } arrow([12,0,75],[0,0,-1],22); }
 if(step==9){ FA(){ color(GR){ P_out(); RING(); INNER(); } B_out(); SH_out(); SH_in(); translate([0,0,-35]) { color(OR) P_in(); B_in(); } } arrow([30,0,57],[0,0,-1],22); }
 if(step==10){ FA(){ color(GR){ P_out(); RING(); P_in(); INNER(); } B_out(); B_in(); SH_out(); SH_in(); translate([0,0,-30]) BOLTS(); } for(x=[-1,1],y=[-1,1]) arrow([x*bolt_xy,-y*bolt_xy,62],[0,0,-1],15); }
 if(step==11){ color(GR){ P_out(); RING(); P_in(); INNER(); } B_out(); B_in(); SH_out(); SH_in(); BOLTS(); translate([0,0,20]) NUTS(); for(x=[-1,1],y=[-1,1]) arrow([x*bolt_xy,y*bolt_xy,T_ring+t_pl+30],[0,0,-1],12); }
 if(step==12){ FA(){ color(GR){ P_out(); RING(); P_in(); INNER(); } B_out(); B_in(); SH_out(); SH_in(); BOLTS(); NUTS(); } translate([0,0,30]) rot_arrow(9,300); translate([0,0,-70]) rot_arrow(9,75); }
 if(step==13){ color(GR) TRAY(); translate([0,0,45]) GBc(OR); arrow([12,-60,115],[0,0,-1],35); }
 if(step==14){ baseB(13); translate([0,0,25]){ color(OR) CR(); SCR(); } for(p=[lc,rc]) arrow(p+[0,-28,70],[0,0,-1],30); }
 if(step==15){ baseB(14); color(OR) ENC(40); MAG(40); arrow([encL-40-36,0,zc+20],[1,0,0],30); arrow([encR+45+36,0,zc+20],[-1,0,0],30); }
 if(step==16){ baseB(15); translate([0,0,30]) MOT2(); TIES(); for(p=[lc,rc]) arrow(p+[0,-25,100],[0,0,-1],30); }
 if(step==17){ baseB(16); MOT2(12); CPL(12); arrow([lc[0]-72,0,zc+20],[1,0,0],30); arrow([rc[0]+72,0,zc+20],[-1,0,0],30); }
 if(step==18){ baseB(17); translate([0,0,20]){ color(OR) BRK(); HALL(); } translate([0,0,40]) BSCR(); if(left_arrow) arrow([tx-end_wall/2,brk_c+30,100],[0,0,-1],30); arrow([tx+Lx+end_wall/2,brk_c+30,100],[0,0,-1],30); }
 if(step==19){ baseB(18); translate([0,0,30]) TS(); arrow([tx+Lx-6,45,130],[0,0,-1],30); }
 if(step==20){ baseB(19); OIL(); translate([tx+Lx-12,-25,45]) syringe(); }
 if(step==21){ baseB(20); }
} else if (cu==1) {
 // ---------- 확대 그림 (단면) ----------
 if(step==1||step==2){ bx=[-16,-20,-1]; sec(GR){ plate(step==1); translate(bx) cube([32,20,12]); } sec(ST){ translate([0,0,1.5]) bearing(); translate(bx) cube([32,20,12]); } }
 if(step==3){ FA(){ sec(GR){ SUN(); translate([-15,-15,-6]) cube([30,15,20]); } sec(ST){ SH_in(); translate([-15,-15,-6]) cube([30,15,20]); } } }
 if(step==4){ FA(){ sec(GR){ CAR(); translate([-11,-15,7]) cube([22,15,14]); } sec(GR){ HUB(); translate([-11,-15,7]) cube([22,15,14]); } sec(ST){ SH_out(); translate([-11,-15,7]) cube([22,15,14]); } } }
 if(step==5) color(OR) render() planet(2);
 if(step==6){ FA(){ sec(GR){ P_out(); translate([22,37,10]) cube([16,11,20]); } sec(OR){ RING(); translate([22,37,10]) cube([16,11,20]); } } }
 if(step==11){ bx=[bolt_xy-9,bolt_xy-9,T_ring+2]; sec(GR){ P_out(); translate(bx) cube([18,9,12]); } sec("DimGray"){ BOLTS(); translate(bx) cube([18,9,12]); } sec(ST){ NUTS(); translate(bx) cube([18,9,12]); } }
 if(step==16){ bx=[lc[0]-20,-25,0]; sec(GR){ translate(lc) cradle(); translate(bx) cube([28,50,75]); } sec("Silver"){ MOT2(); translate(bx) cube([28,50,75]); } sec("Black"){ TIES(); translate(bx) cube([28,50,75]); } }
 if(step==15){ color(OR) render() encoder(); translate([9,0,8]) magnet(); arrow([9,0,20],[0,0,-1],10); }
 if(step==18){ bx=[tx-end_wall-14,-16,floor_t+wall_h-6]; bs=[32,46,40];   // 입력측 센서 주변 (자르지 않은 입체, 상자 밖만 덜어냄)
   sec(GR){ TRAY(); translate(bx) cube(bs); } sec(GR){ GBc(GR); translate(bx) cube(bs); } sec(ST){ translate([0,0,zc]) rotate([0,90,0]) rotate([0,0,90]) SH_in(); translate(bx) cube(bs); }
   sec(GR){ ENC(); translate(bx) cube(bs); } sec("DimGray"){ MAG(); translate(bx) cube(bs); } sec("Black"){ HALL(); translate(bx) cube(bs); } color(GR) render() BRK_L();
   color(RD) translate([encL-hall_gap,8.6,zc+2]) cube([hall_gap,0.8,0.8]); }   // 빨간 막대 = 센서~원판 간격
 if(step==20){ bx=[tx+Lx-0.8,8,0];sec(GR){ TRAY(); translate(bx) cube([10,34,28]); }   // 온도센서 고리(x 끝 46.4)가 가리지 않게 벽 앞 0.8 mm만
   color(RD) for (h=[10,15,20]) translate([tx+Lx-0.01, 20, floor_t+h-0.3]) cube([0.5, h==15?16:8, 0.6]);   // 눈금 홈(설계 위치) 강조
   color("DodgerBlue",0.45) translate([tx+Lx-0.8,8,floor_t]) cube([0.8,34,15]); }
} else if (cu==2) {
 // 1단계 보조 그림: plate_out 을 뒤집은 모습(바깥면 육각 홈 4개)
 color(GR) rotate([180,0,0]) render() plate(true);
} else if (cu==3) {
 // 부품 썸네일: 출력 부품 = 주황, 산 물건 = 실제 색
 if(th=="plate_out") color(OR) render() plate(true);
 if(th=="plate_in") color(OR) render() plate(false);
 if(th=="sun") color(OR) render() sun();
 if(th=="planet") color(OR) render() planet(1);
 if(th=="carrier") color(OR) render() carrier();
 if(th=="hub") color(OR) render() hub();
 if(th=="ring") color(OR) render() ring();
 if(th=="tray") color(OR) render() tray();
 if(th=="cradle") color(OR) render() cradle();
 if(th=="encoder") color(OR) render() encoder();
 if(th=="bracket_in") color(OR) render() bracket_in();
 if(th=="bracket") color(OR) render() bracket();
 if(th=="bearing") bearing();
 if(th=="shaft50") color(ST) rotate([0,90,0]) cylinder(d=6,h=50,$fn=32);
 if(th=="shaft75") color(ST) rotate([0,90,0]) cylinder(d=6,h=75,$fn=32);
 if(th=="bolt") rotate([0,90,0]) bolt(35);
 if(th=="nut") nut();
 if(th=="screw") screw();
 if(th=="motor") motor();
 if(th=="tie") color("Black") difference(){ cylinder(d=30,h=3.5,$fn=48); translate([0,0,-1]) cylinder(d=28,h=6,$fn=48); }
 if(th=="coupling") coupling(-1);
 if(th=="magnet") magnet();
 if(th=="hall") rotate([0,0,90]) hall();
 if(th=="tsens") rotate([0,90,0]) tsens();
 if(th=="oil") rotate([0,90,0]) syringe();
 if(th=="sub7") FA(){ color(OR){ CAR(); HUB(); PL(); } SH_out(); }
 if(th=="sub8") FA(){ color(OR) SUN(); SH_in(); }
 if(th=="sub9") FA(){ color(OR) P_in(); B_in(); }
 if(th=="sub13") GBc(OR);
}
