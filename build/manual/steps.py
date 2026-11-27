"""설명서 단계 정의 → steps.json. 수치는 tx(설계 코드)에서 가져옴."""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import tx
BOUNDS = json.load(open(os.path.join(HERE, 'parts.json')))
NAMES = set(BOUNDS)
def center(*names):
    lo = [min(BOUNDS[n][0][i] for n in names) for i in range(3)]; hi = [max(BOUNDS[n][1][i] for n in names) for i in range(3)]
    return [(a + b) / 2 for a, b in zip(lo, hi)]

def G(*prefixes):
    out = []
    for p in prefixes:
        hit = sorted(n for n in NAMES if n == p or (p.endswith('*') and n.startswith(p[:-1])))
        assert hit, p
        out += hit
    return out

# 보기 방향 (카메라가 있는 쪽), 위 방향
STAND = dict(dir=[0.55, -1.0, 0.8], up=[0, 0, 1])          # 끝판 A 를 바닥에 세움 (축이 위)
LIE_A = dict(dir=[-1.0, 0.75, -1.05], up=[0, 1, 0])        # 눕힘, 끝판 A(클러치) 쪽 앞에서
LIE_B = dict(dir=[0.9, 0.8, 1.1], up=[0, 1, 0])             # 눕힘, 끝판 B(레버) 쪽에서
FACE = dict(dir=[0.35, -0.55, 1.0], up=[0, 1, 0])           # 기어 한 장을 정면 가까이
FACE1 = dict(dir=[0.35, 0.6, -1.0], up=[0, 1, 0])           # 1단 출력 기어 (핀이 -z 면)
UNDER = dict(dir=[0.55, -1.0, -0.45], up=[0, 0, 1])        # 세운 상태에서 끝판 A 아래쪽
CLU = dict(dir=[-0.75, 0.55, -1.0], up=[0, 1, 0])           # 클러치 (끝판 A 바깥)
CLUB = dict(dir=[0.7, 0.55, 1.0], up=[0, 1, 0])            # 클러치 부품을 끝판 쪽에서
PED = dict(dir=[-1.0, 0.8, -0.9], up=[0, 1, 0])

PIN_OUT = tx.PIN_OUT
PIN_LEN = tx.PIN_OUT + tx.PIN_IN
A_OUT = tx.PLATE_T                       # 끝판 A 바깥면 z = -15
def from_A(z):                           # 끝판 A 바깥면에서 바깥(클러치 쪽)으로 잰 거리
    return round(-A_OUT - z)

S = []          # 단계
built = []      # 큰 조립체에 지금까지 붙은 것
def step(sec, new, text, call, view, ctx=None, explode=None, rep=None, note=None, inset=None, keep=True, hide=(), fit=None, tip=None):
    global built
    if ctx is None:
        ctx_ = [n for n in built if n not in hide]
    else:
        ctx_ = ctx
    if fit is None and ctx is None and sec.startswith(('4.', '9.', '10.')) and new: fit = 'new'
    S.append(dict(n=len(S) + 1, sec=sec, new=new, ctx=ctx_, text=text, call=call, view=view, explode=explode or [0, 0, 0],
                  rep=rep, note=note, inset=inset, fit=fit, tip=tip))
    if keep and ctx is None:
        built = [n for n in built if n not in hide] + [n for n in new if n not in built]

# ---------------- 1. 출력 기어 준비 ----------------
g1 = 'gout_1'
step('1. 출력 기어 준비', [g1] + G('brg_g1_*'), '출력 기어 양쪽 구멍에 베어링 6001을 1개씩 바이스로 눌러 넣기',
     [['11 출력 기어', 1, 'stl:11_gear_out_1_z49'], ['베어링 6001', 2, 'brg6001']], FACE1, ctx=[], explode=[0, 0, 0],
     rep='×6', note='망치로 치지 않기. 평평한 판을 대고 바깥 링을 고르게 누르기', keep=False)
