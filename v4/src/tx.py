"""3D프린팅 5단+후진 수동변속기 — 파라메트릭 부품 생성기 (v4)

좌표계(조립 기준): z = 축 방향(끝판 A 안쪽 면 z=0, 끝판 B 안쪽 면 z=STACK),
x = 가로(입력축 x=0, 출력축 x=99), y = 높이(MDF 윗면 y=0). 모든 치수 mm.
v3 → v4 바뀐 점 (근거는 calc/ 계산서)
  - 기어: 랙 커터 창성(트로코이드 이뿌리) + 1단·후진 17T 전위 +0.3 / 49T -0.3, 양쪽 면 1.2mm 끝 릴리프
  - 도그: PLA 돌기 → 강철 평행핀 Ø5 (기어 면에 압입) + 슬리브 면의 포켓 (층간 굽힘 제거)
  - 허브: 기어 면~기어 면 43mm 한 덩어리 (스페이서 겸용, D면 압력 낮춤)
  - 포크: 스프링 카트리지(C252 예압 26N) → 도그끼리 막혔을 때 포크에 걸리는 힘 ≤ 40N
  - 클러치: 코르크-강철 건식 단판, 밀어서 끊는 방식, 스프링 3개 (조절나사 M5x10 끝까지 조임 = 설정, 0.44~0.75N·m)
  - 모터 연결: 스프로킷 이 사이에 강철 핀 6개 (핀 커플링), 플라이휠은 입력축 끝 베어링에 지지
  - 표시 바퀴: 끝판 B 쪽(운전자 앞)으로 이동
v4.1 안전 덮개: 아크릴 3T 상자(윗판·옆판 2) + 끝 채움판 2 + 클러치 덮개(+앞판) + 축 끝 덮개 2 + 바퀴 덮개 + 덮개 스위치
  → 돌아가는 부품은 모두 덮개 안 (밖에 남는 것: 매끈한 표시 바퀴 앞면·보스, 손으로 움직이는 레버·셀렉터)
"""
import math
import numpy as np
import manifold3d as mf
from shapely.geometry import Polygon, Point, box
from shapely import affinity

mf.set_circular_segments(96)
M = mf.Manifold
CS = mf.CrossSection

# ---------------- 공차 (쿠폰 측정 후 수정) ----------------
SHAFT_HOLE = 12.30   # 12mm 축이 헐겁게 도는/미끄러지는 구멍
D_HOLE = 12.15       # D컷 축에 끼워 고정되는 구멍 지름
D_FLAT = 5.05        # D면까지 거리 (축 D컷 깊이 1mm → 축 쪽 5.0)
D_SLIDE, D_SLIDE_FLAT = 12.30, 5.15   # 클러치 디스크: D축 위에서 축방향으로 미끄러져야 함
BRG_SEAT = 28.15     # 6001 베어링 외륜 압입 구멍
BRG3_SEAT = 35.15    # 6003 베어링 외륜 압입 구멍 (같은 비율로 보정)
RAIL_HOLE = 6.35     # 6mm 레일이 미끄러지는 구멍
RAIL_CLAMP = 6.10    # 6mm 레일을 조이는 클램프 구멍
SLIDE = 0.25         # 슬리브-허브 키 한쪽 틈
IDLER_PRESS = 11.95  # 아이들러 축 압입 구멍
PIN_HOLE = 4.90      # Ø5 강철 평행핀 압입 구멍 (핀 시험 출력 후 수정)

# ---------------- 기어 ----------------
MOD, PA, BL = 3.0, math.radians(20), 0.20
FILLET = None                # v4.1: 필렛 대신 랙 창성 트로코이드 (gear_poly 참고)
RELIEF_H, RELIEF_BL = 1.2, 0.30   # 면 끝 릴리프: 높이 1.2mm 구간은 이 두께를 추가로 0.30(면당 0.15) 얇게
C = 99.0                     # 입력-출력 중심거리
H = 85.0                     # 축 높이 (MDF 윗면 기준)
FW = 25.0                    # 이 폭
PAIRS = {'1': (17, 49), '2': (22, 44), '3': (27, 39), '4': (31, 35), '5': (36, 30)}
REV = (17, 17, 41)           # 입력 17 → 아이들러 17 → 출력 41
IDLER_XY = None                 # 아래에서 전위 반영해 계산 (입력축 아래쪽)

# ---------------- 핀 도그·슬리브·허브 ----------------
PIN_D, PIN_R, PIN_N = 5.0, 35.5, 4       # Ø5 강철 평행핀 4개, 반지름 35.5
PIN_OUT, PIN_IN = 6.0, 19.0              # 기어 면 밖 돌출 6, 박힘 19 (Ø5x25 핀)
CUSH_OD = 10.0                           # 돌출부에 NBR 호스(안5 x 바깥10, 두께 2.5) 6mm 를 씌워 접착 = 쿠션 (오토바이 쿠션 드라이브와 같은 원리)
GAP0 = 3.0                               # 중립에서 핀 끝 ~ 슬리브 면 간격
TRAVEL = 8.0                             # 슬리브 이동량 (물림 5, 슬리브-기어 면 틈 1)
POCKET_DEPTH = 7.0                       # 포켓 깊이 (핀 5 물림 + 끝 여유 2)
POCKET_SWING = math.radians(20)          # 핀 중심이 포켓 안에서 움직일 수 있는 각 (±20° → 틈 40°)
POCKET_CLR = 0.15                        # 포켓 끝 반원 = 쿠션 바깥 반지름 + 0.15
SLV_HALF, GROOVE_W = 9.2, 6.6
SLV_BODY = 2 * SLV_HALF + GROOVE_W       # 25.0
SLV_R, GROOVE_R = 44.0, 39.0
HUB_CORE, HUB_KEY_R, HUB_KEYS, KEY_W = 13.0, 17.0, 6, 6.0
HUB_LEN = PIN_OUT + GAP0 + SLV_BODY + GAP0 + PIN_OUT     # 43 = 기어 면 ~ 기어 면

# ---------------- 축방향 배치 (z) ----------------
END_SP = 3.0
GROUP = FW + HUB_LEN + FW                # 93
def group_layout(z0):
    """그룹 시작 z0 → (앞 기어 z, 슬리브 중심 z, 뒤 기어 z)"""
    return z0, z0 + FW + HUB_LEN / 2, z0 + FW + HUB_LEN
# 끝판 A 쪽부터: [R S 5] [4 S 3] [2 S 1]  (운전자는 끝판 B 쪽에서 A를 바라봄)
GA = group_layout(END_SP)
GB = group_layout(END_SP + GROUP + END_SP)
GC = group_layout(END_SP + 2 * (GROUP + END_SP))
PLANE = {'R': GA[0], '5': GA[2], '4': GB[0], '3': GB[2], '2': GC[0], '1': GC[2]}
SLEEVE_Z = {'5R': GA[1], '34': GB[1], '12': GC[1]}
STACK = 3 * GROUP + 4 * END_SP                     # 291
PLATE_T = 15.0

# ---------------- 변속 레일·셀렉터 ----------------
RAIL_Y = H + 86.0
RAIL_X = {'12': 119.0, '34': 99.0, '5R': 79.0}     # 운전자 기준 왼쪽 열(1-2)이 핑거 +x
RAIL_Z0, RAIL_LEN = -15.0, STACK + 80.0             # 레일: 끝판 A 바깥면 ~ 러그 끝
LUG_Z = STACK + PLATE_T + 35.0                      # 셀렉터 러그 중심 z (중립)
LUG_W, LUG_L = 19.0, 24.0
SLOT_W, SLOT_Y0, SLOT_Y1 = 10.6, RAIL_Y + 11, RAIL_Y + 31
FINGER_Y0 = SLOT_Y0 + 8                             # 핑거 바닥 (중립)
PIVOT_Y = FINGER_Y0 + 6 + 60                        # 볼 피벗 중심
L1 = PIVOT_Y - (FINGER_Y0 + 6)                      # 피벗→핑거 중심 60
REV_PUSH = 5.5                                      # 후진 때 레버를 누르는 깊이
GATE_Y = PIVOT_Y + 84.0                             # 게이트 판 가운데 높이
GATE_T = 8.0                                        # 게이트 판 두께 (v3 6 → 8: 손잡이 400N 기준)
ROD_Y0, ROD_LEN = PIVOT_Y - 28.0, 160.0             # 12mm 강철 레버봉
CAGE_Z0, CAGE_Z1 = STACK + PLATE_T, STACK + PLATE_T + 60.0
WALL_X = ((16.0, 28.0), (170.0, 182.0))            # 케이지 옆벽 (두께 12)
PLATE_X0, PLATE_X1, PLATE_Y1 = -25.0, 182.0, 200.0  # 끝판 외곽 (207 x 200)

# ---------------- 포크 스프링 카트리지 (C252: 외경18, 자유장32, k≈2.55N/mm) ----------------
SPR_FREE, SPR_K = 32.0, 2.55
CART_PRE_L = 21.6                     # 예압 길이 → 26.5N (디바이스마트 C252 P1 값)
CART_WASH_T, CART_CAV_D = 2.5, 19.0
CART_HOLE = 13.0                      # 끝벽 구멍 (Ø12 강철 칼라가 들어감)
CART_WALL = 3.0
CART_OD = 30.0
CART_CAV_L = CART_PRE_L + 2 * CART_WASH_T            # 26.6
CART_LEN = CART_CAV_L + 2 * CART_WALL                # 32.6
CART_DIR = {'12': -1, '34': -1, '5R': +1}            # 카트리지를 기어와 안 부딪히는 쪽으로
RAIL_COLLAR = (12.0, 8.0)                            # 6mm 강철 샤프트 칼라 외경·폭 (구매품)

# ---------------- 클러치 (끝판 A 바깥, 입력축 x=0) ----------------
CL_R = 50.0                    # 앞판·뒷판·압력판 반지름
CL_STANDOFF_R = 44.0           # 기둥(M4) 원
CL_SPRING_R = 30.0             # 스프링 원 (60, 180, 300°)
CL_PUSH_R = 30.0               # 릴리스 핀(M5 볼트) 원 (0, 120, 240°)
CORK = (13.0, 25.0, 2.0)       # 코르크 링 안·바깥 반지름, 두께
WASHER = (17.0, 50.0, 3.0)     # 강철 와셔 DIN9021 M16 (안지름, 바깥지름, 두께) = 디스크
B6003 = (17.0, 35.0, 10.0)
Z_REL = (-39.0, -29.0)         # 6003 릴리스 베어링
Z_RING = (-45.0, -41.0)        # 릴리스 링 판 (보스 -41~-29)
Z_BACK = (-55.0, -48.5)        # 뒷판 6.5 (v4.1: 8 → 6.5, 릴리스 링 이동 2.5 = 누름 볼트 틈 1.0 + 압력판 1.5 뒤에도 1.0 남음)
Z_WASH = (-60.0, -57.0)        # 강철 와셔(디스크) — 코르크 사이
Z_PRESS = (-70.0, -62.0)       # 압력판 (코르크 -62~-60)
Z_FRONT = (-108.0, -92.0)      # 앞판(플라이휠): 스프링 컵 홈 깊이 9, 6001 파일럿 베어링
Z_HUB = (-88.0, -55.0)         # 디스크 허브 (외경 16.6, 플랜지 -57~-55)
SPRING_POCKET = 9.0            # 스프링 컵이 움직이는 홈 깊이. 컵 윗면 깊이 s = 13 - 조절나사 길이.
                               # 스프링 길이 = 24 + s (압력판 자리 홈 2 포함). 설정 = M5x10 끝까지 → s=3, 27mm (calc: 0.44~0.75 N·m). M5x12 이상 금지
