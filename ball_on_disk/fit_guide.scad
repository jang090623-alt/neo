// 안내관(Ø8) 구멍 공차 시험편 - fit 의 Ø8.3~8.9 구멍 4개가 8 mm 간격이라 서로 붙어 있어서 간격만 13 mm 로 넓힌 것
// 구멍 번호 = 구멍 옆 점 개수 (1점 Ø8.3, 2점 Ø8.5, 3점 Ø8.7, 4점 Ø8.9). 두께는 fit 과 같은 6 mm
d = [8.3, 8.5, 8.7, 8.9];  pitch = 13;  t = 6;
difference() {
  translate([0, 0, 0]) cube([pitch * 4, 18, t]);
  for (i = [0:3]) {
    translate([pitch * (i + 0.5), 8, -1]) cylinder(d = d[i], h = t + 2, $fn = 96);
    for (k = [0:i]) translate([pitch * (i + 0.5) - 3 + k * 2, 15.5, t - 0.6]) cylinder(d = 1.2, h = 1, $fn = 16);   // 번호 점
  }
}