step('1. 출력 기어 준비', ['pinsteel_1'], f'핀 구멍 4곳에 평행핀 Ø5×{PIN_LEN:.0f}을 인두로 데워 바닥까지 넣기 → {PIN_OUT:.0f}mm 나옴',
     [['평행핀 Ø5×25', 4, 'pin5x25'], ['인두', 0, 'iron']], FACE1, ctx=[g1] + G('brg_g1_*'), explode=[0, 0, -15], rep='×6',
     note=f'망치 금지: 바닥을 뚫고 더 들어가 짧아짐. 나온 길이 {PIN_OUT - 1:.0f}~{PIN_OUT + 1:.0f}mm면 OK, 4개 차이는 0.5mm 안',
     inset=dict(target=[tx.C + tx.PIN_R, tx.H, tx.PLANE['1']], size=40), keep=False,
     tip='나온 길이 − 1mm = 슬리브에 걸리는 길이')
step('1. 출력 기어 준비', ['pins_1'], '고무 호스를 (핀 나온 길이 − 0.5mm)로 잘라 핀에 끼우기. 접착은 아직 안 함',
     [['고무 호스 Ø5×10', 4, 'hose']], FACE1, ctx=[g1, 'pinsteel_1'] + G('brg_g1_*'), explode=[0, 0, -12], rep='×6',
     note='예: 핀 6mm → 호스 5.5mm. 핀보다 길면 끝이 찢어짐', keep=False, inset=dict(target=[tx.C + tx.PIN_R, tx.H, tx.PLANE['1']], size=40))

# ---------------- 2. 슬리브 ----------------
step('2. 슬리브', ['slv_12'], '반쪽 2개 사이에 링을 끼우고 M3×20 3개 + 너트로 조이기 (머리·너트는 육각 자리 안)',
     [['21 슬리브 반쪽', 2, 'stl:21_sleeve_half'], ['22 슬리브 링', 1, 'stl:22_sleeve_ring'], ['M3×20', 3, 'bolt:3:20'], ['M3 너트', 3, 'nut:3']],
     FACE, ctx=[], rep='×3', keep=False)
step('2. 슬리브', ['hub_12'], '슬리브 안에 허브를 끼우기. 걸리지 않고 미끄러지면 OK',
     [['20 허브', 1, 'stl:20_hub']], FACE, ctx=['slv_12'], explode=[0, 0, 60], rep='×3', keep=False)
step('2. 슬리브', ['slv_12'], '호스 낀 핀에 슬리브 포켓을 대 보기 → 손가락으로 밀어 쑥 들어가면 OK. 그다음 호스를 빼고 핀에만 에폭시를 얇게 발라 다시 끼우기',
     [['에폭시', 0, 'epoxy'], ['사포 240', 0, 'sand']], FACE1, ctx=[g1, 'pins_1'] + G('brg_g1_*'), explode=[0, 0, -45], rep='×6',
     note='빡빡하면 포켓의 안·바깥 둥근 벽만 사포로 갈기. 호스 바깥에 에폭시가 묻으면 다시 빡빡해짐', keep=False)

# ---------------- 3. 끝판 A ----------------
step('3. 끝판 A', ['plate_A'] + G('brg_A_*'), '안쪽 면(넓게 파인 구멍)에 베어링 6001 2개 눌러 넣기',
     [['40 끝판 A', 1, 'stl:40_plate_A'], ['베어링 6001', 2, 'brg6001']], STAND, explode=[0, 0, 40])
step('3. 끝판 A', G('nutA_*'), '같은 면의 네모 홈 4개에 M4 너트를 인두로 데워 눌러 넣기 (클러치 브래킷용, 나중에 손이 안 닿음)',
     [['M4 너트', 4, 'nut:4']], STAND, explode=[0, 0, 25], note='홈(6.4mm)이 너트(7mm)보다 좁게 설계됨 → 데워서 넣으면 빠지지 않음',
     inset=dict(target=[0, 134, 0], size=70))
step('3. 끝판 A', ['shaft_idler'], f'아이들러 축 Ø12×55 끝에 에폭시를 바르고 작은 구멍(Ø{tx.IDLER_PRESS})에 끝까지 넣기',
     [['아이들러 축 Ø12×55', 1, 'rod:12:55'], ['에폭시', 0, 'epoxy']], STAND, explode=[0, 0, 70])