Z_SHAFT_IN_END = Z_FRONT[0] - 1.0 - 8.0                # 입력축 끝 = 앞판 - 끝 와셔 1 - 칼라 8
CPL_PIN_R = 18.40              # 스프로킷 12T 3/8" 피치원 반지름 (03 시험 캡과 같음)
CPL_PIN_LEN = 40.0             # Ø5x40 강철 핀, 앞판에 15 박힘
Z_SPROCKET = (Z_SHAFT_IN_END - 2.0 - 8.0 - 4.3, Z_SHAFT_IN_END - 2.0 - 8.0)   # 감속기 축 끝은 스프로킷 바깥면 +8
Z_GEARHEAD_FRONT = Z_SPROCKET[1] - 15.0                # 받침 브래킷(K9B-M6) 앞판 바깥면. 스프로킷 바깥면을 여기서 15에 맞춤 (축 끝 23 실측 = 설계 일치)
MOTOR_LEN = 214.0              # 모터 뒤 ~ 브래킷 앞판 (사진 판독 약 210 → 긴 쪽 214 유지)


# ======================= 기본 도형 =======================
def cyl(r, h, z0=0.0, seg=0):
    return M.cylinder(h, r, r, seg).translate([0, 0, z0])

def tube(r_out, r_in, h, z0=0.0):
    return cyl(r_out, h, z0) - cyl(r_in, h + 2, z0 - 1)

def poly2cs(poly):
    """shapely Polygon(구멍 포함) → CrossSection"""
    polys = list(poly.geoms) if hasattr(poly, 'geoms') else [poly]
    rings = []
    for p in polys:
        rings += [list(p.exterior.coords)[:-1]] + [list(i.coords)[:-1] for i in p.interiors]
    return CS(rings, mf.FillRule.EvenOdd)

def ext(poly, h, z0=0.0):
    return poly2cs(poly).extrude(h).translate([0, 0, z0])

def boxm(x0, x1, y0, y1, z0, z1):
    return M.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def d_hole_poly(d=None, flat=None, double=True):
    """D 구멍. v4 기본 = 양면 D (축 양쪽 1mm 평면) → 토크를 두 면이 나눠 받음 (calc C4)"""
    d = d or D_HOLE; flat = flat or D_FLAT
    return Point(0, 0).buffer(d / 2, 128).intersection(box(-flat if double else -d, -d, flat, d))

def rot_x(m, deg):   return m.rotate([deg, 0, 0])
def along_x(m):      return m.rotate([0, 90, 0])      # z축 원통 → x축 원통
def along_y(m):      return m.rotate([-90, 0, 0])     # z축 원통 → y축 원통

inv = lambda a: math.tan(a) - a

XSH = {17: 0.3, 49: -0.3}    # 전위계수: 17T(1단·후진 입력, 아이들러) +0.3, 49T(1단 출력) -0.3 → 1단 쌍 중심거리 99 그대로
RACK_RHO = 0.38              # 랙 커터 끝 반지름 (×m) = 표준 호브 → 트로코이드 이뿌리 필렛이 저절로 생김

from functools import lru_cache
@lru_cache(maxsize=None)
def gear_poly(z, bl=BL, fillet=None, x=None, steps=600):
    """v4.1: 랙 커터를 굴려 깎은(창성) 인벌류트 평기어 외형. 실제 호브 가공과 같은 트로코이드 이뿌리가 생겨
    v4(직선 뿌리 + 필렛 R1.0)보다 이뿌리 응력이 낮음 (calc/fem_tooth.py: 17T 전위 +0.3 기준 약 -47%).
    bl = 이 두께 감소량(백래시), x = 전위계수(기본 XSH), fillet 인자는 예전 호출 호환용(무시).
    0번 이가 +x 축 대칭."""
    from shapely.ops import unary_union
    x = XSH.get(z, 0.0) if x is None else x
    m = MOD
    rp = m * z / 2
    ra = rp + m + x * m
    w0 = (math.pi * m / 2 + bl) / 2                     # 커터 이 반폭(기준선) → 기어 이 두께 = πm/2 - bl
    d = 1.25 * m                                         # 커터가 기준선 안쪽으로 들어가는 깊이 (= 이뿌리 깊이)
    ext_ = 12.0
    cutter = Polygon([(ext_, w0 + ext_ * math.tan(PA)), (-d, w0 - d * math.tan(PA)),
                      (-d, -(w0 - d * math.tan(PA))), (ext_, -(w0 + ext_ * math.tan(PA)))])
    r = RACK_RHO * m
    cutter = cutter.buffer(-r, 64, join_style=1).buffer(r, 64, join_style=1)
    span = 2.2 * math.pi / z + 0.35
    pieces = []
    for phi in np.linspace(-span, span, steps):
        c = affinity.translate(cutter, rp + x * m, rp * phi)
        pieces.append(affinity.rotate(c, -phi, origin=(0, 0), use_radians=True))
    space = unary_union(pieces)
    blank = Point(0, 0).buffer(ra, 720)
    sector = Polygon([(0, 0)] + [(2 * ra * math.cos(t), 2 * ra * math.sin(t))
                                 for t in np.linspace(-math.pi / z * 1.02, math.pi / z * 1.02, 40)])
    one = space.intersection(sector)
    cuts = unary_union([affinity.rotate(one, 2 * math.pi * k / z + math.pi / z, origin=(0, 0), use_radians=True)
                        for k in range(z)])
    g = blank.difference(cuts)
    g = g.buffer(-0.25, 32, join_style=1).buffer(0.25, 32, join_style=1)   # 이끝 모서리 R0.25
    return g.simplify(0.003)

def working_cd(z1, x1, z2, x2):
    """전위 기어 쌍의 물림 중심거리 (백래시 0 기준; 실제 백래시는 bl 로 얇게 깎은 만큼)"""
    a0 = MOD * (z1 + z2) / 2
    invw = inv(PA) + 2 * math.tan(PA) * (x1 + x2) / (z1 + z2)
    lo, hi = 0.2, 0.6
    for _ in range(60):
        mid = (lo + hi) / 2
        if inv(mid) < invw: lo = mid
        else: hi = mid
    return a0 * math.cos(PA) / math.cos((lo + hi) / 2)

def _idler_xy():
    a1 = working_cd(17, XSH.get(17, 0), 17, XSH.get(17, 0))      # 입력 17 - 아이들러 17
    a2 = working_cd(17, XSH.get(17, 0), 41, XSH.get(41, 0))      # 아이들러 17 - 출력 41
    xx = (a1 ** 2 - a2 ** 2 + C ** 2) / (2 * C)
    yy = math.sqrt(a1 ** 2 - xx ** 2)
    return (xx, H - yy), a1, a2
IDLER_XY, IDLER_A1, IDLER_A2 = _idler_xy()

def tip_r(z): return MOD * z / 2 + MOD * (1 + XSH.get(z, 0.0))
def root_r(z): return MOD * z / 2 - MOD * (1.25 - XSH.get(z, 0.0))

def gear_body(z):
    """이 폭 FW, 양쪽 면 RELIEF_H 구간은 이를 조금 얇게 (첫 층 눌림·면 끝 하중 집중 방지)"""
    full, thin = gear_poly(z), gear_poly(z, BL + RELIEF_BL)
    return ext(thin, RELIEF_H, 0) + ext(full, FW - 2 * RELIEF_H, RELIEF_H) + ext(thin, RELIEF_H, FW - RELIEF_H)

def pin_holes(z_face, depth, up=True):
    """기어 면(z_face)에서 안쪽으로 핀 구멍 4개"""
    s = None
    for k in range(PIN_N):
        a = 2 * math.pi * k / PIN_N
        z0 = z_face - depth if up else z_face
        c = cyl(PIN_HOLE / 2, depth + 0.01, z0 - (0.01 if up else 0)).translate([PIN_R * math.cos(a), PIN_R * math.sin(a), 0])
        s = c if s is None else s + c
    return s

def pin_solids(z_face, up=True):
    """조립 검사용 강철 핀 돌출부 (기어 면 밖)"""
    s = None
    for k in range(PIN_N):
        a = 2 * math.pi * k / PIN_N
        c = cyl(CUSH_OD / 2, PIN_OUT, z_face if up else z_face - PIN_OUT).translate([PIN_R * math.cos(a), PIN_R * math.sin(a), 0])
        s = c if s is None else s + c
    return s


# ======================= 부품 (출력 방향 = 그대로 프린트) =======================
def fixed_gear(z):
    """입력축 기어: D구멍으로 축에 고정"""
    return gear_body(z) - ext(d_hole_poly(), FW + 2, -1)

def free_gear(z, pins=True):
    """출력축 공회전 기어: 양쪽 6001 베어링 2개, 윗면(z=FW)에 핀 구멍 4개 (핀이 위로)"""
    g = gear_body(z)
    g -= cyl(BRG_SEAT / 2, 8.0 + 0.01, -0.01)           # 아래 베어링 자리
    g -= cyl(BRG_SEAT / 2, 8.0 + 0.01, FW - 8.0)        # 위 베어링 자리
    g -= cyl(11.0, FW + 2, -1)                          # 가운데 턱 (외륜만 닿음, 내경 22)
    g -= M.cylinder(3.0, BRG_SEAT / 2, 11.0).translate([0, 0, 8.0])  # 아래쪽 45° 모따기 → 오버행 없음
    if pins:
        g -= pin_holes(FW, PIN_IN, up=True)
    return g

def idler_gear():
    return free_gear(REV[1], pins=False)

HUB_BODY = HUB_LEN - 2.0            # 허브 몸통 41 + 양 끝 1mm 와셔(외경 15) → 와셔만 베어링 내륜에 닿음
def hub():
    """슬리브 허브 (몸통 41): 양면 D구멍, 바깥 키 6개 (끝까지 같은 단면 → 세워서 서포트 없이 출력)"""
    p = Point(0, 0).buffer(HUB_CORE, 128)
    for k in range(HUB_KEYS):
        key = affinity.rotate(box(0, -KEY_W / 2, HUB_KEY_R, KEY_W / 2), 360 * k / HUB_KEYS, origin=(0, 0))
        p = p.union(key)
    return ext(p.difference(d_hole_poly()), HUB_BODY)

def sleeve_inner_poly():
    p = Point(0, 0).buffer(HUB_CORE + SLIDE, 128)
    for k in range(HUB_KEYS):
        key = affinity.rotate(box(0, -KEY_W / 2 - SLIDE, HUB_KEY_R + SLIDE + 0.15, KEY_W / 2 + SLIDE), 360 * k / HUB_KEYS, origin=(0, 0))
        p = p.union(key)
    return p

BOLT_R = 23.5   # 슬리브 결합 볼트 원 (키 홈 r17.25 ~ 포켓 r30.35 사이, 육각 자리 벽 3 이상)
BOLT_HEX = (6.2, 4.0)   # 슬리브 반쪽 바깥면 육각 자리 (맞변 6.2, 깊이 4): 한쪽은 M3 머리(유두 Ø5.7 도 들어감), 반대쪽은 너트(맞변 5.5, 못 돎) → 면 아래 1.0 에 숨음 (M3x20)
def _bolts(h, z0, d=3.4):
    s = None
    for k in range(3):
        a = math.radians(30 + 120 * k)
        c = cyl(d / 2, h + 2, z0 - 1).translate([BOLT_R * math.cos(a), BOLT_R * math.sin(a), 0])
        s = c if s is None else s + c
    return s

