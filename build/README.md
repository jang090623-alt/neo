# build — 실제 제작판 (2026-11)

v4 설계에서 실제로 만든 것에 맞춘 소스. v4/ 는 그대로 둠.

- **둥근 축 (D컷 없음)**: 부품 축 구멍 12.50 + 에폭시. 공차 BRG 28.15 · PIN 5.05 · RAIL 6.55 · IDLER 12.40, 레일 칼라 구멍 = RAIL_HOLE − 0.25.
  → `src/export.py` 로 다시 만든 부품이 출력한 01~17판과 부피 0.0001% 안에서 같음.
- **클러치 디스크 허브**: 축에 에폭시 (원래는 D축 위에서 미끄러짐).
- **GGM 모터 + 아두이노** (v4 그대로): 모터 받침(45), 표시 바퀴(43)·바퀴 덮개(44, rpm 센서). 덮개 스위치 자리는 전선으로 이음.
- **변속 느낌 (2026-11 말)**: 피벗을 낮춰 손잡이 이동 ±23mm·줄 간격 57.6mm. 게이트 밑면 단 홈(잠금 칼라가 '딸깍' 걸림, 손잡이에서 약 5N),
  위 피벗 위 좌우 피스톤(큰 스프링 2개 직렬 ×2, 필라멘트 핀으로 막음)이 중립 줄로 되돌림 (손잡이 3~6N). 후진은 구면 턱 (누르기 약 21N).
  → 15(새)·16·17판 새로, 러그 51 ×3·잠금판 56 다시 출력 (15판에 포함). 14판은 그대로.
- **페달**: 케이블을 피벗 아래 꼬리(b −22)에 걸어 앞으로 뺌 (위쪽에 걸면 운전자 쪽으로 나가 발에 걸림), 피벗 높이 42, 복귀 스프링 3개, 끝 멈춤 14.1° (릴리스 링 3.07mm) → 20·21·23판 새로.
- 빼는 부품 (학교 물품으로 대신): 클러치 덮개(46·47), 끝 채움판(49), 축 끝 덮개(48), 아크릴 덮개, 핸들 받침(90~96). 페달은 클러치 1개만.

## 다시 만들기
```
cd src && python3 -c "import export; [export.save(m,n) for n,m,q,c,no in export.parts()]"
python3 pack_clutch.py                 # plates/C1~C6 (출력 번호 18~23)
python3 pack_shifter.py                # plates/S15~S17 (변속기 새 판)
python3 verify.py --sweep              # 간섭 검사 (결과 verify_result.json)
cd ../manual && python3 scene.py && python3 steps.py && node render_imgs.js && python3 compose.py && node make_pdf.js
```
렌더러는 three@0.160.0 (npm) 과 Playwright Chromium 을 씀 (`manual/web/three` 링크 필요).