step('3. 끝판 A', ['idler_spacer', 'g_idler', 'idler_collar'] + G('brg_idler_*'), '스페이서 3 → 아이들러(베어링 2개 넣은 것) → 칼라 순서로 끼우고 M3×12로 조이기',
     [['30 스페이서 3', 1, 'stl:30_spacer_3'], ['12 아이들러', 1, 'stl:12_gear_idler_z17'], ['베어링 6001', 2, 'brg6001'], ['34 칼라', 1, 'stl:34_collar_M3'], ['M3×12', 1, 'bolt:3:12']],
     STAND, explode=[0, 0, 45])

# ---------------- 4. 축 쌓기 ----------------
in_below = from_A(-117.0); out_below = from_A(-27.0)
step('4. 축 쌓기', ['shaft_in', 'shaft_out'] + G('pspacer_A_*', 'collar_A_*'),
     f'끝판 A를 11cm 받침 위에 올림. 축 2개를 꽂아 바깥면 아래로 입력축 {in_below}mm, 출력축 {out_below}mm가 나오게 맞추고, 바깥면 쪽에 스페이서 9 → 칼라를 밀어 붙여 조이기',
     [['입력축 Ø12×435', 1, 'rod:12:435'], ['출력축 Ø12×358', 1, 'rod:12:358'], ['33 스페이서 9', 2, 'stl:33_spacer_plate_9'], ['34 칼라', 2, 'stl:34_collar_M3'], ['M3×12', 2, 'bolt:3:12']],
     UNDER, explode=[0, 0, 0], note='칼라가 축 위치를 잡아 줘서, 쌓는 동안 축이 미끄러져 내려가지 않음')

def stack(k, gin, gout, extra_new, extra_call, text, pin_up):
    step('4. 축 쌓기', extra_new + [gin, gout, f'pins_{k}'] + G(f'brg_g{k}_*'), text,
         extra_call + [[f'10 입력 {k}단 (이 {tx.PAIRS[k][0]})' if k != 'R' else '10 입력 R (이 17)', 1, f'stl:10_gear_in_{k}_z{tx.PAIRS[k][0] if k != "R" else 17}'],
                       [f'11 출력 {k}단 (이 {tx.PAIRS[k][1]})' if k != 'R' else '11 출력 R (이 41)', 1, f'stl:11_gear_out_{k}_z{tx.PAIRS[k][1] if k != "R" else 41}'],
                       ['에폭시', 0, 'epoxy']],
         STAND, explode=[0, 0, 55], note=f'입력 기어만 축에 에폭시 (출력 기어는 붙이지 않음). 출력 기어 핀은 {"위" if pin_up else "아래"}로')

step('4. 축 쌓기', ['sp_in_end_0', 'sp_out_end_0'], '두 축에 스페이서 3을 1개씩',
     [['30 스페이서 3', 2, 'stl:30_spacer_3']], STAND, explode=[0, 0, 40])
stack('R', 'gin_R', 'gout_R', [], [], 'R 기어 2개 (입력은 이 17, 출력은 이 41)', True)
def sleeve_step(g):
    step('4. 축 쌓기', [f'sp_in_{g}', f'hubw_a_{g}', f'slv_{g}', f'hub_{g}', f'hubw_b_{g}'],
         '입력축: 긴 스페이서 43 / 출력축: 와셔 1 → 슬리브+허브 → 와셔 1',
         [['32 스페이서 43', 1, 'stl:32_spacer_43'], ['31 와셔 1', 2, 'stl:31_spacer_1'], ['슬리브+허브 (2번)', 1, 'stl:21_sleeve_half'], ['에폭시', 0, 'epoxy']],
         STAND, explode=[0, 0, 55], note='허브만 출력축에 에폭시. 와셔·슬리브·베어링에는 묻히지 않기')