def pocket_poly():
    """핀이 들어가는 포켓 4개 (반지름 PIN_R 원호 ±POCKET_SWING + 끝 반원)"""
    rr = CUSH_OD / 2 + POCKET_CLR
    s = None
    for k in range(PIN_N):
        c0 = 2 * math.pi * k / PIN_N
        arc = [(PIN_R * math.cos(c0 + t), PIN_R * math.sin(c0 + t)) for t in np.linspace(-POCKET_SWING, POCKET_SWING, 25)]
        from shapely.geometry import LineString
        p = LineString(arc).buffer(rr, 32)
        s = p if s is None else s.union(p)
    return s

def sleeve_half():
    """슬리브 반쪽(2개 출력): 두께 9.2, 바깥 면에 핀 포켓 4개 깊이 7 + 볼트 육각 자리 3 (포켓 면이 위로 출력)"""
    body = ext(Point(0, 0).buffer(SLV_R, 128).difference(sleeve_inner_poly()), SLV_HALF)
    body -= ext(pocket_poly(), POCKET_DEPTH + 0.01, SLV_HALF - POCKET_DEPTH)
    body -= ext(pocket_poly().buffer(0.8, 16), 0.8 + 0.01, SLV_HALF - 0.8)    # 입구 모따기 근사 (0.8 계단)
    body -= _bolts(SLV_HALF, 0)
    for k in range(3):                                                         # v4.1: 머리·너트가 기어 면에 닿지 않게 숨김
        a = math.radians(30 + 120 * k)
        hx = ext(hexagon(BOLT_HEX[0]), BOLT_HEX[1] + 0.01, SLV_HALF - BOLT_HEX[1])
        body -= hx.translate([BOLT_R * math.cos(a), BOLT_R * math.sin(a), 0])
    return body

def sleeve_ring():
    """슬리브 가운데 링 = 포크 홈 바닥 (반지름 39, 두께 6.6)"""
    r = ext(Point(0, 0).buffer(GROOVE_R, 128).difference(sleeve_inner_poly()), GROOVE_W)
    return r - _bolts(GROOVE_W, 0)

def spacer(length, r_out=7.5):
    """베어링 내륜만 누르는 스페이서 (6001 내륜 어깨 ≈ 지름 16.7 → 외경 15)"""
    return tube(r_out, SHAFT_HOLE / 2, length)

def collar(bore=SHAFT_HOLE - 0.2, w=10.0, r=13.0):
    """M3 조임 칼라 (v4.1): 슬릿 + M3x12 머리 자리(바닥 x=-3, 머리가 반지름 r 안으로 숨음) + 반대쪽 자가탭 Ø2.5.
    너트 없음 → 밖으로 튀어나온 것 없음 (v4 는 너트가 칼라 밖으로 3mm 튀어나와 덮개·커플링 핀에 닿았음)"""
    yb = 8.5
    c = tube(r, bore / 2, w)
    c -= boxm(-0.75, 0.75, 0, r + 1, -1, w + 1)                                  # 슬릿
    c -= along_x(cyl(1.7, r + 1, -r - 1)).translate([0, yb, w / 2])              # 머리 쪽 Ø3.4
    c -= along_x(cyl(3.1, r, -r - 3)).translate([0, yb, w / 2])                  # 머리 자리 Ø6.2
    c -= along_x(cyl(1.25, r + 1, 0)).translate([0, yb, w / 2])                  # 자가탭 Ø2.5
    return c


# ======================= 시험편 =======================
def coupon():
    """한 장으로 구멍 공차를 모두 확인: 베어링 4종, 12mm 3종, D구멍 3종, 6mm 3종 (v3와 같음)"""
    base = boxm(0, 150, 0, 60, 0, 8)
    holes = []
    for i, d in enumerate([27.9, 28.05, 28.2, 28.35]):
        holes.append(cyl(d / 2, 10, -1).translate([18 + 34 * i, 40, 0]))
    for i, d in enumerate([12.1, 12.3, 12.5]):
        holes.append(cyl(d / 2, 10, -1).translate([12 + 17 * i, 13, 0]))
    for i, d in enumerate([12.0, 12.15, 12.3]):          # 한쪽 D (이미 출력한 v3 쿠폰과 같게)
        holes.append(ext(d_hole_poly(d, d / 2 - 1.0 + 0.05, double=False), 10, -1).translate([66 + 17 * i, 13, 0]))
    for i, d in enumerate([6.1, 6.35, 6.6]):
        holes.append(cyl(d / 2, 10, -1).translate([118 + 11 * i, 13, 0]))
    for h in holes: base -= h
    return base

def fit_test():
    """허브-슬리브 미끄럼 맞춤 시험 (높이 6): v3와 같은 키 단면"""
    p = Point(0, 0).buffer(HUB_CORE, 128)
    for k in range(HUB_KEYS):
        p = p.union(affinity.rotate(box(0, -KEY_W / 2, HUB_KEY_R, KEY_W / 2), 360 * k / HUB_KEYS, origin=(0, 0)))
    hub6 = ext(p.difference(d_hole_poly()), 6.0)
    ring = ext(Point(0, 0).buffer(24.0, 128).difference(sleeve_inner_poly()), 6.0).translate([55, 0, 0])
    return hub6 + ring

def pin_fit_test():
    """강철 핀·6003 도착 후 시험: Ø5 핀 압입 구멍 4.8/4.9/5.0, 6003 자리 34.9/35.05/35.2, 깊이 14"""
    base = boxm(0, 130, 0, 40, 0, 15)
    for i, d in enumerate([4.8, 4.9, 5.0]):
        base -= cyl(d / 2, 14.01, 1.0).translate([10 + 10 * i, 10, 0])
    for i, d in enumerate([34.9, 35.05, 35.2]):
        base -= cyl(d / 2, 16, -0.5).translate([50 + 38 * i, 21, 0])
    return base


# ======================= 조립 좌표로 만드는 부품 =======================
def _m3_pinch(center, axis, length):
    c = cyl(1.7, length, -length / 2)
    if axis == 'x': c = along_x(c)
    if axis == 'y': c = along_y(c)
    return c.translate(list(center))

def _m4(x, y, z0, t=PLATE_T):
    return cyl(2.2, t + 2, z0 - 1).translate([x, y, 0])

# ---------------- v4.1 안전 덮개 (아크릴 3T + 출력 부품) ----------------
COVER_X0, COVER_X1, COVER_T = -65.0, 185.0, 3.0     # 왼쪽 판 바깥면 x=-65 (입력 기어 끝 x=-57 보다 바깥), 오른쪽 판 바깥면 185
COVER_TOP_X = (20.0, 140.0)                          # 끝판 윗면 나사 x
COVER_SIDE_Y = (50.0, 160.0)                         # 끝판 오른쪽 면 나사 y
FILLER_Y = (40.0, 160.0)                             # 끝판 왼쪽 면 ~ 끝 채움판 연결 나사 y
FILLER_SIDE_Y = (70.0, 180.0)                        # 끝 채움판 왼쪽 면 (아크릴 왼쪽 판) 나사 y
HOOD_TABS = ((72.0, 40.0), (72.0, 150.0))            # 클러치 덮개 오른쪽 탭 → 끝판 A (5-R 레일 끝 y171 피함)
CAP_TABS = ((99.0, 63.0), (99.0, 107.0))             # 축 끝 덮개 탭: 끝판 A 출력축
CAP_TABS_B = ((0.0, 63.0), (0.0, 107.0))             # 축 끝 덮개 탭: 끝판 B 입력축 (같은 부품을 뒤집어 씀)
GUARD_TABS = ((64.0, 128.0), (134.0, 128.0))         # 바퀴 덮개 위쪽 탭 → 끝판 B 바깥면 (아래쪽은 RPM_BRK_HOLES)
SW_NOTCH = (179.0, 176.0, 180.0)                     # 덮개 스위치(끝판 A 안쪽 면에 접착) 전선 통로: 오른쪽 모서리 x179~182, y176~180
HOOD_Z = (-135.0, -15.0)                             # 클러치 덮개 z. 앞판(3) 바깥면 -138 ~ 감속기 앞면 -142 = 4mm 틈 (손끝이 안 들어감)
HOOD_TOP = 195.0

PLATE_WINDOWS = {
    'A': [],      # v4.1: 끝판 A 도 덮개의 끝 벽 → 창 없음 (A 쪽에서 기어로 손가락이 들어가지 않게)
    'B': [],      # v4: 끝판 B 는 덮개의 끝 벽 → 창 없음 (손가락이 들어가지 않게)
}
CAGE_BOLTS = ((40.0, 150.0), (158.0, 150.0), (40.0, 192.0), (158.0, 192.0))
FORK_BRK_HOLES = ((-17.0, 112.0), (17.0, 112.0), (-17.0, 168.0), (17.0, 168.0))   # 클러치 포크 브래킷 M4 (끝판 A)
RPM_BRK_HOLES = ((91.0, 14.0), (107.0, 14.0))                                       # rpm 센서 브래킷 M3 (끝판 B)

def end_plate(side):
    """끝판 A(z -15~0, 아이들러 축, 클러치 포크 브래킷) / B(z STACK~STACK+15, 셀렉터 케이지, rpm 센서)"""
    z0 = -PLATE_T if side == 'A' else STACK
    inner = 0.0 if side == 'A' else STACK
    p = boxm(PLATE_X0, PLATE_X1, 0, PLATE_Y1, z0, z0 + PLATE_T)     # v4.1: 모서리 둥글림 없앰 → 아크릴 판과 틈 없이 맞닿음
    for x in (0.0, C):
        p -= cyl(8.0, PLATE_T + 2, z0 - 1).translate([x, H, 0])                      # 축 통과 16
        zs = inner - 8.0 if side == 'A' else inner
        p -= cyl(BRG_SEAT / 2, 8.0 + 0.01, zs - (0.01 if side == 'A' else 0)).translate([x, H, 0])  # 베어링 자리
    for xr in RAIL_X.values():
        p -= cyl(RAIL_HOLE / 2, PLATE_T + 2, z0 - 1).translate([xr, RAIL_Y, 0])
    for xb in (-12.0, 165.0):                                                        # 받침 브래킷 M4
        p -= _m4(xb, 14.0, z0)
    for (x0, y0, x1, y1) in PLATE_WINDOWS[side]:
        w = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]).buffer(-8).buffer(8)
        p -= ext(w, PLATE_T + 2, z0 - 1)
    if side == 'A':
        p -= cyl(IDLER_PRESS / 2, PLATE_T + 2, z0 - 1).translate([IDLER_XY[0], IDLER_XY[1], 0])
        for (xb, yb) in FORK_BRK_HOLES:
            p -= _m4(xb, yb, z0)
            p -= boxm(xb - 3.6, xb + 3.6, yb - 3.2, yb + 3.2, z0 + PLATE_T - 4.0, z0 + PLATE_T + 1)  # 안쪽 면 M4 너트 홈
    else:
        for (xb, yb) in CAGE_BOLTS:
            p -= _m4(xb, yb, z0)
        for (xb, yb) in RPM_BRK_HOLES:
            p -= cyl(1.3, PLATE_T + 2, z0 - 1).translate([xb, yb, 0])
    # v4.1 덮개: 윗면 나사(M3 자가탭 Ø2.5 깊이 12) x=20,140 / 오른쪽 면 y=50,160 / 왼쪽 면(끝 채움판) y=40,160
    zm = z0 + PLATE_T / 2
    for xt in COVER_TOP_X:
        p -= along_y(cyl(1.25, 12.01, -12.0)).translate([xt, PLATE_Y1 + 0.01, zm])
    for yr in COVER_SIDE_Y:
        p -= along_x(cyl(1.25, 12.01, -12.0)).translate([PLATE_X1 + 0.01, yr, zm])
    for yl in FILLER_Y:                                                              # 끝 채움판 M3x50 (끝 17mm 가 끝판에 들어감)
        p -= along_x(cyl(1.25, 18.01, 0.0)).translate([PLATE_X0 - 0.01, yl, zm])
    if side == 'A':
        for (xh, yh) in HOOD_TABS + CAP_TABS:                                         # 클러치 덮개·출력 칼라 덮개 (바깥면에서 M3 자가탭)
            p -= cyl(1.25, 12.01, z0 - 0.01).translate([xh, yh, 0])
        xn, yn0, yn1 = SW_NOTCH
        p -= boxm(xn, PLATE_X1 + 1, yn0, yn1, z0 - 1, z0 + PLATE_T + 1)
    else:
        for (xh, yh) in CAP_TABS_B + GUARD_TABS:                                      # 입력축 끝 덮개·바퀴 덮개 (바깥면에서 M3 자가탭)
            p -= cyl(1.25, 12.01, z0 + PLATE_T - 12.0).translate([xh, yh, 0])
    # 클러치 케이블 아우터 통로 (0, CABLE_Y): B 는 관통 Ø6, A 는 안쪽에서 Ø6 깊이 12 + 속선 Ø2.4
    cx, cy = 0.0, H + 92.0
    if side == 'A':
        p -= cyl(3.0, 12.0 + 0.01, -12.0).translate([cx, cy, 0])
        p -= cyl(1.2, PLATE_T + 2, z0 - 1).translate([cx, cy, 0])
    else:
        p -= cyl(3.0, PLATE_T + 2, z0 - 1).translate([cx, cy, 0])
    return p

