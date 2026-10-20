"""구매목록.xlsx 에 '구매목록_v4' 시트 추가 (v3 시트 서식을 그대로 복사). 단가 칸이 비어 있으면 미확인."""
import json, os
from copy import copy
import openpyxl
import export

ROOT = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(ROOT, '..', '구매목록_v4.xlsx')
# PLA: 슬라이서 추정 합계(g) + 실패 여유 15% − 보유 750g 롤 1개 → 1kg 롤 수
res = {r[0][:-4]: r[2] for r in json.load(open(os.path.join(ROOT, 'slice_result.json')))}
pla_g = sum(res[n] * q for n, _, q, _, _ in export.parts_meta())
pla_rolls = -(-(pla_g * 1.15 - 750) // 1000)

V3 = '단가는 v3 표(2026-10-19 확인)에서 가져온 것만 넣음'
# (품명, 규격, 수량, 단위, 단가 or None, 용도, 상태, 비고)
ROWS = [
    ('6001ZZ 볼 베어링 (10개 묶음)', '12×28×8', 2, '묶음', 6000, '끝판 4 + 출력 기어 12 + 아이들러 2 + 클러치 파일럿 1 = 19개', '확정', 'v3 단가 · 쿠팡 /vp/products/8630678241'),
    ('6003ZZ 볼 베어링', '17×35×10', 1, '개', 1100, '클러치 릴리스 베어링', '확정', 'KYK 6003ZZ 1개 (표준 17×35×10) · 배송비 3,000 · 2026-10-20 확인 · 02 시험편으로 압입 자리 확인'),
    ('연마봉(강철 축)', 'Ø12 1m → 435·358(둘 다 전체 양면 D컷: 마주 보는 두 면, 면 사이 10.0) + 160', 1, '개', 16000, '입력축 435, 출력축 358, 레버봉 160', '확정', 'v3 단가 · 소망트레이딩(smball.co.kr) · 절단·양면 D컷 가능 여부·비용 미확인 → 불가하면 미스미 양면 D컷 샤프트(길이 지정)'),
    ('연마봉(강철 축) 짧은 것', 'Ø12, 55mm 이상 (55로 절단)', 1, '개', 1600, '후진 아이들러 축', '확정', '소망트레이딩 "열처리 연마봉 절단 판매" 12파이 100mm 옵션 1,600 (2026-10-20 확인) · 55 절단은 문의 문구대로 요청 (안 되면 100 받아서 자름)'),
    ('연마봉(변속 레일)', 'Ø6, 371mm', 3, '개', 5200, '시프트 레일', '확정', '소망트레이딩 6파이 400mm 옵션 5,200/개 (2026-10-20 확인) · 371 절단 요청 (안 되면 400 받아서 자름) · 소망트레이딩 배송비 3,000'),
    ('강철 평행핀', 'Ø5×25', 1, '봉(100개)', 27000, '출력 기어 6개 × 4 = 24 (+여유 4): 도그', '확정', '국산 SUS 평행핀 "M5 (+)공차 / 25mm × 100개" 옵션 (공차 0~+0.01, 무료배송, 2026-10-20 확인) · 28개 필요 · 소량(30개) 해외 상품은 19,500 이나 널링 여부 불명확해 제외 · 02 시험편(구멍 4.8/4.9/5.0)으로 압입 구멍 확정'),
    ('강철 평행핀', 'Ø5×40', 6, '개', 440, '스프로킷 커플링 핀', '확정', '국산 SUS 평행핀 M5 (+) 0~+0.01, 5x40 낱개 (2026-10-20 확인) · 배송비 4,000'),
    ('NBR 고무 호스', '안지름 5 × 바깥지름 10', 1, '개(약2m)', 8900, '핀 쿠션 (6mm × 24개 = 144mm)', '확정', '진공호스(카박스) 내경 5 · 외경 10 · 약 2m, 국내생산 (2026-10-20 확인) · 재질 표기 없음(고무) → 도착 후 경도 손으로 확인, 너무 무르면 실리콘 70도 5x10 으로'),
    ('큰 와셔 DIN9021 M16 (강철)', '안지름 17 × 바깥지름 50 × 두께 3', 2, '개', 710, '클러치 원판 1 + 여분 1', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 스텐 대와셔 "M16 × 50mm" 옵션 = 안지름 17·바깥 50·두께 3 (상세 표 확인, 2026-10-20 확인)'),
    ('코르크 시트', '두께 2mm, A4', 1, '장', 1890, '클러치 마찰재 링 2개 (바깥 Ø50, 안 Ø26)', '확정', '콜크쉬트 연갈색 2mm × A4 × 2매 (2026-10-20 확인) · 배송비 2,500'),
    ('압축 스프링 C252', '외경 18, 자유장 32', 9, '개', 8360, '포크 카트리지 3 + 클러치 3 + 레버 후진 잠금 1 + 페달 복귀 2', '확정', '디바이스마트 no=15336269 · 8,360원 = 1개 값(VAT 포함, 2026-10-20 화면 확인) · 반품 불가 · 준비 4~5일 · 재질 SUS304, 하중 ±10%, 끝면 연삭 · 선경 미표기 → k·허용 길이로 역산 선경 1.7 이하, 안지름 14.6 이상 (필요 12.5, 실측 전)'),
    ('압축 스프링 C147', '외경 5, 길이 10', 3, '개', 990, '러그 디텐트', '확정', '디바이스마트 no=15336164'),
    ('강구', 'Ø6mm 50개', 1, '봉', 3500, '러그 디텐트 3', '확정', 'v3 단가 · 쿠팡 /9638493021'),
    ('샤프트 칼라 (Ø6 축용)', '안지름 6.1, 바깥지름 11, 폭 6, 멈춤나사형 (RC 휠 칼라, 10개)', 1, '봉(10개)', 14800, '변속 레일 카트리지 양쪽', '확정', '옵션 "01 D11xd6.1xH6mm" 14,800 (해외, 무료배송, 11/4 도착 예정, 2026-10-20 확인) · 6개 필요 · 바깥 11 ≤ 12 → 카트리지 구멍(13) 통과 · 폭 6 < 설계값 8 (tx.RAIL_COLLAR) 이라 간섭 검사보다 작음 · 쿠팡 6/12/8 표준품(SOH6)은 1개 10,620 이라 제외'),
    ('M3 렌치볼트', 'M3×8 (육각 홈붙이, 스텐)', 9, '개', 50, '포크 카트리지 뚜껑 6, 디텐트 3 (C147 을 5mm 로 누름)', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 스텐 유두 렌치볼트 낱개 (2026-10-20 확인) · 모든 볼트는 렌치볼트(머리 Ø5.5): 부품의 머리 자리가 이 크기'),
    ('M3 렌치볼트', 'M3×10', 1, '개', 60, '클러치 포크 속선 누름 (자가탭, 와셔 1)', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) (2026-10-20 확인)'),
    ('M3 렌치볼트', 'M3×12', 34, '개', 60, '칼라 7, 클러치 덮개 7, 축 끝 덮개 4, 바퀴 덮개 2, 아크릴 14', '확정', '모두 자가탭 · 아크릴에는 M3 와셔 · 리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) (2026-10-20 확인)'),
    ('M3 렌치볼트', 'M3×16', 2, '개', 100, '바퀴 덮개 아래 받침', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) (2026-10-20 확인)'),
    ('M3 렌치볼트 + 너트', 'M3×20', 9, '세트', 130, '슬리브 결합 (머리·너트는 육각 자리 안에 숨음)', '확정', '냄비머리(Ø6)는 육각 자리(맞변 5.7)에 안 들어감 · 리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 볼트 70 + 스텐 육각너트 M3 60 (2026-10-20 확인)'),
    ('M3 렌치볼트', 'M3×25', 6, '개', 70, '러그 (자가탭, 끝이 레일을 누름)', '확정', 'M3×30 은 머리가 러그 위로 5mm 나와 캐리어에 닿음 · 리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) (2026-10-20 확인)'),
    ('M3 렌치볼트', 'M3×50', 4, '개', 170, '끝 채움판 → 끝판', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) (2026-10-20 확인)'),
    ('M3 무두볼트', 'M3×8', 1, '개', 60, '표시 바퀴 고정', '확정', '스텐 무두렌치볼트 오목끝 M3 8mm 낱개 (2026-10-20 확인) · 배송비 3,000 (리우툴 낱개 M3×8 없음)'),
    ('M3 평와셔', 'M3 (바깥지름 8, 두께 0.5)', 15, '개', 20, '아크릴 고정 나사 밑 14 (균열 방지) + 속선 누름 1', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) "스텐 평와셔 M3x8x0.5T" (2026-10-20 확인) · 바깥 7 낱개는 쿠팡에 없어 8 로 · 속선 누름: 와셔 반지름 4 = 속선까지 거리 4 → 오히려 더 덮음, 포크 몸통 폭 18 안'),
    ('M4 렌치볼트 + 너트', 'M4×16', 4, '세트', 170, '클러치 포크 브래킷 (너트는 끝판 A 안쪽 홈)', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 볼트 110 + 너트 60 (2026-10-20 확인)'),
    ('M4 렌치볼트 + 너트', 'M4×25', 4, '세트', 160, '페달 발판 (너트는 팔 앞면 홈)', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 볼트 100 + 너트 60 (2026-10-20 확인)'),
    ('M4 렌치볼트 + 너트', 'M4×30', 20, '세트', 190, '케이지 4, 피벗 8, 게이트 4, 받침 브래킷 4', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 볼트 130 + 너트 60 (2026-10-20 확인)'),
    ('M4 렌치볼트 + 너트', 'M4×60', 3, '세트', 350, '클러치 기둥', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 볼트 290 + 너트 60 (2026-10-20 확인)'),
    ('M5 렌치볼트 + 너트', 'M5×10', 3, '세트', 200, '클러치 조절나사 (끝까지 조임 = 설정)', '확정', 'M5×12 이상 금지 (미끄럼 토크가 1.05N·m 까지 올라가 기어 설계 하중 초과) · 리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 볼트 110 + 너트 90 (2026-10-20 확인)'),
    ('M5 렌치볼트 + 너트', 'M5×20', 3, '세트', 230, '클러치 릴리스 누름 볼트', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 볼트 140 + 너트 90 (2026-10-20 확인)'),
    ('M5 렌치볼트 + 평와셔', 'M5×8 3개 + M5×12 3개 + M5 와셔 3개', 1, '세트', 720, '클러치 미끄럼 토크 조정 (설계서 8장 시험 3: 크면 M5×8, 작으면 M5×12 + 와셔 1장)', '확정', '시험 3 이 합격이면 안 씀 · 다시 주문하지 않으려고 같이 구매 · 리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 100×3 + 110×3 + 평와셔 M5x12x0.5T 30×3 (2026-10-20 확인)'),
    ('M5 렌치볼트 + 나일론 너트', 'M5×70', 1, '세트', 550, '클러치 포크 피벗 (팔·볼·보스 관통)', '확정', '너트는 손으로 닿을 때까지만 (세게 조이면 포크가 안 돎) · 리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 볼트 470 + 스텐 나일론너트 M5 80 (2026-10-20 확인)'),
    ('M6 렌치볼트', 'M6×25', 6, '개', 210, '모터 받침 4 (45 밑면 너트), 페달 피벗 2', '확정', 'M6×30 이상 금지 (모터 받침: MDF 에 닿음, 페달: 가변저항 축에 닿음) · 리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) (2026-10-20 확인)'),
    ('M6 너트', 'M6 (맞변 10)', 4, '개', 60, '모터 받침 (45 밑면 홈)', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 스텐 육각너트 M6 (2026-10-20 확인)'),
    ('M6 나일론 너트', 'M6 (DIN985, 두께 6)', 2, '개', 170, '페달 피벗 (팔 너트 홈, 볼트가 팔과 같이 돎 → 풀리지 않음)', '확정', '리우툴(판매자 우진카본볼트, 한 번 배송비 3,000) 스텐 나일론너트 M6 (2026-10-20 확인)'),
    ('목재 나사', '4×16 둥근머리 1종 (스텐, 26개 봉)', 1, '봉(26개)', 1150, '받침 브래킷 8, 클러치 덮개 4, 모터 받침 4, 페달 받침 8', '확정', '옵션 "1-5 스텐둥근1종(M4) e)4x16mm-26개" (2026-10-20 확인) · 24개 필요 · 배송비 2,800 · MDF 12T 에 10~11 박힘 · 4×20 이상은 밑으로 나옴 · 머리 자리 Ø9 → 와샤머리(Ø10 내외) 안 됨'),
    ('에폭시 접착제', '2액형', 1, '개', 4440, '레버봉-핑거·손잡이, 아이들러 축, 클러치 와셔-허브, 고무 쿠션, 페달 가변저항 2', '확정', 'Vtech 주사기 에폭시 25ml 1개 (2026-10-20 확인)'),
    ('순간접착제', '일반', 1, '개', 3000, '덮개 스위치, 홀센서, 자석', '확정', '탐사 젤타입 2개 (2026-10-20 확인) · 보유하면 생략'),
    ('자전거 브레이크 케이블 세트', '속선(니플 달린 것) 2m + 아우터 바깥지름 5 2m + 끝 캡', 1, '세트', 6900, '클러치 페달 → 클러치 포크', '확정', '[RCM] 브레이크케이블세트 (속선 2줄 + 겉선 + 마감재, 2026-10-20 확인) · 아우터가 끝판 B 구멍 Ø6·페달 받침 Ø5.6 에 들어가야 함 (자전거 브레이크 겉선 표준 5) · 니플은 페달 팔 Ø3.4 구멍보다 커야 함'),
    ('MDF 판', '12T 300×1200 재단', 1, '장', 9600, '바닥판 750×300 (모터·클러치 덮개 포함) + 남는 450×300 = 페달 받침판 (바닥)', '확정', 'v3 단가 · 쿠팡 /71452005'),
    ('투명 아크릴', 'A3 3T', 3, '장', 9000, '덮개 윗판 250×321, 옆판 200×321 × 2', '확정', 'v3 단가 · 쿠팡 /9593337115 · 재단 주문 가능하면 치수대로'),
    ('아두이노 레오나르도 R3 + 케이블', 'ATmega32u4', 1, '개', 9200, '센서 → PC 게임 입력 + 모터 허가 출력', '확정', 'v3 단가 · 쿠팡 /1119152790'),
    ('홀센서 A3144', '3핀 소자', 7, '개', 90, '기어 위치 6 + 출력 rpm 1', '확정', 'v3 단가 · 쿠팡 /8520223332'),
    ('네오디뮴 자석', 'Ø6×3mm', 10, '개', 220, '러그 3 + 표시 바퀴 4 (+여분 3)', '확정', '디바이스마트 ND 원형자석 6Ø x 3t, 최소 10개 (2026-10-20 확인) · 쿠팡 40개 봉(11,300) 대신'),
    ('가변저항 B10K', '회전형 16mm, 축 Ø6 반달(D컷, 평면까지 4.5~4.6), 축 길이 15mm(장착면부터), 부싱 M7', 3, '개', 3993, '클러치·브레이크 페달 2 + 핸들 1', '확정', '디바이스마트(Mouser 대행) TT Electronics P160KNP-1FD15B10K 3,993(VAT 포함, 2026-10-20 확인) · 데이터시트: F형 축 Ø6 평면 4.5, L 15, 부싱 M7×0.75, 몸통 Ø16.5 · 가운데 딸깍(center detent) 있음 → 페달은 몸통 에폭시 때 딸깍 위치가 밟는 범위 밖이 되게 돌려 붙임 · 쿠팡은 전부 톱니(널링) 축이라 제외 · 반품 불가, 준비 1주 · C252 와 같이 주문 → 66,000 넘어 배송비 0'),
    ('마이크로스위치', 'KW-11-3Z 레버형', 2, '개', 400, '덮개 열림 감지 1 + 여분 1', '확정', 'v3 단가 · 쿠팡 /9167678186'),
    ('점퍼 케이블', 'M-F 40P 40cm', 1, '개', 5300, '센서 배선', '확정', 'v3 단가 · 쿠팡 /9699042565'),
    ('만능기판', '하프 사이즈 89×52 (브레드보드형, 양면)', 1, '장', 2420, '센서 배선', '확정', '디바이스마트 일렉트로쿠키 브레드보드형 만능기판 Half (2026-10-20 확인) · 쿠팡 20장 묶음(15,000) 대신'),
    ('자동차 릴레이 + 소켓', '12V, 접점 40A, 4핀', 1, '개', 3100, '모터 전원 주 스위치', '확정', '12v 4핀 릴레이 + 배선된 소켓 세트 40A (2026-10-20 확인) · 배송비 3,000 · 코일 회로에 비상정지·덮개 스위치·5V 릴레이 모듈 직렬'),
    ('블레이드 퓨즈 + 인라인 홀더', '15A', 1, '세트', 8900, '배터리 + 단자 바로 옆', '확정', '12AWG 인라인 ATC/ATO 홀더 4개 + 퓨즈 12개(15A 2개 포함) (2026-10-20 확인) · 여분 퓨즈 포함'),
    ('비상정지 스위치', '버섯형, b접점(NC)', 1, '개', 7370, '운영자 비상 차단 (릴레이 코일 회로)', '확정', '디바이스마트 KGAUTO KGE-C4R1R 25Φ 푸쉬록턴 리셋 1a1b (2026-10-20 확인) · 준비 2주 · 25mm 판 구멍 필요'),
    ('5V 릴레이 모듈', '1채널, 로우 트리거', 1, '개', 990, '아두이노 워치독 → 주 릴레이 코일 차단', '확정', '디바이스마트 SZH-RLBG-007 Low-Trigger (2026-10-20 확인) · 펌웨어 RELAY_ACTIVE_LOW 기본값(로우)과 맞음'),
    ('다이오드 1N4007', '', 10, '개', 22, '주 릴레이 코일 역기전력 흡수 1 + 여분', '확정', '디바이스마트 1N4007, 최소 10개 (2026-10-20 확인) · 내장 다이오드 릴레이면 생략'),
    ('전선', '1.5mm²(16AWG) 이상, 적·흑 각 2m', 2, '세트(1m)', 1310, '배터리-퓨즈-릴레이-모터 드라이버', '확정', 'KDsafe 실리콘전선 16AWG 빨검 세트 1M × 2 (2026-10-20 확인) · 배송비 3,000 · 키트 배터리 선 16AWG 확인(2026-10-20) → 퓨즈 15A 유지'),
    ('압착 단자 세트', '250 규격(6.3mm) 절연 암 평형 단자 (22~16AWG)', 3, '봉(2개)', 310, '퓨즈 홀더·릴레이 소켓 연결 (배터리 쪽은 키트 선 단자 재사용)', '확정', '6.3mm 절연 PG REC 250 빨강 2개 × 3 (2026-10-20 확인) · 배송비 3,000 · 절연형이라 수축 튜브 불필요 · 배터리 단자 = 6.3mm 평형 탭(사진 확인) · 릴레이 소켓은 배선 완성품'),
    ('저항', '10kΩ 30개 + 4.7kΩ 30개 (1/4W, 최소 수량)', 1, '세트', 1518, '안전 회로 감지 (비상정지·덮개 뒤 12V → 아두이노 A4)', '확정', '디바이스마트 제일전자 103J·472J 각 30개 × 25.3원 (2026-10-20 확인) · 1개씩 사용 · 풀었을 때 페달을 떼야 재시동 (펌웨어)'),
    ('배송비', '새 판매처 포함', 1, '식', 53200, None, '확정', 'v3 22,900 + 새 판매처 30,300 (2026-10-20 확인): KYK 3,000 · 평행핀 5x40 4,000 · 리우툴 3,000 · 무두볼트 3,000 · 목재나사 2,800 · 코르크 2,500 · 릴레이 3,000 · 전선 3,000 · 압착단자 3,000 · 소망트레이딩 3,000 / 디바이스마트(66,000 이상)·나머지 무료배송'),
]

# 품명 칸 링크: 쿠팡 상품(번호) 또는 쿠팡 검색어. 규격이 계산에 들어가는 스프링·가공 축은 원래 판매처
from urllib.parse import quote
CP = 'https://www.coupang.com/vp/products/'
RW = CP + '6455358137'   # 리우툴 스텐 유두 렌치볼트 낱개 (M3~M6 전 길이)
SM = 'https://smball.co.kr/product/detail.html?product_no=50'   # 소망트레이딩 열처리 연마봉 절단 판매
LINK = {
    '6001ZZ 볼 베어링 (10개 묶음)': CP + '8630678241', '6003ZZ 볼 베어링': CP + '8230435105',
    '연마봉(강철 축)': 'https://smball.co.kr', '연마봉(강철 축) 짧은 것': SM, '연마봉(변속 레일)': SM,
    ('강철 평행핀', 'Ø5×25'): CP + '9743421687', ('강철 평행핀', 'Ø5×40'): CP + '8532354386', 'NBR 고무 호스': CP + '8558801755',
    '큰 와셔 DIN9021 M16 (강철)': CP + '6305734042', '코르크 시트': CP + '4845669553',
    '압축 스프링 C252': 'https://www.devicemart.co.kr/goods/view?no=15336269', '압축 스프링 C147': 'https://www.devicemart.co.kr/goods/view?no=15336164',
    '강구': CP + '9638493021', '샤프트 칼라 (Ø6 축용)': CP + '9669133315',
    ('M3 렌치볼트', 'M3×8 (육각 홈붙이, 스텐)'): RW, ('M3 렌치볼트', 'M3×10'): RW,
    ('M3 렌치볼트', 'M3×12'): RW, ('M3 렌치볼트', 'M3×16'): RW,
    'M3 렌치볼트 + 너트': RW, ('M3 렌치볼트', 'M3×25'): RW, ('M3 렌치볼트', 'M3×50'): RW,
    'M3 무두볼트': CP + '7974822838', 'M3 평와셔': CP + '7440529428',
    ('M4 렌치볼트 + 너트', 'M4×16'): RW, ('M4 렌치볼트 + 너트', 'M4×25'): RW,
    ('M4 렌치볼트 + 너트', 'M4×30'): RW, ('M4 렌치볼트 + 너트', 'M4×60'): RW,
    ('M5 렌치볼트 + 너트', 'M5×10'): RW, ('M5 렌치볼트 + 너트', 'M5×20'): RW,
    'M5 렌치볼트 + 평와셔': RW, 'M5 렌치볼트 + 나일론 너트': RW,
    'M6 렌치볼트': RW, 'M6 너트': CP + '7687671245', 'M6 나일론 너트': CP + '6280971320',
    '목재 나사': CP + '7760964029', '에폭시 접착제': CP + '2725054', '순간접착제': CP + '8643897709',
    '자전거 브레이크 케이블 세트': CP + '8305908512', 'MDF 판': CP + '71452005', '투명 아크릴': CP + '9593337115',
    '아두이노 레오나르도 R3 + 케이블': CP + '1119152790', '홀센서 A3144': CP + '8520223332', '네오디뮴 자석': 'https://www.devicemart.co.kr/goods/view?no=31671',
    '가변저항 B10K': 'https://www.devicemart.co.kr/goods/view?no=16130996', '마이크로스위치': CP + '9167678186', '점퍼 케이블': CP + '9699042565',
    '만능기판': 'https://www.devicemart.co.kr/goods/view?no=12506669', '자동차 릴레이 + 소켓': CP + '6667848502', '블레이드 퓨즈 + 인라인 홀더': CP + '9663070188',
    '비상정지 스위치': 'https://www.devicemart.co.kr/goods/view?no=10895020', '5V 릴레이 모듈': 'https://www.devicemart.co.kr/goods/view?no=1327543', '다이오드 1N4007': 'https://www.devicemart.co.kr/goods/view?no=3011',
    '전선': CP + '7225302003', '압착 단자 세트': CP + '8667960491', '저항': 'https://www.devicemart.co.kr/goods/view?no=856',
   
}

def link(name, spec):
    q = LINK.get((name, spec), LINK.get(name))
    if q is None:
        return None
    return q if q.startswith('http') else 'https://www.coupang.com/np/search?q=' + quote(q)

wb = openpyxl.load_workbook(PATH)
if '구매목록_v4' in wb.sheetnames:
    del wb['구매목록_v4']
src = wb['구매목록_v3']
ws = wb.create_sheet('구매목록_v4', 0)
wb.active = 0

def style(dst, s):
    dst.font = copy(s.font); dst.fill = copy(s.fill); dst.border = copy(s.border)
    dst.alignment = copy(s.alignment); dst.number_format = s.number_format

for col, dim in src.column_dimensions.items():
    ws.column_dimensions[col].width = dim.width
ws['A1'] = '3D프린팅 수동변속기 제작 - 구매 물품 목록 (v4.1)'; style(ws['A1'], src['A1'])
ws['A2'] = ('작성일 2026-10-19 · 설계서 v4.1 기준 · 노란 칸(단가)만 입력하면 금액·합계가 계산됩니다. '
            + V3 + ', 비어 있는 칸은 미확인입니다. 나머지 단가는 2026-10-20 쿠팡 등에서 확인. 품명을 누르면 고른 상품으로 (스프링·가변저항은 디바이스마트, 축은 소망트레이딩). 판매처별 주문 방법은 두 번째 시트 \'주문방법\'.')
style(ws['A2'], src['A2'])
ws.row_dimensions[1].height = src.row_dimensions[1].height
ws.row_dimensions[2].height = src.row_dimensions[2].height
for c in range(1, 11):
    d, s = ws.cell(4, c), src.cell(4, c)
    d.value = s.value; style(d, s)
ws.row_dimensions[4].height = src.row_dimensions[4].height
r0 = 5
for i, (name, spec, q, unit, price, use, st, note) in enumerate(ROWS):
    r = r0 + i
    vals = [i + 1, name, spec, q, unit, price, f'=D{r}*F{r}', use, st, note]
    for c, v in enumerate(vals, 1):
        d = ws.cell(r, c); d.value = v; style(d, src.cell(5, c))
    u = link(name, spec)
    if u:
        ws.cell(r, 2).hyperlink = u
    ws.row_dimensions[r].height = src.row_dimensions[5].height
last = r0 + len(ROWS) - 1
tot = [('합계 (확정 항목, 단가 입력된 것만)', f'=SUMIFS(G{r0}:G{last},I{r0}:I{last},"확정")', 36),
       ('합계 (선택 포함)', f'=SUM(G{r0}:G{last})', 37),
       ('단가 미확인 항목 수', f'=COUNTBLANK(F{r0}:F{last})', 38)]
for k, (lab, f, sr) in enumerate(tot):
    r = last + 1 + k
    ws.cell(r, 2).value = lab; style(ws.cell(r, 2), src.cell(sr, 2))
    ws.cell(r, 7).value = f; style(ws.cell(r, 7), src.cell(sr, 7))
# 두 번째 시트: 판매처별 주문 방법 (주문 전 확인할 것 포함)
if '주문방법' in wb.sheetnames:
    del wb['주문방법']
wo = wb.create_sheet('주문방법', 1)
ORDER = [
    ('판매처', '품목', '방법 · 확인할 것'),
    ('디바이스마트', '압축 스프링 C252 9개, C147 3개, 가변저항 P160KNP-1FD15B10K 3개, 5V 릴레이 모듈, 1N4007, 저항, 비상정지 스위치, 만능기판, 자석 10개', '한 장바구니로 주문 (합계 66,000 이상 → 배송비 0). C252 = 1개 8,360원(VAT 포함), 수량 9 로 내려감 확인(2026-10-20), 반품·취소 불가, 준비 4~5일. '
     'C252: https://www.devicemart.co.kr/goods/view?no=15336269 / C147: https://www.devicemart.co.kr/goods/view?no=15336164 (외경 5, 자유장 10, P1 1.77N@6.47, P2 2.79N@4.41 인지 확인) / '
     '가변저항: https://www.devicemart.co.kr/goods/view?no=16130996 (Mouser 대행, TT Electronics P160 F형 D축 Ø6·평면 4.5·L15·부싱 M7×0.75, 가운데 딸깍 있음, 반품 불가, 준비 1주. 쿠팡 B10K 는 전부 톱니 축이라 여기서)'),
    ('소망트레이딩 (smball.co.kr)', '연마봉 Ø12 435·358(양면 D컷)·160·55, Ø6 371 ×3',
     'D컷 가공을 맡김. 게시판·카카오톡에 도면(v4/도면_D컷축.pdf 또는 .png)을 첨부하고 아래 문구 그대로 견적 요청: "열처리 연마봉 Ø12 를 아래처럼 절단·가공해 주시고 가격을 알려 주세요. '
     '1) 435mm 1개, 2) 358mm 1개: 두 개 모두 전체 길이 양면 D컷 (마주 보는 두 면, 면 사이 10.0mm, 한쪽 깊이 1.0mm) '
     '3) 160mm 1개, 4) 55mm 1개: 가공 없음 5) Ø6 연마봉 371mm 3개: 가공 없음. 길이 오차 ±0.5mm 이내 가능한지도 알려 주세요." '
     '열처리봉이 가공 어렵다고 하면 S45C 비열처리 연마봉으로 해도 됨 (축 안전율 14 이상이라 강도 문제 없음). 견적이 오면 구매신청 "축 양면 D컷 가공" 줄에 금액을 넣음'),
    ('쿠팡', '위 두 곳을 뺀 나머지 전부', '구매목록 시트의 품명을 누르면 고른 쿠팡 상품 (2026-10-20 확인). 옵션이 있는 상품은 비고 칸의 옵션 이름으로 고를 것. '
     '볼트·너트·와셔(M3 무두볼트 빼고)는 리우툴(판매자 우진카본볼트) 한 판매자 → 한 장바구니. 고른 상품은 아래 7가지를 지킴: '
     '① 가변저항 = 축 Ø6 반달(D컷) 15mm + 부싱 M7 (톱니 축·20mm 안 됨) ② 볼트 = 렌치볼트(육각 홈, 머리 Ø5.5) — 냄비머리 안 됨 '
     '③ 샤프트 칼라 = 안지름 6, 바깥지름 12 이하 ④ 6003ZZ = 17×35×10 ⑤ 평행핀 = Ø5 정확히 (25·40 길이) ⑥ PLA = 2.85mm ⑦ 목재나사 = 4×16 (4×20 이상 안 됨)'),
    ('공구 (보유, 목록에서 뺌)', '육각 렌치 2.5·3·4·5, 드릴 + Ø3.4 날, 납땜 인두·실납, 걸이 저울 0~5kg(10g 단위, 시험 3 클러치 토크용), 디지털 캘리퍼스(0.01mm, 학교 것)',
     '렌치볼트·무두볼트 / 아크릴 나사 구멍 14 (드릴이 없으면 아크릴 재단 업체에 구멍까지 주문) / 만능기판'),
    ('PLA (따로 준비)', f'2.85mm PLA 약 {pla_g * 1.15 / 1000:.1f}kg (보유 750g 빼면 1kg 롤 {int(pla_rolls)}개)',
     f'구매 신청에서 뺌. 출력 예상 {pla_g / 1000:.2f}kg + 실패 여유 15% (PrusaSlicer 추정). Ultimaker 2+ 용 2.85mm. 쿠팡 해외 1kg 30,600원(11/5 도착) 또는 국내 UltiMaker 750g 75,900원'),
    ('도착 후', '—', '① 가변저항 축 지름·평면·길이 실측 → 80·82 페달 출력 (다르면 수정) ② 핀·6003 도착 → 02 시험편 출력 '
     '③ 00 쿠폰 구멍마다 안 들어감/꽉/헐거움 → 공차 확정 후 전체 출력 ④ C252 안지름 실측 (12.5 이상)'),
]
for i, row in enumerate(ORDER, 1):
    for j, v in enumerate(row, 1):
        c = wo.cell(i, j); c.value = v
        c.alignment = openpyxl.styles.Alignment(wrap_text=True, vertical='top')
        if i == 1:
            c.font = openpyxl.styles.Font(bold=True)
for col, w in (('A', 22), ('B', 34), ('C', 110)):
    wo.column_dimensions[col].width = w
wb.save(PATH)
print('rows', len(ROWS), 'last', last, 'PLA g', round(pla_g), 'rolls', pla_rolls)

# 제출용 신청서 (동아리 학술제 물품 구입 신청 1차): 판매처별로 묶어 A4 세로 한 장 + 구입처 링크 시트.
# 같은 내용을 HTML 로도 써서 PDF 로 인쇄할 수 있게 함 (구매신청_최종.html)
import html as _html
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from urllib.parse import urlparse, parse_qs
FINAL = os.path.join(ROOT, '..', '구매신청_최종.xlsx')
FINAL_HTML = os.path.join(ROOT, '..', '구매신청_최종.html')
APPLY = {'동아리명': 'RPM', '지도교사': '홍경표, 장수빈', '신청일': '2026년 10월    일',
         '학술제 주제': '직접 설계·3D 프린팅한 5단+후진 수동변속기로 탐구하는 기어비와 동력 전달 (전시·체험)',
         '구입 목적': '수동변속기 제작 재료: 축·베어링·볼트 등 금속 부품, 스프링, 전기·안전 부품 (3D 프린팅 필라멘트는 별도 준비)'}
NOTE = ('단가는 2026-10-20 판매처 화면 가격(VAT 포함)이며 주문 시점에 조금 달라질 수 있음. '
        '배송비는 판매처별 합계. 축 양면 D컷 가공비는 소망트레이딩 견적 회신 후 확정.')
SHORT = {'연마봉(강철 축)': 'Ø12 1m (435·358·160 으로 절단)',
         '가변저항 B10K': '16mm, D축 Ø6 15mm, 부싱 M7 (P160KNP-1FD15B10K)',
         '압축 스프링 C252': '외경 18, 자유장 32, SUS304'}


def shop(u):
    if not u:
        return '-', ''
    h, q = urlparse(u).netloc, parse_qs(urlparse(u).query)
    if 'devicemart' in h:
        return '디바이스마트', q.get('no', [''])[0]
    if 'smball' in h:
        return '소망트레이딩', ''
    return '쿠팡', u.rsplit('/', 1)[-1] if '/vp/products/' in u else ''


ORDER_SHOP = {'디바이스마트': 0, '소망트레이딩': 1, '쿠팡': 2, '-': 3}
items = []
for i, (name, spec, q, unit, price, use, st, note) in enumerate(ROWS):
    s, no = shop(link(name, spec))
    items.append((ORDER_SHOP[s], i, name, SHORT.get(name, spec), q, unit, price, s, no, link(name, spec)))
items.sort()
DCUT = ('축 양면 D컷 가공 (입력축 435, 출력축 358)', '면 사이 10.0, 전체 길이', 2, '개', '소망트레이딩(가공)')
total = sum(it[4] * it[6] for it in items)

fb = openpyxl.Workbook()
fs = fb.active
fs.title = '물품 구입 신청'
thin = Side(style='thin', color='808080')
box_b = Border(left=thin, right=thin, top=thin, bottom=thin)
F8, F9 = Font(size=8), Font(size=9)
fs['A1'] = '2026학년도 동아리 학술제 물품 구입 신청서 (1차)'
fs['A1'].font = Font(bold=True, size=14)
fs.merge_cells('A1:I1')
fs['A1'].alignment = Alignment(horizontal='center')
r = 3
for k, v in APPLY.items():
    fs.cell(r, 1, k).font = Font(bold=True, size=9)
    fs.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
    fs.cell(r, 3, v).font = F9
    fs.merge_cells(start_row=r, start_column=3, end_row=r, end_column=9)
    for c in range(1, 10):
        fs.cell(r, c).border = box_b
    fs.cell(r, 3).alignment = Alignment(wrap_text=True, vertical='center')
    r += 1
r += 1
for c, v in enumerate(['번호', '품명', '규격', '수량', '단위', '단가', '금액', '구입처', '상품번호'], 1):
    x = fs.cell(r, c, v)
    x.font = Font(bold=True, size=8); x.border = box_b
    x.fill = PatternFill('solid', fgColor='DDDDDD'); x.alignment = Alignment(horizontal='center', vertical='center')
r += 1
r0 = r
for k, (_, _, name, spec, q, unit, price, s, no, u) in enumerate(items, 1):
    for c, v in enumerate([k, name, spec, q, unit, price, f'=D{r}*F{r}', s, no], 1):
        x = fs.cell(r, c, v)
        x.font = F8; x.border = box_b
        x.alignment = Alignment(vertical='center', wrap_text=c in (2, 3), horizontal='center' if c in (1, 4, 5, 8) else None)
        if c in (6, 7):
            x.number_format = '#,##0'
    if u:
        fs.cell(r, 2).hyperlink = u
    r += 1
for c, v in zip((1, 2, 3, 4, 5, 7, 8), (len(items) + 1,) + DCUT[:4] + ('견적 후', DCUT[4])):
    fs.cell(r, c, v)
for c in range(1, 10):
    x = fs.cell(r, c); x.border = box_b; x.font = F8
    x.alignment = Alignment(vertical='center', horizontal='center' if c in (1, 4, 5, 7, 8) else None)
r += 1
fs.cell(r, 5, '합계 (가공비 제외)').font = Font(bold=True, size=9)
fs.merge_cells(start_row=r, start_column=5, end_row=r, end_column=6)
fs.cell(r, 7, f'=SUM(G{r0}:G{r - 1})').font = Font(bold=True, size=9)
fs.cell(r, 7).number_format = '#,##0'
for c in (5, 6, 7):
    fs.cell(r, c).border = box_b
r += 1
fs.cell(r, 1, '※ ' + NOTE).font = Font(size=8)
fs.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
fs.cell(r, 1).alignment = Alignment(wrap_text=True)
fs.row_dimensions[r].height = 24
r += 2
fs.cell(r, 6, '신청자:').font = F9
fs.cell(r, 7, '                (서명)').font = F9
fs.cell(r + 1, 6, '지도교사:').font = F9
fs.cell(r + 1, 7, '                (서명)').font = F9
r += 1
for col, w in zip('ABCDEFGHI', (5, 26, 30, 5, 6, 8, 9, 13, 11)):
    fs.column_dimensions[col].width = w
fs.page_setup.paperSize = fs.PAPERSIZE_A4
fs.page_setup.orientation = 'portrait'
fs.page_setup.fitToWidth = 1
fs.page_setup.fitToHeight = 1
fs.sheet_properties.pageSetUpPr.fitToPage = True
fs.page_margins.left = fs.page_margins.right = 0.4
fs.page_margins.top = fs.page_margins.bottom = 0.5
fs.print_area = f'A1:I{r}'
fs.print_options.horizontalCentered = True
# 두 번째 시트: 구입처 링크 (행정실·주문하는 사람용)
fl = fb.create_sheet('구입처 링크')
fl.append(['번호', '품명', '구입처', '상품 링크'])
for k, (_, _, name, spec, q, unit, price, s, no, u) in enumerate(items, 1):
    fl.append([k, name, s, u or ''])
    if u:
        fl.cell(k + 1, 4).hyperlink = u
for c in range(1, 5):
    fl.cell(1, c).font = Font(bold=True)
for col, w in zip('ABCD', (5, 30, 14, 70)):
    fl.column_dimensions[col].width = w
fb.save(FINAL)

# 같은 내용의 HTML (Chrome 등으로 PDF 인쇄)
E = _html.escape
rows_html = ''.join(
    f'<tr><td class=c>{k}</td><td>{E(name)}</td><td>{E(str(spec))}</td><td class=c>{q}</td><td class=c>{E(unit)}</td>'
    f'<td class=n>{price:,}</td><td class=n>{q * price:,}</td><td class=c>{E(s)}</td><td class=c>{E(no)}</td></tr>'
    for k, (_, _, name, spec, q, unit, price, s, no, u) in enumerate(items, 1))
rows_html += (f'<tr><td class=c>{len(items) + 1}</td><td>{E(DCUT[0])}</td><td>{E(DCUT[1])}</td><td class=c>{DCUT[2]}</td>'
              f'<td class=c>{DCUT[3]}</td><td></td><td class=c>견적 후</td><td class=c>{E(DCUT[4])}</td><td></td></tr>')
info_html = ''.join(f'<tr><th>{E(k)}</th><td>{E(v)}</td></tr>' for k, v in APPLY.items())
link_html = ''.join(f'<tr><td class=c>{k}</td><td>{E(name)}</td><td class=c>{E(s)}</td><td class=u>{E(u or "")}</td></tr>'
                    for k, (_, _, name, spec, q, unit, price, s, no, u) in enumerate(items, 1))
CSS = ("@page{size:A4;margin:9mm}body{font-family:'Malgun Gothic',sans-serif;font-size:7pt;line-height:1.12;color:#000;margin:0}"
       "h1{font-size:12pt;text-align:center;margin:0 0 4px}table{border-collapse:collapse;width:100%}"
       "td,th{border:1px solid #777;padding:0 2px;vertical-align:middle}th{background:#ddd}"
       ".info th{width:16%;text-align:left}.c{text-align:center}.n{text-align:right}.u{font-size:6.5pt;word-break:break-all}"
       ".tot td{font-weight:bold;font-size:9pt}.note{font-size:7pt;margin:4px 0}"
       ".sign{text-align:right;font-size:9pt;margin-top:4px;line-height:1.8}.p2{page-break-before:always}")
with open(FINAL_HTML, 'w', encoding='utf-8') as f:
    f.write('<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>물품 구입 신청서</title>'
            f'<style>{CSS}</style></head><body>'
            '<h1>2026학년도 동아리 학술제 물품 구입 신청서 (1차)</h1>'
            f'<table class=info>{info_html}</table><div style="height:5px"></div>'
            '<table><colgroup><col style="width:4%"><col style="width:22%"><col style="width:30%"><col style="width:4%"><col style="width:8%"><col style="width:7%"><col style="width:7%"><col style="width:10%"><col style="width:8%"></colgroup>'
            '<tr><th>번호</th><th>품명</th><th>규격</th><th>수량</th><th>단위</th><th>단가</th><th>금액</th><th>구입처</th><th>상품번호</th></tr>'
            f'{rows_html}<tr class=tot><td colspan=6 class=n>합계 (가공비 제외)</td><td class=n>{total:,}</td><td colspan=2></td></tr></table>'
            f'<p class=note>※ {E(NOTE)}</p>'
            '<div class=sign>신청자: ____________ (서명)<br>지도교사: ____________ (서명)</div>'
            '<div class=p2><h1>구입처 링크</h1><table><tr><th>번호</th><th>품명</th><th>구입처</th><th>상품 링크</th></tr>'
            f'{link_html}</table></div></body></html>')
print('final rows', len(items), 'total', total, '->', os.path.basename(FINAL), os.path.basename(FINAL_HTML))