sleeve_step('5R')
stack('5', 'gin_5', 'gout_5', [], [], '5단 기어 2개', False)
step('4. 축 쌓기', ['sp_in_end_96', 'sp_out_end_96'], '두 축에 스페이서 3을 1개씩', [['30 스페이서 3', 2, 'stl:30_spacer_3']], STAND, explode=[0, 0, 40])
stack('4', 'gin_4', 'gout_4', [], [], '4단 기어 2개', True)
sleeve_step('34')
stack('3', 'gin_3', 'gout_3', [], [], '3단 기어 2개', False)
step('4. 축 쌓기', ['sp_in_end_192', 'sp_out_end_192'], '두 축에 스페이서 3을 1개씩', [['30 스페이서 3', 2, 'stl:30_spacer_3']], STAND, explode=[0, 0, 40])
stack('2', 'gin_2', 'gout_2', [], [], '2단 기어 2개', True)
sleeve_step('12')
stack('1', 'gin_1', 'gout_1', [], [], '1단 기어 2개', False)
step('4. 축 쌓기', ['sp_in_end_288', 'sp_out_end_288'], '두 축에 스페이서 3을 1개씩. 에폭시가 굳을 때까지 하루 두기', [['30 스페이서 3', 2, 'stl:30_spacer_3']], STAND, explode=[0, 0, 40])

# ---------------- 5. 끝판 B ----------------
step('5. 끝판 B', ['plate_B'] + G('brg_B_*'), '끝판 B 안쪽 면에 베어링 6001 2개', [['41 끝판 B', 1, 'stl:41_plate_B'], ['베어링 6001', 2, 'brg6001']],
     STAND, ctx=[], explode=[0, 0, 0], keep=False)
step('5. 끝판 B', ['cage'], '바깥면에 케이지를 대고 M4×30 4개 (너트는 안쪽 면)',
     [['52 케이지', 1, 'stl:52_selector_cage'], ['M4×30', 4, 'bolt:4:30'], ['M4 너트', 4, 'nut:4']], STAND, ctx=['plate_B'] + G('brg_B_*'), explode=[0, 0, 50], keep=False)
step('5. 끝판 B', ['plate_B', 'cage'] + G('brg_B_*'), '끝판 B를 두 축 위에 내려 끼우기 (아래 변끼리 같은 쪽)',
     [['끝판 B + 케이지', 1, 'stl:41_plate_B']], STAND, explode=[0, 0, 70])
step('5. 끝판 B', G('pspacer_B_*', 'collar_B_*'), '끝판 B 바깥 두 축 끝: 스페이서 9 → 칼라를 밀어 붙이고 M3×12로 조이기',
     [['33 스페이서 9', 2, 'stl:33_spacer_plate_9'], ['34 칼라', 2, 'stl:34_collar_M3'], ['M3×12', 2, 'bolt:3:12']], STAND, explode=[0, 0, 40])

# ---------------- 6. 바닥판 ----------------
step('6. 바닥판', G('foot_*'), '눕혀서 받침 브래킷 4개를 끝판에 M4×30 + 너트로 달고, MDF에 목재나사 4×16 8개로 고정',
     [['42 받침 브래킷', 4, 'stl:42_foot_bracket'], ['M4×30', 4, 'bolt:4:30'], ['M4 너트', 4, 'nut:4'], ['목재나사 4×16', 8, 'wood'], ['MDF 판', 1, 'mdf']],
     LIE_A, explode=[0, -40, 0], note='끝판 A 바깥면을 MDF 왼쪽 끝에서 200mm 안쪽에 두기 (클러치·크랭크 자리 174mm)')

# ---------------- 7. 변속 포크 ----------------
step('7. 변속 포크', G('fork_*'), '포크 3개를 슬리브 링 홈에 위에서 걸치기', [['50 포크', 3, 'stl:50_fork_34']], LIE_B, explode=[0, 50, 0],
     note='1-2단·5-R단 포크는 180° 돌린 같은 모양: 아무거나 써도 됨')