def plate_spacer():
    return spacer(9.0)

def foot_bracket():
    """끝판 바깥면-MDF 연결 L 브래킷 (출력: L자 단면이 바닥)"""
    prof = Polygon([(0, 0), (40, 0), (40, 6), (6, 6), (6, 30), (0, 30)])
    b = ext(prof, 30)
    b -= along_x(cyl(2.2, 10, -1)).translate([-2, 14, 15])          # v4.1: 끝판 구멍 높이 14 와 맞춤 (v3 은 16 → 2mm 어긋남)
    for zz in (8.0, 22.0):
        b -= along_y(cyl(2.2, 10, -1)).translate([26, -2, zz])
    return b

# ---------------- 시프트 포크 (스프링 카트리지) ----------------
def cart_span(g):
    """카트리지 하우징 z 범위 (포크 판은 하우징의 한쪽 끝)"""
    zc = SLEEVE_Z[g]
    if CART_DIR[g] > 0:
        return zc - 3.0, zc - 3.0 + CART_LEN
    return zc + 3.0 - CART_LEN, zc + 3.0

def fork(group):
    """포크: 홈(반지름 39~44)에 들어가는 립(두께 6) + 홈 밖 두꺼운 링(반지름 44.5~52)과 팔(두께 13, 카트리지 쪽으로만 두꺼움)
    + 레일 위 스프링 카트리지 컵. 축방향 힘(≤40N)에 대한 판 굽힘을 견디려고 v3(6mm)보다 두껍게 (calc C8).
    출력 방향: 립 면이 바닥(카트리지 쪽이 위) → 서포트 없음"""
    xr = RAIL_X[group]; zc = SLEEVE_Z[group]; dr = CART_DIR[group]
    lip = Point(0, 0).buffer(44.6, 128).difference(Point(0, 0).buffer(GROOVE_R + 0.6, 128))
    ring = Point(0, 0).buffer(52.0, 128).difference(Point(0, 0).buffer(44.6, 128))
    half = box(-60, 0, 60, 60)
    pads = Point(-43.8, 0).buffer(4.2).union(Point(43.8, 0).buffer(4.2))
    lip = affinity.translate(lip.intersection(half).union(pads.intersection(Point(0, 0).buffer(44.6, 64))), C, H)
    ring = affinity.translate(ring.intersection(half).union(Point(-48.3, 0).buffer(3.7)).union(Point(48.3, 0).buffer(3.7)), C, H)
    p0, p1 = np.array([C, H + 49.0]), np.array([xr, RAIL_Y])
    d = p1 - p0; n = np.array([-d[1], d[0]]) / np.linalg.norm(d) * 6.0
    arm = Polygon([p0 + n, p1 + n, p1 - n, p0 - n])
    thick = ring.union(arm).difference(Point(xr, RAIL_Y).buffer(CART_OD / 2 - 0.5))
    za, zb = cart_span(group)
    if dr > 0:
        f = ext(lip, 6.0, zc - 3.0) + ext(thick, 13.0, zc - 3.0)
    else:
        f = ext(lip, 6.0, zc - 3.0) + ext(thick, 13.0, zc + 3.0 - 13.0)
    cup = cyl(CART_OD / 2, CART_LEN - CART_WALL, 0) - cyl(CART_CAV_D / 2, CART_LEN, CART_WALL) - cyl(CART_HOLE / 2, CART_LEN + 2, -1)
    for k in (0, 1):                                                       # 뚜껑 M3 자가탭 2개 (Ø2.5)
        a = math.pi / 2 + math.pi * k
        cup -= cyl(1.25, 12, CART_LEN - CART_WALL - 11).translate([12.25 * math.cos(a), 12.25 * math.sin(a), 0])
    if dr > 0:
        cup = cup.translate([xr, RAIL_Y, za])
    else:
        cup = cup.mirror([0, 0, 1]).translate([xr, RAIL_Y, zb])
    return f + cup

def fork_cap(group=None):
    """카트리지 뚜껑 (출력용: 원점 기준 z 0~3)"""
    c = tube(CART_OD / 2, CART_HOLE / 2, CART_WALL)
    for k in (0, 1):
        a = math.pi / 2 + math.pi * k
        c -= cyl(1.7, 5, -1).translate([12.25 * math.cos(a), 12.25 * math.sin(a), 0])
    return c

def cap_placed(group):
    xr = RAIL_X[group]; za, zb = cart_span(group)
    c = fork_cap()
    if CART_DIR[group] > 0:
        return c.translate([xr, RAIL_Y, zb - CART_WALL])
    return c.translate([xr, RAIL_Y, za])

def cart_washer():
    return tube(CART_CAV_D / 2 - 0.2, 3.2, CART_WASH_T)

def cart_inner_z(group):
    """카트리지 안쪽 공간 (와셔 바깥면) z 범위"""
    za, zb = cart_span(group)
    return za + CART_WALL, zb - CART_WALL

def lug(group):
    """셀렉터 러그: 레일에 M3 두 개로 고정, 위가 열린 홈(핑거·잠금판이 지나감)"""
    xr = RAIL_X[group]
    g = boxm(xr - LUG_W / 2, xr + LUG_W / 2, RAIL_Y - 8, SLOT_Y1, LUG_Z - LUG_L / 2, LUG_Z + LUG_L / 2)
    g -= boxm(xr - 20, xr + 20, SLOT_Y0, SLOT_Y1 + 1, LUG_Z - SLOT_W / 2, LUG_Z + SLOT_W / 2)
    g -= cyl(RAIL_HOLE / 2, 40, LUG_Z - 20).translate([xr, RAIL_Y, 0])
    for dz in (-9.0, 9.0):
        g -= along_y(cyl(1.3, 40, 0)).translate([xr, RAIL_Y, LUG_Z + dz])
        g -= along_y(cyl(3.2, 4, 0)).translate([xr, SLOT_Y1 - 3.5, LUG_Z + dz])
    for dz in (-TRAVEL, 0.0, TRAVEL):
        g -= M.cylinder(1.4, 2.6, 0.0).rotate([-90, 0, 0]).translate([xr, RAIL_Y - 8 - 0.01, LUG_Z + dz])
    g -= along_y(cyl(3.1, 3.3, 0)).translate([xr + 5.5, RAIL_Y - 8 - 0.01, LUG_Z])
    return g

def finger_x(group): return RAIL_X[group]
def gate_x(group): return C + (C - RAIL_X[group]) * (GATE_Y - PIVOT_Y) / L1
GATE_DZ = TRAVEL * (GATE_Y - PIVOT_Y) / L1

def cage():
    """셀렉터 케이지 (출력: 플랜지 면이 바닥, z 방향으로 60 쌓기)"""
    zA, zB = CAGE_Z0, CAGE_Z1
    c = boxm(WALL_X[0][0], WALL_X[1][1], 140, PLATE_Y1, zA, zA + 8)
    for (x0, x1) in WALL_X:
        c += boxm(x0, x1, 140, GATE_Y - GATE_T / 2, zA, zB)
    c += boxm(62, 136, 144, 161, zA, zB)
    c += boxm(WALL_X[0][0], 62, 140, 150, zA, zB) + boxm(136, WALL_X[1][1], 140, 150, zA, zB)
    for xr in RAIL_X.values():
        c -= cyl(RAIL_HOLE / 2 + 0.15, 20, zA - 5).translate([xr, RAIL_Y, 0])
        c -= along_y(cyl(3.15, 13, 0)).translate([xr, 149, LUG_Z])
        c -= along_y(cyl(1.3, 8, 0)).translate([xr, 143, LUG_Z])
        for dz in (-TRAVEL, TRAVEL):
            sx, sz = xr + 5.5, LUG_Z + dz
            c -= boxm(sx - 2.2, sx + 2.2, 161 - 1.8, 162, sz - 1.7, sz + 1.7)
            c -= boxm(sx - 2.0, sx + 2.0, 143, 162, sz - 0.6, sz + 0.6)
    for (xb, yb) in CAGE_BOLTS:
        c -= _m4(xb, yb, zA - 1, 12)
        c -= cyl(4.2, 60, zA + 8).translate([xb, yb, 0])
    for y in (PIVOT_Y - 9, PIVOT_Y + 9):
        for zz in (LUG_Z - 15, LUG_Z + 15):
            c -= along_x(cyl(2.2, 400, -200)).translate([0, y, zz])
    gb = GATE_Y - GATE_T / 2
    for (x0, x1) in WALL_X:
        x = (x0 + x1) / 2; out = x0 if x < C else x1
        for zz in (zA + 12, zB - 12):
            c -= along_y(cyl(2.2, 30, 0)).translate([x, gb - 25, zz])
            c -= boxm(min(x, out) - 1 if x < C else x - 3.6, max(x, out) + 1 if x > C else x + 3.6,
                      gb - 17, gb - 13.6, zz - 3.6, zz + 3.6)
    return c

# ---------------- 레버 기구 ----------------
FINGER_YC = FINGER_Y0 + 6.0
PIVOT = np.array([C, PIVOT_Y, LUG_Z])

def lever_rot(dx, dz):
    a = math.asin(dx / L1); b = -math.asin(dz / L1)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    return Rz @ Rx

def lever_point(dx, dz, local_y, push=0.0):
    return PIVOT + lever_rot(dx, dz) @ np.array([0.0, local_y - push, 0.0])

WIN = 12.8
FINGER_HALF = 10.63
def carrier():
    zc = LUG_Z
    plate = boxm(-46.0, 46.0, SLOT_Y0 + 0.3, 204.0, zc - 5.0, zc + 5.0)
    plate -= boxm(-WIN, WIN, SLOT_Y0, 204.5, zc - 6, zc + 6)
    bridge = boxm(-22, 22, 204.0, 211.0, zc - 20, zc + 20)
    bridge -= boxm(-15.5, 15.5, 203, 212, zc - 13, zc + 13)
    return plate + bridge

def lower_lever():
    zc = LUG_Z
    fin = along_x(cyl(5.0, LUG_W, -LUG_W / 2)).translate([C, FINGER_YC, zc])
    sock_y0 = PIVOT_Y - BALL_R - 14.0
    neck = boxm(C - 7, C + 7, FINGER_YC, sock_y0 + 1, zc - 3, zc + 3)
    sock = along_y(cyl(7.5, 14.0, 0)).translate([C, sock_y0, zc])
    sock -= along_y(cyl(6.15, 13, 0)).translate([C, ROD_Y0, zc])
    fin -= boxm(C - 20, C + 20, FINGER_YC - 6, FINGER_YC - 4.4, zc - 6, zc + 6)
    return fin + neck + sock

