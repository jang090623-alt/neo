// 시험 4 볼-온-디스크: fit 시험편 결과로 hub·arm·pin 구멍만 고쳐 다시 만드는 파일
// (ball_on_disk.scad 원본이 없어서 최종본 3MF 에서 뽑은 STL(orig/)을 그대로 쓰고 구멍만 메운 뒤 다시 뚫음)
// 사용: openscad -D part="hub" -D dcut_no=3 -o hub.stl fix_holes.scad
//       번호 0 = 설계값 그대로 (hub D컷 4.15x3.65, arm 구멍 Ø8.50, pin 강구 자리 Ø5.95)
part = "hub";      // hub, arm, pin
dcut_no  = 0;      // fit 윗줄 D컷 1~4   (Ø4.0 / 4.1 / 4.2 / 4.3, 평평한 면 폭 = 지름 - 0.5)
guide_no = 0;      // fit_guide 점 1~4   (Ø8.3 / 8.5 / 8.7 / 8.9)  ← 출력한 pin 막대(Ø8)를 끼워 보고 고름
ball_no  = 0;      // fit 아랫줄 강구 1~3 (Ø5.85 / 5.95 / 6.05)  ← Ø6 강구를 끼워 보고 고름

DCUT  = [4.15, 4.0, 4.1, 4.2, 4.3];
GUIDE = [8.50, 8.3, 8.5, 8.7, 8.9];
BALL  = [5.95, 5.85, 5.95, 6.05];

// 원본 구멍 위치 (최종본 3MF 실측)
HUB_C = [191.5, 117.0];   HUB_H = 10;          // D컷 구멍: z 0~10, 평평한 면은 +y 쪽
ARM_C = [187.5, 66.75];   ARM_H = 30;          // 안내관 구멍: z 0~30 관통
PIN_C = [134.5, 89.0];    PIN_Z = 101.7;       // 강구 자리: z 101.7~105

module dshape(d, h) {   // fit 과 같은 D컷: 원 Ø d 에서 +y 쪽을 중심에서 d/2-0.5 위치로 자름
  intersection() { cylinder(d = d, h = h, $fn = 64); translate([-d, -d, -1]) cube([2 * d, 1.5 * d - 0.5, h + 2]); }
}

if (part == "hub") difference() {
  union() { import("orig/hub.stl"); translate([HUB_C[0], HUB_C[1], 0]) dshape(DCUT[0] + 0.02, HUB_H - 0.01); }
  translate([HUB_C[0], HUB_C[1], -1]) dshape(DCUT[dcut_no], HUB_H + 1 - 0.01);
}
if (part == "arm") difference() {
  union() { import("orig/arm.stl"); translate([ARM_C[0], ARM_C[1], 0]) cylinder(d = GUIDE[0] + 0.02, h = ARM_H, $fn = 96); }
  translate([ARM_C[0], ARM_C[1], -1]) cylinder(d = GUIDE[guide_no], h = ARM_H + 2, $fn = 96);
}
if (part == "pin") difference() {
  union() { import("orig/pin.stl"); translate([PIN_C[0], PIN_C[1], PIN_Z]) cylinder(d = BALL[0] + 0.02, h = 105 - PIN_Z, $fn = 64); }
  translate([PIN_C[0], PIN_C[1], PIN_Z]) cylinder(d = BALL[ball_no], h = 10, $fn = 64);
}