step('7. 변속 포크', G('fwash_*', 'fspring_*', 'fcap_*'), '통마다 와셔 → 큰 스프링 → 와셔 → 뚜껑 (M3×8 2개)',
     [['50b 와셔', 6, 'stl:50b_cart_washer'], ['큰 스프링 C252', 3, 'spring:big'], ['50a 뚜껑', 3, 'stl:50a_fork_cap'], ['M3×8', 6, 'bolt:3:8']], LIE_B, explode=[0, 0, 40])
step('7. 변속 포크', G('rail_*', 'rcol_*'), f'레일 Ø6×{tx.RAIL_LEN:.0f}을 끝판 A 쪽에서 밀어 넣으며 칼라 → 포크 통 → 칼라. 포크를 가운데 두고 칼라 코를 와셔에 대고 M3×10 조이기',
     [[f'레일 Ø6×{tx.RAIL_LEN:.0f}', 3, 'rod:6:371'], ['50c 레일 칼라', 6, 'stl:50c_rail_collar'], ['M3×10', 6, 'bolt:3:10']], LIE_B, explode=[0, 0, 80],
     note='M3×10이 모자라면 M3×12도 됨: 끝이 칼라 밖으로 1.5mm 나오니 칼라를 돌려 나사 끝이 빈 쪽을 보게')
step('7. 변속 포크', G('lug_*'), '케이지 안 레일 끝에 러그. 밑에 작은 스프링 + 쇠구슬, M3×25 2개로 고정 (세 러그 홈이 일직선)',
     [['51 러그', 3, 'stl:51_lug'], ['M3×25', 6, 'bolt:3:25'], ['작은 스프링 C147', 3, 'spring:small'], ['쇠구슬 Ø6', 3, 'ball'], ['M3×8', 3, 'bolt:3:8']], LIE_B, explode=[0, 40, 0])

# ---------------- 8. 레버 ----------------
lock_len = tx.SPRING_L0 - tx.LOCK_F0 / tx.SPRING_K
step('8. 레버', ['carrier'], '잠금판을 세 러그 홈 위에 올리기', [['56 잠금판', 1, 'stl:56_carrier_lockplate']], LIE_B, explode=[0, 40, 0])
step('8. 레버', ['pivot_lo'], '아래 피벗을 케이지 두 벽 사이에 끼우고 M4×30 4개', [['53 아래 피벗', 1, 'stl:53_pivot_lower'], ['M4×30', 4, 'bolt:4:30'], ['M4 너트', 4, 'nut:4']], LIE_B, explode=[0, 50, 0])
step('8. 레버', ['rod', 'lower_lever'], f'레버봉 Ø12×{tx.ROD_LEN:.0f} 끝에 핑거를 에폭시로 붙이고, 위에서 피벗 구멍으로 내리기',
     [[f'레버봉 Ø12×{tx.ROD_LEN:.0f}', 1, 'rod:12:160'], ['57 핑거', 1, 'stl:57_lower_lever_finger'], ['에폭시', 0, 'epoxy']], LIE_B, explode=[0, 70, 0])
step('8. 레버', ['ball'], '볼 반쪽 2개를 레버봉에 끼워 피벗 자리에 앉히기', [['55 볼 반쪽', 2, 'stl:55_ball_half']], LIE_B, explode=[0, 40, 0])
step('8. 레버', ['pivot_hi'], '위 피벗으로 볼을 덮고 M4×30 4개', [['54 위 피벗', 1, 'stl:54_pivot_upper'], ['M4×30', 4, 'bolt:4:30'], ['M4 너트', 4, 'nut:4']], LIE_B, explode=[0, 40, 0])
step('8. 레버', ['spring_spacer', 'lock_collar'], f'스페이서 → 큰 스프링 → 잠금 칼라. 스프링을 {lock_len:.1f}mm로 누르고 M3×12 조이기',
     [['58 스프링 스페이서', 1, 'stl:58_spring_spacer'], ['큰 스프링 C252', 1, 'spring:big'], ['59 잠금 칼라', 1, 'stl:59_lock_collar'], ['M3×12', 1, 'bolt:3:12']], LIE_B, explode=[0, 40, 0],
     inset=dict(target=center('spring_spacer', 'lock_collar'), size=45), tip='스프링 길이는 스페이서 윗면 ~ 칼라 아랫면 사이를 자로 잼')