BALL_R = 16.0
def pivot_half(upper):
    x0, x1 = WALL_X[0][1], WALL_X[1][0]
    y0, y1 = (PIVOT_Y, PIVOT_Y + 18) if upper else (PIVOT_Y - 18, PIVOT_Y)
    b = boxm(x0, x1, y0, y1, LUG_Z - 25, LUG_Z + 25)
    b -= M.sphere(BALL_R + 0.25, 128).translate(list(PIVOT))
    if upper:
        b -= M.cylinder(18.01, 15.0, 19.5).rotate([-90, 0, 0]).translate([C, PIVOT_Y, LUG_Z])
    else:
        b -= M.cylinder(10.4, 17.4, 13.5).rotate([-90, 0, 0]).translate([C, PIVOT_Y - 19, LUG_Z])
    yb = PIVOT_Y + 9 if upper else PIVOT_Y - 9
    for zz in (LUG_Z - 15, LUG_Z + 15):
        for xe, sgn in ((x0, 1), (x1, -1)):
            b -= along_x(cyl(2.2, 30, 0)).translate([xe - 1 if sgn > 0 else xe - 29, yb, zz])
            nx = xe + sgn * 12
            b -= boxm(nx - 1.8, nx + 1.8, yb - 3.6, (y1 + 1) if upper else yb + 3.6, zz - 3.6, zz + 3.6) if upper else \
                 boxm(nx - 1.8, nx + 1.8, y0 - 1, yb + 3.6, zz - 3.6, zz + 3.6)
    return b

def ball_half(upper):
    s = M.sphere(BALL_R, 128) - along_y(cyl(6.15, 40, -20))
    keep = boxm(-20, 20, 0, 20, -20, 20) if upper else boxm(-20, 20, -20, 0, -20, 20)
    return (s ^ keep).translate(list(PIVOT))

SPACER_L = 30.0
def spring_spacer():
    y0 = PIVOT_Y + math.sqrt(BALL_R ** 2 - 6.2 ** 2)
    return along_y(tube(8.0, 6.2, SPACER_L)).translate([C, y0, LUG_Z]), y0 + SPACER_L

LOCK_RHO = GATE_Y - GATE_T / 2 - 0.6 - PIVOT_Y
LIP_Y0 = GATE_Y - GATE_T / 2 - 8.0
def lock_collar():
    c = along_y(collar(bore=12.1, w=9.0, r=14.0)).translate([C, PIVOT_Y + LOCK_RHO - 8.5, LUG_Z])
    return c ^ M.sphere(LOCK_RHO, 256).translate(list(PIVOT))

def lever_paths(step=1.0):
    xs = sorted(RAIL_X[g] - C for g in RAIL_X)
    paths = [[(x, 0.0) for x in np.arange(xs[0], xs[-1] + 1e-6, step)]]
    for x in xs:
        paths.append([(x, z) for z in np.arange(-TRAVEL, TRAVEL + 1e-6, step)])
    return paths

def _rod_seg(dx, dz, y0, y1, r):
    p0, p1 = lever_point(dx, dz, y0 - PIVOT_Y), lever_point(dx, dz, y1 - PIVOT_Y)
    d = p1 - p0; L = np.linalg.norm(d); u = d / L
    c = cyl(r, L, 0)
    ax = np.cross([0, 0, 1], u); s = np.linalg.norm(ax)
    if s > 1e-9:
        ang = math.atan2(s, u[2]); k = ax / s
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        Rm = np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K
        A = np.zeros((3, 4)); A[:, :3] = Rm; A[:, 3] = p0
        return c.transform(A)
    return c.translate(list(p0))

def swept(y0, y1, r, step=1.0):
    parts = []
    for path in lever_paths(step):
        segs = [_rod_seg(dx, dz, y0, y1, r) for dx, dz in path]
        for a, b in zip(segs, segs[1:]):
            parts.append(M.batch_hull([a, b]))
    return M.batch_boolean(parts, mf.OpType.Add)

def gate():
    """H 게이트 판 (두께 GATE_T): 레버봉이 실제로 지나가는 자리 + 0.8 여유를 파냄. 후진 칸 앞 턱."""
    x0, x1 = WALL_X[0][0], WALL_X[1][1]
    g = boxm(x0, x1, GATE_Y - GATE_T / 2, GATE_Y + GATE_T / 2, CAGE_Z0 + 3, CAGE_Z1 + 3)
    xR = gate_x('5R')
    g += boxm(xR - 12, xR + 18, LIP_Y0, GATE_Y - GATE_T / 2, LUG_Z + 17.2, CAGE_Z1 + 3)
    g -= swept(LIP_Y0 - 8, GATE_Y + GATE_T + 10, 6.8)
    for (wx0, wx1) in WALL_X:
        x = (wx0 + wx1) / 2
        for zz in (CAGE_Z0 + 12, CAGE_Z1 - 12):
            g -= along_y(cyl(2.2, 24, 0)).translate([x, GATE_Y - 12, zz])
    return g

def knob():
    y0 = ROD_Y0 + ROD_LEN - 15.0
    k = cyl(17.0, 25.0, 0) + M.cylinder(4.0, 17.0, 14.0).translate([0, 0, 25.0])
    k -= cyl(6.15, 15.2, -0.2)
    for x in (-8.0, 0.0, 8.0):
        k -= boxm(x - 0.8, x + 0.8, -6, 6, 28.2, 30)
    k -= boxm(-8.8, 8.8, -0.8, 0.8, 28.2, 30)
    return along_y(k).translate([C, y0, LUG_Z])

# ---------------- 출력축 표시 바퀴 (끝판 B 바깥, 운전자 앞) ----------------
WHEEL_R, WHEEL_T = 48.0, 6.0
Z_WHEEL = STACK + PLATE_T + 12.0 + 3.0        # 칼라 바깥 (칼라 끝 STACK+27) + 3
GUARD_R = (WHEEL_R + 2.5, WHEEL_R + 5.5)      # 바퀴 덮개 링 안·바깥 반지름 (바퀴 테와 2.5 틈: 손끝이 안 들어감)
def display_wheel():
    """v4.1: 살 구멍 없는 원판 (손가락이 끼일 구멍 없음), 회전이 보이게 앞면에 홈 1 (깊이 1).
    보스 바깥쪽 M3 무두볼트(자가탭 Ø2.5) 1 이 D면을 눌러 고정. 테에 자석 Ø6x3 4개 (90° 간격, 테와 같은 높이로 접착)"""
    w = cyl(WHEEL_R, WHEEL_T) + cyl(13.0, 4.0, WHEEL_T)
    w -= ext(d_hole_poly(), WHEEL_T + 6, -1)
    w -= boxm(14.0, WHEEL_R - 4.0, -1.5, 1.5, WHEEL_T - 1.0, WHEEL_T + 0.01)
    w -= along_x(cyl(1.25, 9.0, 0)).translate([4.5, 0, WHEEL_T + 2.0])
    for k in range(4):                                       # 자석 4개 (90° 간격): 느리게 돌아도 막힘 감시가 펄스를 놓치지 않음
        w -= along_y(cyl(3.1, 3.1, 0)).translate([0, -WHEEL_R - 0.01, WHEEL_T / 2]).rotate([0, 0, 90 * k])
    return w

def wheel_guard():
    """바퀴 덮개 (v3 rpm 센서 받침 대신, 조립 좌표). 끝판 B 바깥면 ~ 바퀴 앞면까지 링(r50.5~53.5) →
    바퀴 뒤 칼라·축과 바퀴 테가 모두 덮임. 링 아래쪽 안쪽 벽에 A3144 자리(평면이 위, 자석과 2.5 틈) + 다리 통로.
    고정: 아래 받침 M3 2 (RPM_BRK_HOLES) + 위 탭 M3 2 (GUARD_TABS). 출력: 끝판 쪽 면이 바닥"""
    zo = STACK + PLATE_T
    zf = Z_WHEEL + WHEEL_T
    zw = Z_WHEEL + WHEEL_T / 2
    r0, r1 = GUARD_R
    g = tube(r1, r0, zf - zo, zo).translate([C, H, 0])
    g += boxm(84, 114, 4, H - r0 - 1.0, zo, zo + 6)
    for (xb, yb) in RPM_BRK_HOLES:
        g -= cyl(1.7, 10, zo - 2).translate([xb, yb, 0])
    for (xt, yt) in GUARD_TABS:
        g += boxm(xt - 6, xt + 6, yt - 6, yt + 6, zo, zo + 4) - cyl(1.7, 6, zo - 1).translate([xt, yt, 0])
    ys = H - r0
    g -= boxm(C - 2.2, C + 2.2, ys - 1.8, ys + 0.01, zw - 1.7, zw + 1.7)
    g -= boxm(C - 2.0, C + 2.0, H - r1 - 1.0, ys, zw - 0.6, zw + 0.6)
    return g


# ======================= 클러치 =======================
# 각도 배치 (앞판에서 핀 6개 15+60k 와 스프링 홈이 30° 이상 떨어지도록)
SPRING_A = (45.0, 165.0, 285.0)
STANDOFF_A = (105.0, 225.0, 345.0)
PUSH_A = STANDOFF_A                       # 릴리스 볼트(r30)는 기둥(r44)과 같은 각, 반지름만 다름
CPL_PIN_A = tuple(15.0 + 60.0 * k for k in range(6))   # 스프로킷 이 사이 12곳 중 6곳 (03 시험 캡과 같은 15° 위상)

def _ring_pts(r, angles_deg):
    return [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in angles_deg]

def _at(m, x, y):
    return m.translate([x, y, 0])

def hexagon(af):
    """맞변 거리 af 육각형 (너트 홈)"""
    R = af / math.sqrt(3)
    return Polygon([(R * math.cos(math.radians(60 * k)), R * math.sin(math.radians(60 * k))) for k in range(6)])

def cl_front():
    """앞판(플라이휠). 로컬 z=0 = 모터 쪽 면(조립 Z_FRONT[0]), z=16 = 스프링 쪽 면. 출력: z=0 면이 바닥.
    6001 파일럿 베어링(모터 쪽에서 넣음, 뒤 턱 안지름 22) / Ø5 강철 핀 구멍 6 (깊이 15) /
    기둥 M4 3 (머리 자리) / 스프링 컵 홈 Ø20 깊이 9 + M5 조절나사 + M5 너트 홈(둘레에서 밀어넣음)"""
    T = Z_FRONT[1] - Z_FRONT[0]
    f = cyl(CL_R, T)
    f -= cyl(BRG_SEAT / 2, 8.0 + 0.01, -0.01)
    f -= cyl(11.0, T + 2, -1)
    for (x, y) in _ring_pts(CPL_PIN_R, CPL_PIN_A):
        f -= _at(cyl(PIN_HOLE / 2, 15.01, -0.01), x, y)
    for (x, y) in _ring_pts(CL_STANDOFF_R, STANDOFF_A):
        f -= _at(cyl(2.2, T + 2, -1), x, y)
        f -= _at(cyl(4.3, 4.01, -0.01), x, y)                                   # M4 머리 자리 Ø8.6 (유두 머리 Ø7.6)
    for a in SPRING_A:
        x, y = _ring_pts(CL_SPRING_R, [a])[0]
        f -= _at(cyl(10.0, SPRING_POCKET + 0.01, T - SPRING_POCKET), x, y)
        f -= _at(cyl(2.7, T + 2, -1), x, y)
        ns = hexagon(8.2).union(box(0, -4.1, CL_R - CL_SPRING_R + 2, 4.1))     # 너트 홈 + 둘레로 열린 통로 (한 단면으로)
        ns = affinity.translate(affinity.rotate(ns, a, origin=(0, 0)), x, y)
        f -= ext(ns, 4.3, 1.5)
    return f

