3D프린팅 5단+후진 수동변속기 v4.1 (2026-10-19)

먼저 볼 것
  설계서_v4.md      결론, 바뀐 점, 고친 결함, 안전율, 덮개, 출력 목록, 조립 순서, 시험 계획, 미검증 항목
  계산서_v4.md      부하 계산서 전체 (calc/calc.py 가 만듦)
  구매목록_v4.xlsx  첫 시트 '구매목록_v4' (노란 칸 단가만 넣으면 합계 계산, 빈 칸 = 미확인)
  조립뷰어.html     3D 조립 뷰어 (브라우저로 열기, 인터넷 필요: three.js CDN)

출력 파일 (stl/, 66개, 출력 방향 반영, 서포트 없음)
  00~03 시험편 · 10~12 기어 · 20~22 슬리브 · 30~35 축 부속 · 40~49 프레임·덮개
  50~61 변속 기구 · 70~79b 클러치 · 80~82 페달
  수량·시간·무게: 설계서_v4.md 6장 (합계 118개, 약 331시간, 3.99kg, PrusaSlicer 2.7.2 추정)
  03_fit_sprocket 은 이미 출력해서 맞음 확인 (v3 파일 그대로)

src/ (설계 원본. 경로는 스크립트 위치 기준이라 어느 폴더에서든 실행됨. STL은 v4/stl 에 바로 저장)
  tx.py          모든 부품 파라메트릭 생성 (공차 상수는 파일 앞부분)
  asm.py         조립 배치·간섭 검사
  verify.py      26개 상태·레버 경로·맞물림·STL 검사 → verify_result.json
  export.py      STL 저장 + 부품표
  slice.py / reslice.py / totals.py   PrusaSlicer 시간·무게
  calc/          calc.py(계산서) · report.py · fem_tooth.py(이뿌리 FEM) · gearcalc.py(v3 비교용 기어 모양)
  bom.py         구매목록 시트 생성
  gen_viewer.py  뷰어 데이터
  fw/shifter_controller/shifter_controller.ino   레오나르도 펌웨어 (게임 입력 + 모터 허가 릴레이)

필요한 파이썬 패키지: manifold3d, shapely, numpy, trimesh, scipy, triangle, openpyxl, fast_simplification