step('8. 레버', ['gate'], '게이트를 레버봉에 꿰어 케이지 위에 얹고 M4×30 4개', [['60 게이트', 1, 'stl:60_gate'], ['M4×30', 4, 'bolt:4:30'], ['M4 너트', 4, 'nut:4']], LIE_B, explode=[0, 50, 0])
step('8. 레버', ['knob'], '손잡이 안에 에폭시를 바르고 레버봉 끝에 끝까지 끼우기', [['61 손잡이', 1, 'stl:61_knob'], ['에폭시', 0, 'epoxy']], LIE_B, explode=[0, 40, 0])
step('8. 레버', [], 'PTFE 그리스를 톱니·허브·레일에만 얇게 바르고, 입력축을 손으로 돌리며 1~5단·R 넣어 보기 (짧은 핀 단은 세게 돌려 안 빠지는지)',
     [['PTFE 그리스', 0, 'grease']], LIE_A, note='베어링(이미 그리스 있음), 핀, 에폭시 자리에는 바르지 않기')

# ---------------- 9. 클러치 ----------------
CL = '9. 클러치'
hub0, hub1 = from_A(tx.Z_HUB[1]), from_A(tx.Z_HUB[0])
step(CL, ['cl_bracket'] + G('brkbolt_*'), '끝판 A 바깥면에 포크 브래킷을 대고 M4×16 4개 (3번에서 넣어 둔 너트에 물림)',
     [['78 포크 브래킷', 1, 'stl:78_cl_fork_bracket'], ['M4×16', 4, 'bolt:4:16']], CLU, explode=[0, 0, -40])
sub_rel = ['cl_ring', 'cl_relbrg', 'cl_carrier'] + G('cl_push*')
step(CL, sub_rel, '릴리스 링: 육각 홈에 M5 너트 3개, M5×20 3개를 끝까지 조임 → 보스에 베어링 6003 → 바깥에 캐리어를 눌러 끼우기',
     [['75 릴리스 링', 1, 'stl:75_cl_ring'], ['M5×20', 3, 'bolt:5:20'], ['M5 너트', 3, 'nut:5'], ['베어링 6003', 1, 'brg6003'], ['76 캐리어', 1, 'stl:76_cl_carrier']],
     CLUB, ctx=[], keep=False)
step(CL, sub_rel, '릴리스 묶음을 입력축에 끼우기 (캐리어 양옆 돌기가 좌우로)', [['릴리스 묶음', 1, 'stl:75_cl_ring']], CLU, explode=[0, 0, -60])
step(CL, ['cl_fork', 'cl_pivot_bolt'], '포크 두 팔을 돌기 뒤에 걸고, M5×70을 팔 → 볼 → 보스 → 볼 → 팔 순서로 꿰어 나일론 너트를 손으로 닿을 때까지만',
     [['77 클러치 포크', 1, 'stl:77_cl_fork'], ['M5×70', 1, 'bolt:5:70'], ['M5 나일론 너트', 1, 'nut:5']], CLU, explode=[0, 50, 0],
     note='너트를 세게 조이면 포크가 안 돎')
step(CL, ['cl_back', 'cl_cork_b'], '뒷판: 끝판 쪽 면 육각 홈에 M4 너트 3개, 반대 면에 코르크 링을 순간접착제로 붙이기',
     [['71 뒷판', 1, 'stl:71_cl_back'], ['M4 너트', 3, 'nut:4'], ['코르크 링 Ø50/26 두께 2', 1, 'cork'], ['순간접착제', 0, 'ca']], CLU, ctx=[], keep=False)
step(CL, ['cl_hub', 'cl_washer'], '디스크 허브 플랜지에 강철 와셔 M16(바깥 50)을 에폭시로 붙이고 하루 굳히기',
     [['74 디스크 허브', 1, 'stl:74_cl_disc_hub'], ['큰 와셔 DIN9021 M16', 1, 'washer50'], ['에폭시', 0, 'epoxy']], CLU, ctx=[], keep=False)