def cl_back():
    """뒷판. 로컬 z=0 = 끝판 쪽 면(조립 Z_BACK[1]), 두께 8 은 -z 방향. 출력: z=0 면이 바닥.
    가운데 Ø30 / 릴리스 볼트 통과 Ø6.6 / 기둥 M4 + 너트 홈(끝판 쪽 면) / 모터 쪽 면에 코르크 링"""
    T = Z_BACK[1] - Z_BACK[0]
    b = cyl(CL_R, T, -T)
    b -= cyl(15.0, T + 2, -T - 1)
    for (x, y) in _ring_pts(CL_PUSH_R, PUSH_A):
        b -= _at(cyl(3.3, T + 2, -T - 1), x, y)
    for (x, y) in _ring_pts(CL_STANDOFF_R, STANDOFF_A):
        b -= _at(cyl(2.2, T + 2, -T - 1), x, y)
        b -= _at(ext(hexagon(7.2), 3.4, -3.4 + 0.01), x, y)
    return b

def cl_pressure():
    """압력판. 로컬 z=0 = 모터 쪽 면(조립 Z_PRESS[0]), z=8 = 코르크 쪽 면. 출력: z=8 면이 위.
    디스크 허브 통과 Ø22 / 기둥 홈 3 (바깥으로 열림, 회전 전달) / 스프링 자리 Ø19 깊이 2"""
    T = Z_PRESS[1] - Z_PRESS[0]
    p = cyl(CL_R, T)
    p -= cyl(11.0, T + 2, -1)
    for (x, y) in _ring_pts(CL_STANDOFF_R, STANDOFF_A):
        slot = Point(x, y).buffer(5.6, 32).union(Point(x * 1.5, y * 1.5).buffer(5.6, 32)).convex_hull
        p -= ext(slot, T + 2, -1)
    for (x, y) in _ring_pts(CL_SPRING_R, SPRING_A):
        p -= _at(cyl(9.5, 2.01, -0.01), x, y)
    return p

def cl_standoff():
    """기둥: 앞판 +z 면 ~ 뒷판 -z 면, 외경 10 (압력판 홈이 이걸 따라 미끄러짐), M4 볼트 통과"""
    return tube(5.0, 2.2, Z_BACK[0] - Z_FRONT[1])

def cl_disc_hub():
    """디스크 허브: D구멍(미끄럼), 외경 16.6, 길이 33. 로컬 z=0 = 모터 쪽 끝(조립 Z_HUB[0]).
    +z 끝 플랜지 r11 두께 2 의 모터 쪽 면에 강철 와셔(DIN9021 M16)를 에폭시로 붙임. 출력: 플랜지가 바닥"""
    L = Z_HUB[1] - Z_HUB[0]
    h = cyl(8.3, L) + cyl(11.0, 2.0, L - 2.0)
    return h - ext(d_hole_poly(D_SLIDE, D_SLIDE_FLAT), L + 2, -1)

def cl_ring():
    """릴리스 링. 로컬 z=0 = 판의 모터 쪽 면(조립 Z_RING[0]). 판 Ø76x4, 어깨 Ø20x2(6003 내륜만 닿음),
    보스 Ø17 (6003 안지름), M5 누름 볼트 3 (모터 쪽 면에 너트 홈 → 볼트 길이로 유격 조절). 출력: 판이 바닥"""
    T = Z_RING[1] - Z_RING[0]
    r = cyl(38.0, T) + cyl(10.0, 2.0, T) + cyl(B6003[0] / 2 - 0.02, (Z_REL[1] - Z_RING[1]) - 2.0 + 0.5, T + 2.0)
    r -= cyl(6.75, 40, -1)
    for (x, y) in _ring_pts(CL_PUSH_R, PUSH_A):
        r -= _at(cyl(2.7, T + 2, -1), x, y)
        r -= _at(ext(hexagon(8.2), 3.0, -0.01), x, y)
    return r

CARRIER_Z = (Z_REL[0] + 1.5, Z_REL[1] + 1.5)         # 캐리어: 베어링보다 1.5 끝판 쪽 (턱이 외륜 +z 면을 밈)
def cl_carrier():
    """릴리스 베어링 캐리어. 로컬 z=0 = 끝판 쪽 턱 면(조립 CARRIER_Z[1]), -z 방향 10.
    6003 외륜 자리(깊이 8.5) + 턱(안지름 29) + 좌우 트러니언 Ø6 (x=±21.5~±29.5). 출력: 턱 면이 바닥"""
    W = B6003[2]
    c = cyl(22.5, W, -W) - cyl(BRG3_SEAT / 2, W, -W - 0.01) - cyl(14.5, W + 2, -W - 1)
    c += cyl(22.5, 1.5, -1.5) - cyl(14.5, 4, -3)
    for s in (-1, 1):
        t = along_x(cyl(3.0, 8.0, 0))
        c += t.translate([21.5 if s > 0 else -29.5, 0, -W / 2])
    return c

FORK_PIV_Y = H + 32.0          # 포크 피벗 (입력축 위 32)
FORK_CABLE_Y = H + 92.0        # 케이블 (피벗 위 60 → 피벗 아래 32 의 트러니언 대비 지렛대비 1.9)
FORK_Z = (CARRIER_Z[0] + 10 - 5.0 + 3.0, CARRIER_Z[0] + 10 - 5.0 + 9.0)   # 트러니언(z중심) +z 면부터 6mm 판
CABLE_HOLE = (0.0, FORK_CABLE_Y)
FORK_PIV_Z = FORK_Z[1] - 5.75  # v4.1: 피벗 축(x 방향 M5)은 포크 판 모터 쪽 보스 가운데 (보스 18x12x11.5, 벽 3)

def cl_fork():
    """클러치 포크 (두께 6). x 축 M5x70 피벗 + 나일론 너트: 가운데 보스(18x12, 5.5 돌출)와 양 팔 보스(x ±16~±30.5)를 x 방향으로 관통.
    (피벗 축이 팔을 지나므로 팔에 구멍이 없으면 볼트를 끼울 수 없음 → 팔 보스. 너트는 손으로 닿을 때까지만: 세게 조이면 팔이 볼을 물어 포크가 안 돎)
    출력: 끝판 쪽 면(판과 보스가 같은 면)이 바닥. 양쪽 팔(x ±20.5~30.5)이 아래로 내려가
    트러니언(x=±21.5~29.5, y=H)의 +z 쪽을 밀고(-z 방향), 위 끝은 케이블 속선이 +z(끝판 쪽)로 당김.
    팔은 피벗 위 가로대(y PIV+10~16)로 몸통에 연결 → 브래킷 볼(x ±9.5~15.5, y PIV±9)과 안 겹침"""
    pv = FORK_PIV_Y
    prof = box(-30.5, H - 4.0, -20.5, pv + 16).union(box(20.5, H - 4.0, 30.5, pv + 16))      # 세로 팔
    prof = prof.union(box(-30.5, pv + 10, 30.5, pv + 16))                                  # 가로대
    prof = prof.union(Point(0, pv).buffer(9.0, 32)).union(box(-9.0, pv, 9.0, FORK_CABLE_Y + 7))   # 허브·몸통
    prof = prof.difference(Point(0, H).buffer(24.5, 64))
    prof = prof.difference(Point(0, FORK_CABLE_Y).buffer(1.2, 24))
    f = ext(prof, FORK_Z[1] - FORK_Z[0], FORK_Z[0])
    f -= cyl(1.3, 10, FORK_Z[0] - 1).translate([0, FORK_CABLE_Y - 4.0, 0])   # 속선 누름 M3x10 자가탭 + M3 와셔(바깥 7): 와셔가 속선(4 떨어짐)을 덮음
    f += boxm(-9.0, 9.0, pv - 6.0, pv + 6.0, FORK_Z[1] - 11.5, FORK_Z[1])      # 피벗 보스
    for s in (-1, 1):                                                          # v4.1: 팔 보스 (x ±16~±30.5) → 볼트가 팔·볼·보스를 모두 꿰어 끼울 수 있음
        f += boxm(min(16.0 * s, 30.5 * s), max(16.0 * s, 30.5 * s), pv - 6.0, pv + 6.0, FORK_Z[1] - 11.5, FORK_Z[1])
    f -= along_x(cyl(2.75, 64, -32)).translate([0, pv, FORK_PIV_Z])
    return f

FORK_BRK_HOLES = ((-17.0, 112.0), (17.0, 112.0), (-17.0, 156.0), (17.0, 156.0))
def cl_fork_bracket():
    """포크 브래킷: 끝판 A 바깥면에 M4 4개. 받침판(y 104~164) + 피벗 볼 2개(x ±9.5~±15.5, y PIV±9, M5) +
    쉬는 위치 받침(포크 모터 쪽 면을 받침, y 146~154, 기둥은 x ±10~±14). 케이블 아우터는 끝판 A 의 구멍에 걸림"""
    zo = -PLATE_T
    zb = zo - 5.0
    base = boxm(-24, 24, 104, 164, zb, zo) - boxm(-9.8, 9.8, 138, 165, zb - 1, zo + 1)   # 포크 위쪽이 밟을 때 들어오는 자리
    for (xb, yb) in FORK_BRK_HOLES:
        base -= cyl(2.2, 12, zb - 1).translate([xb, yb, 0])
        base -= cyl(4.3, 3.0, zb - 0.01).translate([xb, yb, 0])                # M4 머리 자리 Ø8.6
    zc = (FORK_Z[0] + FORK_Z[1]) / 2
    pv = FORK_PIV_Y
    for s in (-1, 1):
        x0, x1 = (9.5, 15.5) if s > 0 else (-15.5, -9.5)
        base += boxm(x0, x1, pv - 9, pv + 9, FORK_PIV_Z - 6.75, zb + 0.01)
        x0, x1 = (10.0, 14.0) if s > 0 else (-14.0, -10.0)
        base += boxm(x0, x1, 146, 154, FORK_Z[0] - 4.0, zb + 0.01)
    base -= along_x(cyl(2.7, 40, -20)).translate([0, pv, FORK_PIV_Z])
    base += boxm(-14.0, 14.0, 146, 154, FORK_Z[0] - 4.0, FORK_Z[0] - 1.5)
    return base

def cl_spring_cup():
    """스프링 컵: Ø19x3 + 맞춤 보스 Ø11x3 (C252 안지름이 11 보다 커야 함 — 미확인). 출력: 판이 바닥"""
    return cyl(9.5, 3.0) + cyl(5.5, 3.0, 3.0)

def cl_end_spacer():
    """파일럿 베어링 내륜 ~ 끝 칼라 사이 와셔 (외경 16, 두께 1)"""
    return tube(8.0, SHAFT_HOLE / 2, 1.0)

def cork_ring():
    return tube(CORK[1], CORK[0], CORK[2])

def steel_washer():
    return tube(WASHER[1] / 2, WASHER[0] / 2, WASHER[2])


