# build — 실제 제작판 (2026-11)

v4 설계에서 실제로 만든 것에 맞춘 소스. v4/ 는 그대로 둠.

- **둥근 축 (D컷 없음)**: 부품 축 구멍 12.50 + 에폭시. 공차 BRG 28.15 · PIN 5.05 · RAIL 6.55 · IDLER 12.40, 레일 칼라 구멍 = RAIL_HOLE − 0.25.
  → `src/export.py` 로 다시 만든 부품이 출력한 01~17판과 부피 0.0001% 안에서 같음.
- **클러치 디스크 허브**: 축에 에폭시 (원래는 D축 위에서 미끄러짐).
- **GGM 모터 + 아두이노** (v4 그대로): 모터 받침(45), 표시 바퀴(43)·바퀴 덮개(44, rpm 센서). 덮개 스위치 자리는 전선으로 이음.
- 빼는 부품 (학교 물품으로 대신): 클러치 덮개(46·47), 끝 채움판(49), 축 끝 덮개(48), 아크릴 덮개, 핸들 받침(90~96). 페달은 클러치 1개만.

## 다시 만들기
```
cd src && python3 -c "import export; [export.save(m,n) for n,m,q,c,no in export.parts()]"
python3 pack_clutch.py                 # plates/C1~C6 (출력 번호 18~23)
python3 verify.py --sweep              # 간섭 검사 (결과 verify_result.json)
cd ../manual && python3 scene.py && python3 steps.py && node render_imgs.js && python3 compose.py && node make_pdf.js
```
렌더러는 three@0.160.0 (npm) 과 Playwright Chromium 을 씀 (`manual/web/three` 링크 필요).