step(CL, ['cl_press', 'cl_cork_p'], '압력판: 매끈한 바닥면(출력 때 아래 면)에 코르크 링 붙이기',
     [['72 압력판', 1, 'stl:72_cl_pressure'], ['코르크 링', 1, 'cork'], ['순간접착제', 0, 'ca']], CLUB, ctx=[], keep=False)
front_sub = ['cl_front', 'cl_pilot'] + G('cpl_pin*', 'cl_adj*', 'cl_cup*')
step(CL, front_sub, f'앞판: 바깥면에 베어링 6001, 핀 Ø5×{tx.CPL_PIN_LEN:.0f} 6개를 인두로 15mm 깊이까지 (25mm 나옴), 둘레 홈에 M5 너트 3개 + M5×10 끝까지, 안쪽 홈에 스프링 컵 3개',
     [['70 앞판', 1, 'stl:70_cl_front'], ['베어링 6001', 1, 'brg6001'], ['평행핀 Ø5×40', 6, 'pin5x40'], ['M5×10', 3, 'bolt:5:10'], ['M5 너트', 3, 'nut:5'], ['79 스프링 컵', 3, 'stl:79_cl_spring_cup']],
     CLU, ctx=[], keep=False, note='M5×10을 끝까지 = 기본 세기. M5×12 이상은 쓰지 않기 (기어가 못 버팀)')
step(CL, ['cl_back', 'cl_cork_b'], '뒷판을 입력축에 끼우기 (코르크가 바깥쪽)', [['뒷판', 1, 'stl:71_cl_back']], CLU, explode=[0, 0, -60])
step(CL, ['cl_hub', 'cl_washer'], f'입력축의 끝판 A 바깥면에서 {hub0}~{hub1}mm 구간에 에폭시를 얇게 바르고, 허브를 와셔가 뒷판 코르크에 닿을 때까지 밀기',
     [['허브+와셔', 1, 'stl:74_cl_disc_hub'], ['에폭시', 0, 'epoxy']], CLU, explode=[0, 0, -50],
     note='와셔를 코르크에 손으로 붙인 채 몇 분 잡고, 하루 굳힌 뒤 다음 단계. 에폭시가 릴리스 링 쪽(바깥면에서 14~30mm)으로 흐르지 않게',
     tip='축에 유성펜으로 40mm·73mm 두 곳을 표시하고 그 사이에만 바르기')
step(CL, ['cl_press', 'cl_cork_p'] + G('cl_spring*', 'cl_standoff*'), '압력판(코르크가 와셔 쪽) → 스프링 3개를 압력판 자리에 → 기둥 3개',
     [['압력판', 1, 'stl:72_cl_pressure'], ['큰 스프링 C252', 3, 'spring:big'], ['73 기둥', 3, 'stl:73_cl_standoff']], CLU, explode=[0, 0, -50])
step(CL, front_sub + G('cl_bolt*'), '앞판을 덮고 M4×60 3개로 앞판 → 기둥 → 뒷판 너트까지 끝까지 조이기. 축을 돌리지 말고 하루 두기',
     [['앞판 묶음', 1, 'stl:70_cl_front'], ['M4×60', 3, 'bolt:4:60']], CLU, explode=[0, 0, -60])
step(CL, ['cl_endsp', 'cl_endcollar'], '끝 와셔(1mm) → 끝 칼라를 파일럿 베어링에 밀어 붙이고 M3×12',
     [['79b 끝 와셔', 1, 'stl:79b_cl_end_spacer'], ['35 끝 칼라', 1, 'stl:35_collar_end_8'], ['M3×12', 1, 'bolt:3:12']], CLU, explode=[0, 0, -40])

# ---------------- 10. 크랭크 ----------------
KR = '10. 크랭크'
step(KR, ['crank_arm', 'crank_peg'], '손잡이 축의 가는 끝에 에폭시를 바르고 팔 끝 구멍에 끝까지 (어깨가 팔에 닿게). 하루 굳히기',
     [['35b 크랭크 팔', 1, 'stl:35b_crank_arm'], ['35c 손잡이 축', 1, 'stl:35c_crank_peg'], ['에폭시', 0, 'epoxy']], CLU, ctx=[], explode=[0, 0, -40], keep=False)