# ======================= 모터 받침·페달 =======================
# GGM K9B-M6 브래킷 (제조사 도면): 앞판 112x112 두께 9, Ø83 구멍, M6 4개 Ø104 원 / 바닥 146x65 두께 9,
# 바닥 구멍 Ø6.4 좌우 128 · 앞뒤 40 (앞판 바깥면에서 17, 57), 바닥 → 축 중심 66±0.5
MOTOR_FOOT_DY = 66.0          # 브래킷 바닥 → 축 중심 (도면)
MOTOR_FOOT_HOLE = 128.0       # 바닥 구멍 좌우 간격 (도면, 실측 130)
MOTOR_FOOT_Z = (17.0, 57.0)   # 앞판 바깥면 → 바닥 구멍 앞뒤 줄 (도면, 실측 간격 40)
MOTOR_STUD_R = 52.0           # 앞판 M6 볼트 원 반지름 (도면 Ø104) → 45° 4곳
MOTOR_STUD_OUT = 30.0         # 앞판 바깥면 → 볼트 끝 (실측)
RISER_H = H - MOTOR_FOOT_DY   # 19
RISER_BACK = 30.0             # 긴 구멍 뒤로 여유: 볼트 끝(30)이 덮개 앞판 뒤에 있는 위치에서 내려놓고 앞으로 밀어 넣음
Z_RISER = (Z_GEARHEAD_FRONT - MOTOR_FOOT_Z[1] - RISER_BACK - 14.0, Z_GEARHEAD_FRONT + 3.0)   # 앞 끝은 덮개 앞판(-138)과 1 틈

def motor_riser():
    """모터 받침대 (조립 좌표). 높이 19 판 (x ±85). 브래킷 바닥 구멍 4개용 긴 구멍 (폭 6.6, 정위치에서 뒤로 30, 앞 끝 = 정위치:
    앞으로 끝까지 밀고 조이면 볼트 끝과 클러치 앞판 틈 4mm, 더 앞으로 못 감),
    밑면에 M6 너트 홈 (폭 10.4, 깊이 9, 너트가 돌지 않고 긴 구멍을 따라 움직임 → MDF 에 붙이기 전에 너트를 넣음).
    볼트 M6x25 (M6x30 이상은 MDF 에 닿음). 목재나사 4x16 4개 (브래킷 바닥 밖 x ±79, 머리 자리 Ø9). 출력: 바닥이 바닥"""
    z0, z1 = Z_RISER
    r = boxm(-85, 85, 0, RISER_H, z0, z1)
    for s in (-1, 1):
        x = s * MOTOR_FOOT_HOLE / 2
        for dz in MOTOR_FOOT_Z:
            zc = Z_GEARHEAD_FRONT - dz
            za, zb = zc - RISER_BACK - 3.3, zc + 3.3                                        # 볼트(Ø6) 중심 이동 범위 = 정위치 -30 ~ +0.3
            r -= ext(Polygon([(x - 3.3, za), (x + 3.3, za), (x + 3.3, zb), (x - 3.3, zb)]),
                     RISER_H + 2, 0).rotate([90, 0, 0]).translate([0, RISER_H + 1, 0])       # (x,z) 단면을 y 방향으로
            r -= boxm(x - 5.2, x + 5.2, -1, 9.0, za - 5.5, zb + 5.5)                         # 너트 홈 (맞변 10)
    for (x, zz) in ((-79, z0 + 6), (79, z0 + 6), (-79, z1 - 6), (79, z1 - 6)):
        r -= along_y(cyl(2.2, RISER_H + 2, -1)).translate([x, 0, zz])
        r -= along_y(cyl(4.5, RISER_H, 5.0)).translate([x, 0, zz])       # 머리 자리: 바닥 5 남김 → 4x16 이 MDF(12T)에 11 박힘
    return r

def motor_bracket():
    """간섭 검사용 K9B-M6 브래킷 + 앞판 M6 볼트·너트 4 (조립 좌표, 구매품)"""
    zf = Z_GEARHEAD_FRONT
    b = boxm(-56, 56, RISER_H, RISER_H + 112, zf - 9, zf) - cyl(41.5, 11, zf - 10).translate([0, H, 0])
    b += boxm(-73, 73, RISER_H, RISER_H + 9, zf - 65, zf)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, y = MOTOR_STUD_R * math.cos(a), H + MOTOR_STUD_R * math.sin(a)
        b += cyl(3.0, MOTOR_STUD_OUT, zf).translate([x, y, 0]) + cyl(5.8, 5.0, zf).translate([x, y, 0])   # 볼트 + 너트(두께 5)
    return b

PEDAL_L = 195.0
PEDAL_PIV_Y = 30.0
PEDAL_T = 18.0                 # 팔 두께 (피벗 축 방향, 받침 x)
PEDAL_W = 18.0                 # 팔 폭 (a)
PEDAL_CABLE_B = 30.0           # 케이블 구멍 (피벗에서)
PEDAL_PAD_B = 180.0            # 발판 가운데
PEDAL_SPR_B = 42.0             # 복귀 스프링(C252 압축) 자리
PEDAL_REST = 25.0              # 쉬는 각 (수직에서 운전자 반대쪽 +z 로 기움, 도)
PEDAL_TRAVEL = math.degrees(3.0 * (FORK_CABLE_Y - FORK_PIV_Y) / (FORK_PIV_Y - H) / PEDAL_CABLE_B)   # 끝 멈춤: 릴리스 링 3.0 이동 (뒷판까지 3.5)
PEDAL_SPR_L = 29.0             # 쉴 때 복귀 스프링 길이 (C252 자유장 32 → 7.6N)
PEDAL_POT_P = 2.5              # 가변저항 몸통 자리 깊이 (축 15mm 기준: 축 끝이 D 구멍에 4 물림)

def pedal_dirs(th_deg):
    """받침 (y, z) 평면에서 팔 방향 u, 운전자 쪽 면 법선 nb, 앞쪽 면 법선 nf"""
    t = math.radians(th_deg)
    return np.array([math.cos(t), math.sin(t)]), np.array([math.sin(t), -math.cos(t)]), np.array([-math.sin(t), math.cos(t)])

def pedal_arm():
    """페달 팔 (클러치·브레이크 공용, 2개). 로컬: a=x(-9 운전자 쪽 면 ~ +9 앞면), b=y(피벗 0 ~ 195), 두께 z 0~18 (z=0 = 받침 왼쪽).
    피벗: z=0 면 M6 나일론 너트 홈(맞변 10.2, 깊이 6.2) + Ø6.4, z=18 면 가변저항 D 구멍(Ø6.1, 평면까지 1.6, 깊이 5).
    케이블 구멍 b=30 (a 방향 Ø3.4, 니플은 앞면), 복귀 스프링 자리 b=42 (앞면 Ø20 깊이 1.5),
    발판 M4 2개 (b=172, 188, a 방향, 앞면 너트 홈). 출력: z=0 면이 바닥"""
    hw = PEDAL_W / 2
    prof = box(-hw, 0, hw, PEDAL_L).union(Point(0, 0).buffer(13, 64))
    arm = ext(prof, PEDAL_T)
    zc = PEDAL_T / 2
    arm -= ext(hexagon(10.2), 6.2, -0.01)                                    # 나일론 너트 (DIN985 M6 두께 6)
    arm -= cyl(3.2, 12.0, -0.5)                                              # M6 Ø6.4 (볼트 끝 z=11.5)
    dcut = Point(0, 0).buffer(3.05, 32).intersection(box(-4, -4, 1.65, 4))   # 반달축 Ø6, 평면 4.6 (평면이 +a 쪽)
    arm -= ext(dcut, 5.01, PEDAL_T - 5.0)
    arm -= along_x(cyl(1.7, 30, -15)).translate([0, PEDAL_CABLE_B, zc])     # 케이블 (a 방향)
    arm -= along_x(cyl(10.0, 2.0, hw - 1.5)).translate([0, PEDAL_SPR_B, zc])  # 스프링 끝 자리 (앞면 Ø20 깊이 1.5)
    for bb in (172.0, 188.0):
        arm -= along_x(cyl(2.2, 30, -15)).translate([0, bb, zc])
        arm -= along_x(ext(hexagon(7.2), 3.4, 0)).translate([hw - 3.4 + 0.01, bb, zc])   # M4 너트 홈 (앞면)
    return arm

def pedal_arm_placed(th_deg, solid=False):
    """팔을 받침 좌표로 (z=0 면 → x=-9, a → 회전 후 z, b → 위). solid=True: 구멍·보스 없는 외형"""
    t = math.radians(th_deg)
    R0 = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]], float)                 # a→z, b→y, 두께→x
    Rx = np.array([[1, 0, 0], [0, math.cos(t), -math.sin(t)], [0, math.sin(t), math.cos(t)]])
    A = np.zeros((3, 4)); A[:, :3] = Rx @ R0; A[:, 3] = Rx @ np.array([-PEDAL_T / 2, 0, 0]) + np.array([0, PEDAL_PIV_Y, 0])
    arm = ext(box(-PEDAL_W / 2, 0, PEDAL_W / 2, PEDAL_L).union(Point(0, 0).buffer(13, 64)), PEDAL_T) if solid else pedal_arm()
    return arm.transform(A)

def pedal_pad():
    """발판 70x40x8, M4x25 2개(간격 16, 머리는 윗면 Ø8 깊이 3 자리, 너트는 팔 앞면 홈), 미끄럼 방지 홈.
    팔 운전자 쪽 면(b 160~200)에 70 방향이 피벗 축과 나란하게 붙임. 출력: 홈 면이 위"""
    p = boxm(-35, 35, -20, 20, 0, 8)
    for dy in (-8.0, 8.0):
        p -= cyl(2.2, 10, -1).translate([0, dy, 0])
        p -= cyl(4.3, 3.01, 5.0).translate([0, dy, 0])                          # M4 머리 자리 Ø8.6
    for k in range(6):
        p -= boxm(-33, 33, -17 + 6 * k, -15 + 6 * k, 6.5, 9)
    return p

def _pedal_sweep(th0, th1, n=12):
    """팔이 지나가는 공간 (구멍을 메운 외형으로: 받침 블록이 팔 구멍 안에 남지 않게)"""
    return M.batch_boolean([pedal_arm_placed(th0 + (th1 - th0) * k / n, True) for k in range(n + 1)], mf.OpType.Add)

def pedal_points():
    """받침 좌표 (y, z): 케이블 속선 나가는 점·받침 끝, 스프링 자리 (쉴 때 기준)"""
    py = np.array([PEDAL_PIV_Y, 0.0])
    u, nb, nf = pedal_dirs(PEDAL_REST)
    cab0 = py + PEDAL_CABLE_B * u + (PEDAL_W / 2) * nb                    # 운전자 쪽 면에서 나가는 점
    cab1 = cab0 + 40.0 * nb                                                # 케이블 받침(속선 구멍 끝)
    um, _, nfm = pedal_dirs(PEDAL_REST + PEDAL_TRAVEL / 2)
    spr0 = py + PEDAL_SPR_B * u + (PEDAL_W / 2 - 1.5) * nf                 # 팔 스프링 자리 바닥 (쉴 때)
    spr1 = spr0 + (PEDAL_SPR_L - 3.0) * nfm                                # 받침 스프링 보스 끝 (보스 3 이 스프링 안)
    return cab0, cab1, spr0, spr1, nb, nfm

def _yz_cyl(p, d, r, h):
    """(y,z) 점 p 에서 (y,z) 방향 d 로 길이 h 원통 (x=0)"""
    ang = math.degrees(math.atan2(d[0], d[1]))              # z 축에서 y 쪽으로 기운 각
    return cyl(r, h).rotate([-ang, 0, 0]).translate([0, p[0], p[1]])

def pedal_base():
    """페달 받침 (조립 좌표: 바닥 y=0, 피벗 축 = x 축, 높이 30, z=0). 운전자는 -z 쪽, 팔은 +z 로 25° 기움, 밟으면 +z 로 PEDAL_TRAVEL°.
    바닥판 120x(z)140 / 볼 2개 (x ±9.5~±22.5): 왼쪽 M6 Ø6.4, 오른쪽 가변저항 (부싱 Ø7.4 + 바깥 몸통 자리 Ø17.5 깊이 2.5, 에폭시) /
    쉬는 위치 받침(운전자 쪽 면, x ±2.5~±8.5 → 가운데로 케이블) / 끝 멈춤(앞면) / 케이블 받침(아우터 Ø5.6 깊이 8, 속선 Ø2.2) /
    복귀 스프링 C252 받침(보스 Ø12x3, 쉴 때 길이 27 → 끝 18.8) / 목재나사 4. 출력: 바닥판이 바닥"""
    py = PEDAL_PIV_Y
    b = boxm(-60, 60, 0, 6, -55, 85)
    for x0, x1 in ((-22.5, -9.5), (9.5, 22.5)):
        b += boxm(x0, x1, 0, py + 14, -16, 16)
    b -= along_x(cyl(3.2, 20, -25)).translate([0, py, 0])                 # 왼쪽 M6
    b -= along_x(cyl(3.7, 20, 5)).translate([0, py, 0])                   # 오른쪽 가변저항 부싱 M7
    b -= along_x(cyl(8.75, PEDAL_POT_P + 1, 22.5 - PEDAL_POT_P)).translate([0, py, 0])   # 몸통 자리
    swept = _pedal_sweep(PEDAL_REST, PEDAL_REST + PEDAL_TRAVEL)
    swept += along_x(cyl(13.6, 30, -15)).translate([0, py, 0])             # 피벗 둥근 부분 (반지름 13) + 여유: 회전한 다각형 조각이 남지 않게
    u, nb, nf = pedal_dirs(PEDAL_REST)
    us, nbs, nfs = pedal_dirs(PEDAL_REST + PEDAL_TRAVEL)
    # 쉬는 위치 받침: 팔 b=16~28 의 운전자 쪽 (쉴 때 닿음)
    for s in (-1, 1):
        x0, x1 = (2.5, 8.5) if s > 0 else (-8.5, -2.5)                    # 팔(±9) 안쪽: 면이 겹치지 않게
        blk = M.batch_hull([boxm(x0, x1, 0, 6, -40, 10),
                            boxm(x0, x1, py + 26 * u[0] + 9 * nb[0] - 1, py + 26 * u[0] + 9 * nb[0], 26 * u[1] + 9 * nb[1] - 12, 26 * u[1] + 9 * nb[1] + 2)])
        b += blk - swept
    # 끝 멈춤: 팔 b=16~28 의 앞쪽 (끝까지 밟으면 닿음)
    pt = np.array([py, 0.0]) + 22 * us + 9 * nfs
    blk = M.batch_hull([boxm(-8.5, 8.5, 0, 6, pt[1] - 4, pt[1] + 16), boxm(-8.5, 8.5, pt[0] - 6, pt[0] + 2, pt[1] - 2, pt[1] + 10)])
    b += blk - swept
    cab0, cab1, spr0, spr1, nbr, nfm = pedal_points()
    # 케이블 받침: 속선 구멍 끝 cab1 에서 nb 방향 14 (아우터 자리는 바깥 끝 8)
    seat = _yz_cyl(cab1, nbr, 7.0, 14.0)
    seat = M.batch_hull([seat, boxm(-7, 7, 0, 6, cab1[1] + 14 * nbr[1] - 7, cab1[1] + 7)])
    seat -= _yz_cyl(cab1 - 2 * nbr, nbr, 1.1, 20.0)                        # 속선
    seat -= _yz_cyl(cab1 + 6 * nbr, nbr, 2.8, 20.0)                        # 아우터 자리 (깊이 8)
    seat -= _yz_cyl(cab0, nbr, 2.0, float(np.linalg.norm(cab1 - cab0)) - 1.0)   # 속선 지나가는 길 (Ø4)
    b += seat
    # 복귀 스프링 받침: spr1 에 원판 Ø22 두께 5 + 보스 Ø12x3 (팔 쪽), 바닥까지 채움
    disk = _yz_cyl(spr1 + 3.0 * nfm, nfm, 11.0, 5.0)
    post = M.batch_hull([disk, boxm(-11, 11, 0, 6, spr1[1] + 3 * nfm[1] - 8, spr1[1] + 3 * nfm[1] + 14)])
    b += post + _yz_cyl(spr1, nfm, 6.0, 3.0)
    for (x, zz) in ((-50, -45), (50, -45), (-50, 75), (50, 75)):
        b -= along_y(cyl(2.2, 10, -1)).translate([x, 0, zz])
    return b


# ======================= v4.1 안전 덮개 =======================
def end_filler():
    """끝 채움판 (끝판 왼쪽 x=-62~-25 빈 곳을 막음, 2개: A·B 같은 모양). 조립 좌표: z 0~15 (A 는 -15~0, B 는 STACK~).
    끝판 왼쪽 면에 M3x50 2개 (왼쪽 면에서 관통, 머리 자리), 윗면 아크릴 나사 1, 왼쪽 아크릴 판 나사 2. 출력: 넓은 면이 바닥"""
    f = boxm(COVER_X0 + COVER_T, PLATE_X0, 0, PLATE_Y1, 0, PLATE_T)
    zm = PLATE_T / 2
    for y in FILLER_Y:
        f -= along_x(cyl(1.7, 40, 0)).translate([COVER_X0 + COVER_T - 1, y, zm])    # M3 통과 (채움판 전체)
        f -= along_x(cyl(3.2, 4.0, 0)).translate([COVER_X0 + COVER_T - 0.01, y, zm])   # 머리 자리 (아크릴 판 아래로 숨음)
    f -= along_y(cyl(1.25, 12.01, -12.0)).translate([-45.0, PLATE_Y1 + 0.01, zm])  # 윗면 아크릴
    for y in FILLER_SIDE_Y:
        f -= along_x(cyl(1.25, 12.01, 0)).translate([COVER_X0 + COVER_T - 0.01, y, zm])   # 왼쪽 아크릴
    f -= cyl(1.25, 12.01, -0.01).translate([HOOD_TAB_L[0], HOOD_TAB_L[1], 0])        # 클러치 덮개 왼쪽 탭 (A 에서만 씀)
    return f

HOOD_TAB_L = (-56.5, 127.0)                          # 클러치 덮개 왼쪽 탭 → 끝 채움판 A
HOOD_POSTS = ((COVER_X0 + COVER_T + 4, 6.0), (-COVER_X0 - COVER_T - 4, 6.0),
              (COVER_X0 + COVER_T + 4, HOOD_TOP - COVER_T - 4), (-COVER_X0 - COVER_T - 4, HOOD_TOP - COVER_T - 4))
def clutch_hood():
    """클러치·커플링 덮개 (조립 좌표). 뒤집은 U 단면 (바닥은 MDF), x -65~65, y 0~195, z -135~-15, 벽 3.
    끝판 쪽 끝: 오른쪽 탭 2 (끝판 A, M3), 왼쪽 탭 1 (끝 채움판 A, M3). 앞쪽 끝: 앞판 나사 기둥 4 (아래쪽 45° 모따기).
    바닥 양옆 플랜지(폭 14, 전체 길이, 목재나사 4). 출력: 끝판 쪽 끝(탭)이 바닥 → 받침 없이 출력"""
    z0, z1 = HOOD_Z
    x0, x1 = COVER_X0, -COVER_X0
    t = COVER_T
    h = boxm(x0, x1, 0, HOOD_TOP, z0, z1) - boxm(x0 + t, x1 - t, -1, HOOD_TOP - t, z0 - 1, z1 + 1)
    for (xh, yh) in HOOD_TABS:
        h += boxm(x1 - t, xh + 7, yh - 7, yh + 7, z1 - 3, z1) - cyl(1.7, 5, z1 - 4).translate([xh, yh, 0])
    xl, yl = HOOD_TAB_L
    h += boxm(x0 + t - 0.01, xl + 4.5, yl - 7, yl + 7, z1 - 3, z1) - cyl(1.7, 5, z1 - 4).translate([xl, yl, 0])
    for (xc, yc) in HOOD_POSTS:
        xw = x0 + t if xc < 0 else x1 - t                                # 기둥이 붙은 옆벽 안쪽 면
        ya, yb = (0.0, yc + 4) if yc < 50 else (yc - 4, yc + 4)
        post = boxm(xc - 4, xc + 4, ya, yb, z0, z0 + 12)
        post = M.batch_hull([post, boxm(min(xw, xw + 0.01), max(xw, xw + 0.01), ya, yb, z0, z0 + 20)])   # 45° 모따기
        h += post - cyl(1.25, 12.01, z0 - 0.01).translate([xc, yc, 0])
    for xs in (x0, x1):
        xa, xb = (xs - 14, xs) if xs < 0 else (xs, xs + 14)
        h += boxm(xa, xb, 0, 5, z0, z1)                                  # 두께 5: 목재나사 4x16 이 MDF(12T)에 11 박힘 (밑으로 안 나옴)
        for zz in (z0 + 20, z1 - 25):
            h -= along_y(cyl(2.2, 7, -1)).translate([(xa + xb) / 2, 0, zz])
    return h

def hood_front():
    """클러치 덮개 앞판 (조립 좌표 z -138~-135). 가운데 Ø46: 스프로킷(바깥지름 약 41)이 지나감,
    브래킷 볼트 4곳 Ø13 → 덮개를 먼저 달고 모터를 뒤에서 밀어 넣음. 나사 4 (Ø3.4). 출력: 평평하게"""
    z0 = HOOD_Z[0] - COVER_T
    f = boxm(COVER_X0, -COVER_X0, 0, HOOD_TOP, z0, z0 + COVER_T)
    f -= cyl(23.0, 10, z0 - 1).translate([0, H, 0])
    for k in range(4):                                              # 감속기 브래킷 볼트·너트(맞변 10)가 지나가는 구멍 Ø13
        a = math.radians(45 + 90 * k)
        f -= cyl(6.5, 10, z0 - 1).translate([MOTOR_STUD_R * math.cos(a), H + MOTOR_STUD_R * math.sin(a), 0])
    for (xc, yc) in HOOD_POSTS:
        f -= cyl(1.7, 10, z0 - 1).translate([xc, yc, 0])
    return f

def collar_cap():
    """축 끝 덮개 컵 (조립 좌표: 끝판 A 출력축 칼라 r13 z -27~-17 위치). 바깥 r17, 안 r15, z -33~-15, 탭 2 (M3).
    끝판 B 입력축 끝(칼라 z 308~318)에도 같은 부품을 뒤집어 씀. 출력: 막힌 끝이 바닥"""
    z0, z1 = -33.0, -15.0
    c = cyl(17.0, z1 - z0, z0)
    for (xh, yh) in CAP_TABS:
        dy = yh - H
        tab = boxm(-6, 6, dy - 6, dy + 6, z1 - 3, z1) + boxm(-6, 6, min(dy, 0), max(dy, 0), z1 - 3, z1)
        c += tab - cyl(1.7, 5, z1 - 4).translate([0, dy, 0])
    c -= cyl(15.0, z1 - z0 - 2.0 + 0.01, z0 + 2.0)          # 속 (칼라 r13 과 2 틈)
    return c.translate([C, H, 0])

def acrylic_panels():
    """아크릴 3T 판 (조립 검사·재단 치수용): 윗판, 왼쪽 판, 오른쪽 판"""
    za, zb = -PLATE_T, STACK + PLATE_T
    top = boxm(COVER_X0, COVER_X1, PLATE_Y1, PLATE_Y1 + COVER_T, za, zb)
    left = boxm(COVER_X0, COVER_X0 + COVER_T, 0, PLATE_Y1, za, zb)
    right = boxm(PLATE_X1, COVER_X1, 0, PLATE_Y1, za, zb)
    return {'acr_top': top, 'acr_left': left, 'acr_right': right}