step(KR, ['crank_grip', 'crank_cap'], '손잡이 통을 축에 끼우고 뚜껑 + M3×12', [['35d 손잡이 통', 1, 'stl:35d_crank_grip'], ['35e 뚜껑', 1, 'stl:35e_crank_cap'], ['M3×12', 1, 'bolt:3:12']],
     CLU, ctx=['crank_arm', 'crank_peg'], explode=[0, 0, -50], keep=False)
step(KR, ['crank_arm', 'crank_peg', 'crank_grip', 'crank_cap', 'crank_screw'], '크랭크를 앞판 핀 6개에 끝까지 끼우고, 옆 구멍에 M3×12를 핀에 닿을 때까지 조이기',
     [['크랭크 묶음', 1, 'stl:35b_crank_arm'], ['M3×12', 1, 'bolt:3:12']], CLU, explode=[0, 0, -60],
     inset=dict(target=center('crank_screw'), size=40), note='M3×12는 핀을 누르기만 함. 세게 조이면 허브가 갈라짐')

# ---------------- 11. 페달 ----------------
PD = '11. 페달'
step(PD, ['ped_base'], '페달 받침을 MDF(남는 판)에 목재나사 4×16 4개로 고정', [['82 페달 받침', 1, 'stl:82_pedal_base'], ['목재나사 4×16', 4, 'wood']], PED, ctx=[], explode=[0, 40, 0], keep=False)
step(PD, ['ped_arm', 'ped_bolt'], '팔 왼쪽 면 육각 홈에 M6 나일론 너트, 왼쪽 볼에서 M6×25를 머리가 볼에 닿을 때까지만',
     [['80 페달 팔', 1, 'stl:80_pedal_arm'], ['M6×25', 1, 'bolt:6:25'], ['M6 나일론 너트', 1, 'nut:6']], PED, ctx=['ped_base'], explode=[-40, 0, 0], keep=False)
step(PD, ['ped_spring', 'ped_pad'], f'팔 앞면 자리와 받침 보스 사이에 큰 스프링, 발판을 M4×25 2개 (너트는 팔 앞면 홈)',
     [['큰 스프링 C252', 1, 'spring:big'], ['81 발판', 1, 'stl:81_pedal_pad'], ['M4×25', 2, 'bolt:4:25'], ['M4 너트', 2, 'nut:4']], PED, ctx=['ped_base', 'ped_arm', 'ped_bolt'], explode=[0, 0, -30], keep=False)
step(PD, ['ped_cable'], '케이블 속선을 팔 앞면 구멍에 넣어 니플을 걸고, 아우터를 받침 자리에 꽂기',
     [['자전거 브레이크 케이블', 1, 'cable']], PED, ctx=['ped_base', 'ped_arm', 'ped_bolt', 'ped_spring', 'ped_pad'], keep=False)
step(PD, [], '아우터를 끝판 B 구멍(Ø6) → 기어박스 안 → 끝판 A 안쪽 홈까지 넣고, 속선을 포크 위 구멍으로. 페달을 뗀 채 속선을 팽팽하게 당겨 M3×10 + 와셔로 누르기',
     [['M3×10', 1, 'bolt:3:10'], ['M3 와셔', 1, 'washer3']], CLU, note='끝판 B 구멍은 입력축 바로 위 92mm', inset=dict(target=[0, tx.FORK_CABLE_Y, -20], size=60))
step('완성', [], '페달을 떼고 크랭크를 돌리면 기어가 돎. 페달을 밟은 채 변속 → 천천히 떼기',
     [], CLU, note='돌리는 중에는 클러치에 손가락 넣지 않기')

json.dump(S, open(os.path.join(HERE, 'steps.json'), 'w'), ensure_ascii=False, indent=0)
print(len(S), 'steps')
