"""v4 하중·강도 계산서 (모든 수치는 이 파일에서 계산 → calc_result.json, calc_report.md)
단위: N, mm, MPa, N·mm (회전관성은 kg·m², 각속도 rad/s)
출처는 SRC 에 모아 두고 보고서에 함께 출력합니다. '가정' 은 측정으로 바꿔야 할 값입니다.
"""
import math, json, sys
import numpy as np
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # src/
sys.path.insert(0, ROOT)
import tx, trimesh

SRC = {
    'TDS': 'UltiMaker PLA 기술자료 v5.00 (출력 시편 0.15mm, 채움 100%): https://www.alloys.com.au/Documents/Ultimaker-PLA-TDS-v5.00.pdf',
    'FAT': 'Ezeh & Susmel (2018) On the fatigue strength of 3D-printed PLA, Procedia Struct. Integrity 9: 설계 곡선(생존확률 95%) 200만 회 피로강도 = 인장강도의 10%, 기울기 k=5.5, 평균응력은 최대응력으로 처리: https://eprints.whiterose.ac.uk/id/eprint/133457/',
    'CORK': 'RoyMech 브레이크·클러치 마찰재 표: 코르크-주철/강 건식 μ 0.3~0.5, 최대압력 0.1 MPa, 최고온도 100°C: https://roymech.org/Useful_Tables/Drive/Brake_Clutch_mat.html',
    'MU_PLA': 'PLA-강 건식 마찰계수 0.30(정지, 30N)·0.49(핀온디스크): https://tribology.rs/journals/2024/2024-1/9-1546.pdf , https://engmechx.it.cas.cz/improc/2018/649.pdf',
    'B6001': '6001-2Z: C=5.1 kN, C0=2.4 kN: https://www.simplybearings.co.uk/products/6001-2z-eu',
    'C252': f'압축 스프링 (C252 대신 기성품): 스프링팜 SUS304 선경1.5 외경18 자유장{tx.SPRING_L0:.0f} (쿠팡 4387963066), 권수 약 5.5 사진 판독 → k {tx.SPRING_K} N/mm (받으면 걸이 저울로 실측해 tx.SPRING_K), 밀착 {tx.SPRING_SOLID}',
    'C147': '디텐트 스프링 (C147 대신 기성품): 스프링팜 SUS304 선경0.4 외경5 자유장10 (쿠팡 8501265889), 권수 약 6 → k 0.57 N/mm, 5mm 에서 2.85N, 밀착 2.4',
    'MOTOR': '모터 라벨 GGM K9DP90N2: DC24V 90W 3000rpm 5.9A / 감속기 K9P9BH 1:9 (2026-10-19 사진·판매처 목록)',
    'HAND': 'Das & Black (2000) 한 손 당김 최대 473N(남, 앉은 자세), NBSIR 73-156 (1973) 2~6세 당김 95백분위 ~296N: https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir73-156.pdf',
    'GENT': 'Gent (1958) 쇼어 A 경도-영률 관계식 (고무 쿠션 강성 추정)',
    'WS': 'Wellauer & Seireg (1960) 외팔 판 집중하중: 뿌리 최대 모멘트 ≈ 0.51F (등가폭 ≈ 1.96×하중 높이)',
    'FEM': '이 계산서의 2D 유한요소 해석 (calc/fem_tooth.py, 실제 출력 이 모양, 이끝 하중)',
}

# ================= 1. 데이터 =================
PLA = dict(E=3000.0, nu=0.35, UTS_XY=45.5, UTS_Z=33.1, YLD_XY=52.5, FLEX_XY=96.8, HDT=58.8, rho=1.24e-3)   # rho g/mm³
def fatigue_allow(UTS, N):
    """Ezeh & Susmel 설계 곡선 (95%): N 회에서 허용 최대응력"""
    N = max(N, 1e3)
    return 0.10 * UTS * (2e6 / min(N, 2e6)) ** (1 / 5.5)
STEEL = dict(E=200000.0, G=80000.0, Y=235.0, rho=7.85e-3)      # 연마봉 재질 미확인 → 일반 구조용강 최저 항복 235 가정
CORK = dict(mu_lo=0.30, mu_hi=0.50, mu_nom=0.40, pmax=0.10, Tmax=100.0)
C252 = dict(L0=tx.SPRING_L0, k=tx.SPRING_K, P2L=tx.SPRING_SOLID + 1.0, tol=tx.SPRING_TOL)   # 기성품: 밀착 + 1mm 보다 짧게 쓰지 않음, 하중 ±10% 가정
C147 = dict(L0=10.0, k=0.57)
B6001 = dict(C=5100.0, C0=2400.0)
F_KNOB = 400.0                      # 손잡이 설계 하중 (HAND 근거)

R = {'src': SRC, 'assume': {}}
A = R['assume']

# ================= 2. 속도 =================
T_RATED_MOTOR = 90.0 / (2 * math.pi * 3000 / 60)                 # 0.2865 N·m
RATIO_GH = 9.0
W_IN_NOM = 2 * math.pi * (1500 / RATIO_GH) / 60                 # 12V 무부하 1500rpm 가정 → 167rpm
W_IN_MAX = 2 * math.pi * 200 / 60                                # 무부하 속도 +20% 여유 (충격 계산용)
A['motor_12V_noload_rpm'] = '1500 (24V 정격 3000rpm 의 절반, 미측정) → 감속기 출력 167rpm, 충격 계산은 200rpm'
r_gear = {k: zi / zo for k, (zi, zo) in tx.PAIRS.items()}
r_gear['R'] = -tx.REV[0] / tx.REV[2]
R['speeds_rpm'] = {k: round(1500 / RATIO_GH * abs(v)) for k, v in r_gear.items()}

# ================= 3. 회전관성 (CAD 형상 x 밀도, 속 채움 100% = 위쪽 한계) =================
def J_about(m, axis_xy, rho):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(vertices=np.array(mesh.vert_properties)[:, :3], faces=np.array(mesh.tri_verts))
    t.density = rho * 1e3            # g/mm³ → kg/m³ 스케일은 아래에서 처리
    # trimesh 는 단위 무관: 질량[g]=V[mm³]*rho[g/mm³], J[g·mm²] → kg·m² 는 1e-9
    mp = t.mass_properties
    m_g = abs(t.volume) * rho
    I = mp['inertia'] / mp['mass'] * m_g if mp['mass'] != 0 else np.zeros((3, 3))
    c = mp['center_mass']
    # z 축(축 위치 axis_xy)에 대한 관성: 무게중심 기준 Izz + m*d²
    d2 = (c[0] - axis_xy[0]) ** 2 + (c[1] - axis_xy[1]) ** 2
    return m_g, (I[2, 2] + m_g * d2) * 1e-9

def gear_J(z, fixed=True):
    m = tx.fixed_gear(z) if fixed else tx.free_gear(z)
    return J_about(m, (0, 0), PLA['rho'])

J = {}
Jin_shaft = 0.5 * (STEEL['rho'] * math.pi * 36 * 435) * 36 * 1e-9          # Ø12 x 435
J['input_shaft'] = Jin_shaft
for k, (zi, zo) in tx.PAIRS.items():
    J[f'gin_{k}'] = gear_J(zi)[1]
    J[f'gout_{k}'] = gear_J(zo, False)[1]
J['gin_R'] = gear_J(17)[1]; J['g_idler'] = gear_J(17, False)[1]; J['gout_R'] = gear_J(41, False)[1]
J['disc'] = J_about(tx.cl_disc_hub(), (0, 0), PLA['rho'])[1] + 0.5 * (STEEL['rho'] * math.pi * (25 ** 2 - 8.5 ** 2) * 3) * (25 ** 2 + 8.5 ** 2) * 1e-9
J['hub'] = J_about(tx.hub(), (0, 0), PLA['rho'])[1]
J['sleeve'] = J_about(tx.sleeve_half(), (0, 0), PLA['rho'])[1] * 2 + J_about(tx.sleeve_ring(), (0, 0), PLA['rho'])[1]
J['wheel'] = J_about(tx.display_wheel(), (0, 0), PLA['rho'])[1]
J['output_shaft'] = 0.5 * (STEEL['rho'] * math.pi * 36 * 358) * 36 * 1e-9
J['pins'] = 6 * 4 * (STEEL['rho'] * math.pi * 6.25 * 25) * (35.5 ** 2) * 1e-9
# 입력쪽 (입력축 기준): 입력축·입력 기어·디스크 + 출력 공회전 기어·아이들러를 입력축으로 환산
J_in = J['input_shaft'] + J['disc'] + sum(J[f'gin_{k}'] for k in tx.PAIRS) + J['gin_R']
J_pin_gear = J['pins'] / 6                                              # 출력 기어 1개의 핀 4개
J_in += sum((J[f'gout_{k}'] + J_pin_gear) * (zi / zo) ** 2 for k, (zi, zo) in tx.PAIRS.items())
J_in += J['g_idler'] * 1.0 + (J['gout_R'] + J_pin_gear) * (17 / 41) ** 2
J_out = J['output_shaft'] + 3 * J['hub'] + 3 * J['sleeve'] + J['wheel']
R['inertia_kgm2'] = {k: float(f'{v:.3g}') for k, v in J.items()}
R['inertia_kgm2']['J_in(입력축 기준)'] = float(f'{J_in:.3g}'); R['inertia_kgm2']['J_out(출력축)'] = float(f'{J_out:.3g}')

# ================= 4. 필요 토크와 클러치 =================
T_DRAG = 0.10e3          # N·mm, 가정 (조립 후 측정, 합격 기준 0.15 N·m 이하)
A['drag_torque'] = '입력축 기준 끌림 토크 0.10 N·m (미측정: 2단계 조립 후 걸이 저울로 측정, 0.15 이하이면 합격)'
J1 = J_in + J_out * (17 / 49) ** 2
T_need = T_DRAG + J1 * (W_IN_NOM / 0.3) * 1e3
R['torque_need_Nm'] = {'끌림(가정)': T_DRAG / 1e3, '1단에서 0.3초 만에 최고속도까지 가속': round(J1 * (W_IN_NOM / 0.3), 4),
                       '합계': round(T_need / 1e3, 3)}

r_o, r_i = tx.CORK[1], tx.CORK[0]
r_eff_new = (2 / 3) * (r_o ** 3 - r_i ** 3) / (r_o ** 2 - r_i ** 2)       # 새 클러치(균일 압력)
r_eff_worn = (r_o + r_i) / 2                                            # 길든 뒤(균일 마모)
# 스프링 길이 = 컵 윗면(앞판 스프링 쪽 면에서 s 아래) ~ 압력판 스프링 자리 홈(깊이 2) 바닥
L_of_s = lambda s: (tx.Z_PRESS[0] + 2.0) - (tx.Z_FRONT[1] - s - 3.0 + tx.CUP_T)   # = 24 + s + 3 - CUP_T (컵 높이)
S_OF_BOLT = lambda L: 13.0 - L                                          # 조절나사 길이 L 을 끝까지 조였을 때 s
S_MIN = S_OF_BOLT(10.0)                                                 # v4.1: M5x10 끝까지 조임 = 설정값 (s=3, 스프링 27mm)
F_spr = lambda L: 3 * C252['k'] * (C252['L0'] - L)
Tc = lambda F, mu, r: 2 * mu * F * r                                     # 마찰면 2개
rows = []
for bl in (8.0, 10.0, 12.0):
    s = S_OF_BOLT(bl); F = F_spr(L_of_s(s))
    rows.append({'조절나사': f'M5x{bl:.0f}' + (' (설정)' if bl == 10.0 else ' (금지: 기어 설계 하중 초과)' if bl > 10 else ' (약하게)'),
                 's_mm': s, '스프링길이': round(L_of_s(s), 2), '누르는 힘N': round(F, 1),
                 'Tc μ0.3': round(Tc(F, 0.3, r_eff_worn) / 1e3, 2), 'Tc μ0.4': round(Tc(F, 0.4, r_eff_worn) / 1e3, 2),
                 'Tc μ0.5(새것)': round(Tc(F, 0.5, r_eff_new) / 1e3, 2)})
F_MAX = F_spr(L_of_s(S_MIN))
TC_MAX = Tc(F_MAX * (1 + C252['tol']), CORK['mu_hi'], r_eff_new)        # 설정(M5x10 끝까지) + 스프링 +10% + 마찰계수 최대(0.5, 새것) = 설계 하중
TC_NOM = Tc(F_MAX, CORK['mu_nom'], r_eff_worn)                         # 끝까지 조임 + μ0.4 (0.58 N·m)
cork_area = math.pi * (r_o ** 2 - r_i ** 2)
R['clutch'] = {'설정표': rows, 'Tc_max_Nm(설정 M5x10 + 스프링 +10% + μ0.5 새것 = 설계 하중)': round(TC_MAX / 1e3, 3), 'Tc_nom_Nm(끝까지 조임, μ0.4)': round(TC_NOM / 1e3, 2),
               '필요토크 대비 여유(공칭)': round(TC_NOM / T_need, 1),
               '코르크 압력 최대 MPa': round(F_MAX / cork_area, 4), '코르크 허용 MPa': CORK['pmax'],
               '스프링 최대 사용 길이(뗄 때) mm': round(L_of_s(S_MIN) - 1.5, 2), '스프링 최소 허용 길이 mm(밀착 + 1)': C252['P2L']}
# 떼는 힘·페달
F_rel = F_spr(L_of_s(S_MIN) - 1.5) * 1.1           # 마찰 10%
fork_ratio = (tx.FORK_CABLE_Y - tx.FORK_PIV_Y) / (tx.FORK_PIV_Y - tx.H)
cable_F = F_rel / fork_ratio
pedal_ratio = tx.PEDAL_PAD_B / tx.PEDAL_CABLE_B
R['clutch']['떼는 힘 N(압력판)'] = round(F_rel, 1)
R['clutch']['포크 지렛대비'] = round(fork_ratio, 2)
R['clutch']['케이블 장력 N'] = round(cable_F, 1)
R['clutch']['페달 발 힘 N(복귀 스프링 제외, 케이블 30mm 구멍, 발판 180)'] = round(cable_F / pedal_ratio, 1)
PEDAL_STOP_L = tx.PEDAL_SPR_L - 7.81                                    # 복귀 스프링 끝 길이 (쉴 때보다 7.81 짧음, asm.pedal_check)
F_ret = C252['k'] * (C252['L0'] - PEDAL_STOP_L)
R['clutch']['페달 복귀 스프링 힘 N(끝, 발판 기준)'] = round(F_ret * tx.PEDAL_SPR_B / tx.PEDAL_PAD_B, 1)
R['clutch']['페달 행정 mm(발판, 압력판 1.5 + 유격 1.0)'] = round((1.5 + 1.0) * fork_ratio * pedal_ratio, 1)
R['clutch']['페달 끝 멈춤 각 도(릴리스 링 3.0, 뒷판까지 3.5)'] = round(tx.PEDAL_TRAVEL, 1)
# 발열
P_jam = TC_MAX * W_IN_NOM / 1e3                                       # W
E_eng = 0.5 * J1 * W_IN_NOM ** 2 * 2                                  # 한 번 물릴 때 미끄럼 손실 ≈ 얻는 운동에너지 x1 (x2 여유)
m_wash = STEEL['rho'] * math.pi * ((tx.WASHER[1] / 2) ** 2 - (tx.WASHER[0] / 2) ** 2) * tx.WASHER[2]   # g
C_wash = m_wash * 0.46                                                # J/K
R['clutch_heat'] = {'1회 물림 손실 J': round(E_eng, 3), '와셔 열용량 J/K': round(C_wash, 1),
                    '막힘(출력 멈춤) 미끄럼 발열 W': round(P_jam, 1),
                    '5초(펌웨어 막힘 차단) 와셔 온도 상승 K': round(P_jam * 5 / C_wash, 1),
                    '60초(운영자 비상정지) 와셔 온도 상승 K': round(P_jam * 60 / C_wash, 1),
                    '코르크 최고온도 °C': CORK['Tmax'], 'PLA HDT °C': PLA['HDT']}

# ================= 5. 축 (보 모델) =================
def section(double=True):
    from shapely.geometry import Point, box
    p = Point(0, 0).buffer(6.0, 256).intersection(box(-5 if double else -6, -6, 5, 6))
    xy = np.array(p.exterior.coords)
    x, y = xy[:, 0], xy[:, 1]
    cr = x[:-1] * y[1:] - x[1:] * y[:-1]
    Ix = abs(np.sum(cr * (y[:-1] ** 2 + y[:-1] * y[1:] + y[1:] ** 2)) / 12)
    Iy = abs(np.sum(cr * (x[:-1] ** 2 + x[:-1] * x[1:] + x[1:] ** 2)) / 12)
    return p.area, min(Ix, Iy), Ix + Iy
A_sh, I_sh, Jp_sh = section(True)
R['shaft_section'] = {'단면적 mm2': round(A_sh, 1), 'I_min mm4': round(I_sh, 1), 'J_p mm4(근사)': round(Jp_sh, 1)}
SUP = (-4.0, tx.STACK + 4.0)            # 베어링 중심

def beam(loads, L0=SUP[0], L1=SUP[1], n=1200):
    """단순지지보: loads=[(z, F)], 반력·처짐·기울기 (수치적분)"""
    z = np.linspace(L0, L1, n); L = L1 - L0
    Rb = sum(F * (zz - L0) for zz, F in loads) / L; Ra = sum(F for _, F in loads) - Rb
    Mz = Ra * (z - L0) - sum(np.where(z > zz, F * (z - zz), 0) for zz, F in loads)
    k = Mz / (STEEL['E'] * I_sh)
    th = np.concatenate([[0], np.cumsum((k[1:] + k[:-1]) / 2 * np.diff(z))])
    w = np.concatenate([[0], np.cumsum((th[1:] + th[:-1]) / 2 * np.diff(z))])
    w -= w[-1] * (z - L0) / L; th = np.gradient(w, z)
    return z, Mz, w, th, Ra, Rb

shaft_rows = []
for k, (zi, zo) in list(tx.PAIRS.items()) + [('R', (17, 41))]:
    zc = tx.PLANE[k] + tx.FW / 2
    Ft = 2 * TC_MAX / (tx.MOD * zi); Fn = Ft / math.cos(tx.PA)
    zz, Mz, w, th, Ra, Rb = beam([(zc, Fn)])
    i = np.argmin(abs(zz - zc))
    T = TC_MAX if True else 0
    sig_b = abs(Mz).max() * 6.0 / I_sh                 # 최대 굽힘 (반지름 6)
    tau = TC_MAX * zo / zi * 6.0 / Jp_sh if k != 'R' else TC_MAX * 41 / 17 * 6.0 / Jp_sh
    vm = math.sqrt(sig_b ** 2 + 3 * tau ** 2)
    shaft_rows.append({'단': k, '이 힘 N': round(Fn, 1), '처짐 mm(한 축)': round(abs(w[i]), 4), '기울기 μm/mm': round(abs(th[i]) * 1e3, 3),
                       '굽힘+비틀림 MPa': round(vm, 1), 'SF(항복235)': round(STEEL['Y'] / vm, 1),
                       '베어링 반력 최대 N': round(max(abs(Ra), abs(Rb)), 1)})
R['shafts'] = shaft_rows
# 클러치 쪽 내밀린 입력축: 커플링 핀 1개가 모든 토크를 받는 최악 (정렬 오차) → 반지름 방향 힘 = TC_MAX/r
F_cpl = TC_MAX / tx.CPL_PIN_R
a_over = (tx.Z_FRONT[0] + 4) - (-4.0)            # 파일럿 베어링 ~ A 베어링 거리
M_over = F_cpl * abs(a_over)
R['shaft_overhang'] = {'반지름 힘 N': round(F_cpl, 1), '모멘트 N·mm': round(M_over), '굽힘 MPa': round(M_over * 6 / I_sh, 1),
                       '끝 처짐 mm': round(F_cpl * abs(a_over) ** 3 / (3 * STEEL['E'] * I_sh), 3)}

# ================= 6. 기어 이뿌리·면압 =================
fem = {(d['z'], d['fillet']): d['sigma_t_per_Nmm'] for d in json.load(open(os.path.join(ROOT, 'calc', 'fem_tooth.json')))}
c_gamma = 20.0 * PLA['E'] / 206000 * 0.85          # 맞물림 강성 N/(mm·μm): ISO 강철 대표값 20 x 탄성계수비 x 0.85
F_BX = 50.0                                         # μm: 출력 이 방향 오차 가정
A['lead_error'] = 'FDM 출력 기어 이 방향(리드) 오차 50 μm 가정 (미측정) + 축 기울기 x 이 폭'
NF = (25 / 6.75) ** 2 / (1 + 25 / 6.75 + (25 / 6.75) ** 2)
KV_of = lambda zi: (6.1 + W_IN_MAX * tx.MOD * zi / 2 / 1000) / 6.1   # Barth: 그 단 입력 기어 피치원 속도 (m/s)
KV = KV_of(17)
def KFb(Ft, slope_um_per_mm, kv=1.0):
    """ISO 6336-1 방법 C (v4.1: v4 의 상한 2.41 없앰 — 독립 검산에서 끝단 하중이면 2.6~2.8 → ISO 값 그대로가 더 안전)"""
    Fby = F_BX + slope_um_per_mm * tx.FW
    wm = Ft * kv / tx.FW                            # N/mm (F_m = Ft·K_A·K_V, K_A=1)
    x = Fby * c_gamma / (2 * wm)
    KHb = 1 + x if x <= 1 else math.sqrt(2 * Fby * c_gamma / wm)
    return KHb ** NF, KHb
ZE = math.sqrt(PLA['E'] / (2 * math.pi * (1 - PLA['nu'] ** 2)))
def gear_case(name, zp, zg, T_p, slope, N_cycles, label):
    """zp: 하중이 걸리는 작은 기어(피니언), T_p: 그 기어 토크 N·mm"""
    Ft = 2 * T_p / (tx.MOD * zp)
    kv = KV_of(17 if name == 'R' else tx.PAIRS[name][0])
    kfb, khb = KFb(Ft, slope, kv)
    out = {}
    for z in (zp, zg):
        s = fem[(z, 'gen')] * Ft / math.cos(tx.PA) / tx.FW * kv * kfb    # FEM 계수는 법선 하중 기준 → Fn = Ft/cos20° (E1)
        allow_f = fatigue_allow(PLA['UTS_XY'], N_cycles)
        out[z] = (round(s, 2), round(PLA['UTS_XY'] / s, 1), round(allow_f / s, 2))
    u = zg / zp
    sH = 2.49 * ZE * math.sqrt(Ft / (tx.FW * tx.MOD * zp) * (u + 1) / u * khb)
    return {'경우': label, '단': name, 'Ft N': round(Ft, 1), 'K_V': round(kv, 3), 'KFβ': round(kfb, 2),
            f'z{zp} 응력MPa/정적SF/피로SF': out[zp], f'z{zg} 응력MPa/정적SF/피로SF': out[zg],
            '면압 MPa': round(sH, 1), '반복수': N_cycles}
gear_rows = []
slopes = {r['단']: r['기울기 μm/mm'] for r in shaft_rows}
for k, (zi, zo) in list(tx.PAIRS.items()) + [('R', (17, 41))]:
    zp, zg = (zi, zo) if zi <= zo else (zo, zi)
    Tp = TC_MAX if zi <= zo else TC_MAX * zo / zi
    gear_rows.append(gear_case(k, zp, zg, Tp, 2 * slopes[k], 1e4, '클러치 최대 토크(물릴 때 순간) 1만 회'))
    Td = T_DRAG * 1.25 if zi <= zo else T_DRAG * 1.25 * zo / zi
    gear_rows.append(gear_case(k, zp, zg, Td, 0.0, 2e6, '계속 운전(끌림 x1.25) 200만 회'))
    gear_rows.append(gear_case(k, zp, zg, Tp, 2 * slopes[k], 2e6, '(가상) 클러치 최대 토크가 계속 걸림 200만 회'))
R['gears'] = gear_rows
R['gear_factors'] = {'FEM 응력계수 MPa/(N/mm) v4.1 랙 창성(17T +0.3, 49T -0.3 전위)': {z: fem[(z, 'gen')] for z in sorted({z for z, f in fem})},
                     'v4 직선 뿌리 + 필렛 R1.0 (참고)': {z: fem[(z, 1.0)] for z in sorted({z for z, f in fem})},
                     'v3 각진 뿌리 (참고)': {z: fem[(z, 0.0)] for z in sorted({z for z, f in fem})},
                     'K_V(Barth, 1단~5단)': f"{KV_of(17):.3f}~{KV_of(36):.3f}", 'N_F': round(NF, 3), 'c_γ N/(mm·μm)': round(c_gamma, 3)}

# ================= 7. 핀 도그 충격 (고무 쿠션) =================
E_rub = 0.0981 * (56 + 7.62336 * 70) / (0.137505 * (254 - 2.54 * 70))        # Gent, 쇼어 70A
A_c, t_r = 5.0 * 4.0, 2.5                                                   # 눌리는 넓이(물림 5 x 원호 4), 고무 두께
S_f = A_c / (2 * (5 + 4) * t_r)
k_pin = E_rub * (1 + 2 * S_f ** 2) * A_c / t_r                              # N/mm (핀 1개)
N_EFF = 2.0                                                                 # 출력 오차로 4개 중 2개만 먼저 닿는다고 가정
k_th = N_EFF * k_pin * tx.PIN_R ** 2 * 1e-3                                 # N·m/rad
A['cushion'] = f'NBR 쇼어 70A (E≈{E_rub:.1f} MPa, Gent), 호스 안5 x 바깥10 (두께 2.5), 4개 중 2개가 받는다고 가정'
def J_eff_gear(k):
    zi, zo = (17, 41) if k == 'R' else tx.PAIRS[k]
    J_in_ref = J_in * (zo / zi) ** 2
    return J_out * J_in_ref / (J_out + J_in_ref)
imp_rows = []
cases = [('4→5 (순서대로, 가장 큰 차)', '5', W_IN_MAX * abs(r_gear['5'] - r_gear['4'])),
         ('5→1 (건너뛰기)', '1', W_IN_MAX * abs(r_gear['1'] - r_gear['5'])),
         ('5단 달리다 바로 R (오조작 최악)', 'R', W_IN_MAX * abs(r_gear['R'] - r_gear['5']))]
for label, k, dw in cases:
    Je = J_eff_gear(k)
    E = 0.5 * Je * dw ** 2
    T_pk = math.sqrt(2 * E * k_th)                                         # N·m
    F_pin = T_pk * 1e3 / tx.PIN_R / N_EFF
    a = 3.5; d = tx.PIN_D; e = tx.PIN_IN
    p_hole = F_pin / (d * e) * (4 + 6 * a / e)                              # 기어 구멍 테두리 최대 압력 (강체 핀-탄성 기초)
    sig_pin = F_pin * a * 32 / (math.pi * d ** 3)
    p_rub = F_pin / A_c
    # 포켓: 쿠션(바깥 8)이 포켓 끝 반원(4.15)에 닿는 면 → 투영 압력
    p_pock = F_pin / (tx.CUSH_OD * 5.0)
    # 허브 양면 D: 두 면이 나눠 받음, 각 면 가장자리 최대 압력
    wh = math.sqrt(6.0 ** 2 - 5.0 ** 2)
    p_D = (T_pk * 1e3) / (2 * (2 * wh / 3)) * 2 / (tx.HUB_BODY * wh)      # D구멍 길이 = 허브 몸통 41 (E3)
    # 이 (충격 토크가 맞물림을 지나감): 걸린 단의 작은 기어
    zi, zo = (17, 41) if k == 'R' else tx.PAIRS[k]
    zp = min(zi, zo, 17 if k == 'R' else 99)
    T_gear_out = T_pk * 1e3
    Ft = 2 * T_gear_out / (tx.MOD * zo)
    kfb, _ = KFb(Ft, 0.0)
    s_tooth = fem[(zp, 'gen')] * Ft / math.cos(tx.PA) / tx.FW * kfb
    imp_rows.append({'경우': label, 'Δω rad/s': round(dw, 1), 'J_eff kg·m²': float(f'{Je:.3g}'), '에너지 J': round(E, 4),
                     '최대 토크 N·m': round(T_pk, 2), '핀 1개 힘 N': round(F_pin, 1),
                     '고무 눌림 %(두께 2.5)': round(F_pin / k_pin / t_r * 100),
                     '고무 압력 MPa': round(p_rub, 2), '핀 굽힘 MPa(강)': round(sig_pin, 1),
                     '기어 핀구멍 압력 MPa': round(p_hole, 1), 'SF(항복52.5)': round(PLA['YLD_XY'] / p_hole, 1),
                     '포켓 압력 MPa': round(p_pock, 1), '허브 D면 MPa': round(p_D, 1), 'SF D면': round(PLA['YLD_XY'] / p_D, 1),
                     '이뿌리 MPa(작은 기어)': round(s_tooth, 1), '작은 기어 잇수': zp, 'SF 이(인장45.5)': round(PLA['UTS_XY'] / s_tooth, 1)})
# 비교: 쿠션 없이 강철핀-PLA 직접 (같은 에너지, 강성 ~8850 N/mm/핀)
k_th_rigid = N_EFF * 8850 * tx.PIN_R ** 2 * 1e-3
R['impacts'] = {'고무 핀 1개 강성 N/mm': round(k_pin, 1), '비틀림 강성 N·m/rad': round(k_th, 1),
                '쿠션 없으면 R 오조작 최대 토크 N·m(참고)': round(math.sqrt(2 * 0.5 * J_eff_gear('R') * cases[2][2] ** 2 * k_th_rigid), 1),
                'rows': imp_rows}

# ================= 8. 허브·키·D면·볼트 (정상 최대 = 클러치 최대 토크) =================
wh = math.sqrt(36 - 25)
def pD(T, L, double=True):
    n = 2 if double else 1
    return T / (n * (2 * wh / 3)) * 2 / (L * wh)
hub_rows = []
for k, (zi, zo) in list(tx.PAIRS.items()) + [('R', (17, 41))]:
    T_out = TC_MAX * zo / zi
    hub_rows.append({'단': k, '출력 토크 N·m': round(T_out / 1e3, 2), '허브 D면 MPa(양면D, L41)': round(pD(T_out, tx.HUB_BODY), 1),
                     '(한면D였다면)': round(pD(T_out, tx.HUB_BODY, False), 1),
                     '키 6개 면압 MPa': round(T_out / 15.2 / 6 / (tx.SLV_HALF * 4.4), 2),
                     '입력기어 D면 MPa(L25)': round(pD(TC_MAX, tx.FW), 1)})
R['hubs'] = hub_rows
R['disc_hub_D_MPa'] = round(pD(TC_MAX, tx.Z_HUB[1] - tx.Z_HUB[0]), 1)
R['washer_epoxy_MPa'] = round(TC_MAX / (math.pi * (11 ** 2 - 8.5 ** 2)) / 9.8, 3)      # 플랜지 접착면, 평균 반지름 9.8

# ================= 9. 베어링 =================
P_max = max(r['베어링 반력 최대 N'] for r in shaft_rows)
R['bearings'] = {'최대 반지름 하중 N': P_max, '정적 안전계수 C0/P': round(B6001['C0'] / P_max, 1),
                 'L10 수명(시간, 167rpm, 최대하중 계속)': round((B6001['C'] / P_max) ** 3 * 1e6 / (60 * 167)),
                 '릴리스 6003·파일럿 6001 축방향 N': round(F_rel, 1)}

# 스프링이 가장 많이 눌리는 길이 (밀착 + 1mm 보다 길어야 함)
lev_spr = (tx.PIVOT_Y + tx.LOCK_RHO - 8.5) - (tx.spring_spacer()[1]) - tx.REV_PUSH   # 레버 후진 잠금: 스페이서 끝 ~ 잠금 칼라, 눌렀을 때
R['C252_min_len'] = {'클러치(뗄 때)': round(L_of_s(S_MIN) - 1.5, 2), '카트리지(막힘)': round(tx.CART_PRE_L - (tx.TRAVEL - tx.GAP0), 2),
                     '페달 복귀(끝)': round(PEDAL_STOP_L, 2), '레버 후진 잠금(눌렀을 때)': round(lev_spr, 2),
                     '핸들 복귀(135°)': round(tx.ST_SPR_PRE - tx.ST_LIFT, 2), '밀착 + 1 (이보다 길어야 함)': C252['P2L']}
# 스프링 전단응력 (Wahl 보정, 하중 +10%): 인장강도 35% 이하 (스텐 정적 허용). 카트리지·핸들 예압은 tx 에서 이 한도로 정함
A['spring_su'] = f'기성 스프링 SUS304 선경 {tx.SPRING_D} 외경 {tx.SPRING_OD}: 인장강도 {tx.SPRING_SU:.0f} MPa (JIS G4314 SUS304-WPB 하한 근사, 미확인)'
Kw = (4 * tx.SPRING_C - 1) / (4 * tx.SPRING_C - 4) + 0.615 / tx.SPRING_C
F_spr = lambda L: C252['k'] * (C252['L0'] - L) * (1 + C252['tol'])
tau_spr = lambda L: Kw * 8 * F_spr(L) * (tx.SPRING_OD - tx.SPRING_D) / (math.pi * tx.SPRING_D ** 3)
R['springs'] = [{'쓰는 곳': k, '가장 짧을 때 mm': L, '힘 N(+10%)': round(F_spr(L), 1), '전단응력 MPa': round(tau_spr(L)),
                 '인장강도 대비 %': round(100 * tau_spr(L) / tx.SPRING_SU, 1)}
                for k, L in list(R['C252_min_len'].items())[:-1] + [('밀착 (참고)', tx.SPRING_SOLID)]]
# ================= 10. 포크·카트리지 =================
F_cart = (tx.CART_P1 + C252['k'] * (tx.TRAVEL - tx.GAP0)) * (1 + C252['tol'])   # 막혔을 때 (5mm 더 눌림), 스프링 +10%
F_det = round(C147['k'] * (C147['L0'] - 5.0), 2)                            # 디텐트 스프링 5mm 로 눌림
F_shift = F_cart + F_det
def Zrect(b, h): return b * h ** 2 / 6
M_arm = F_shift * (tx.RAIL_Y - 13.5 - tx.H)                  # 카트리지 아래끝 ~ 홈 중심
M_ring = F_shift / 2 * (tx.H + 44.6 - tx.H)                  # 양쪽 패드 → 링 위쪽
s_arm = M_arm / Zrect(12.0, 13.0); s_ring = M_ring / (Zrect(7.4, 13.0))
R['fork'] = {'카트리지 예압 N(공칭)': round(tx.CART_P1, 2), '막힘 최대 N': round(F_cart, 1), '디텐트 최대 N': F_det,
             '팔 굽힘 MPa': round(s_arm, 1), 'SF 정적': round(PLA['UTS_XY'] / s_arm, 1),
             'SF 피로 1만회': round(fatigue_allow(PLA['UTS_XY'], 1e4) / s_arm, 2),
             '링 굽힘 MPa': round(s_ring, 1), 'SF 링 피로 1만회': round(fatigue_allow(PLA['UTS_XY'], 1e4) / s_ring, 2),
             '(v3 6mm 팔이었다면) MPa': round(M_arm / Zrect(12.0, 6.0), 1),
             '러그 고정력 여유(M3 2개 마찰, 300N/나사 가정)': round(0.3 * 2 * 2 * 300 / F_shift, 1)}
A['lug_screw'] = '러그 M3 자가탭 나사가 레일을 누르는 힘 300N/개 가정 (손으로 조인 값, 미측정)'

# ================= 11. 레버·게이트 (손잡이 400N) =================
y_knob = tx.ROD_Y0 + tx.ROD_LEN - 15 + 14.0
Lk = y_knob - tx.PIVOT_Y; Lg = tx.GATE_Y - tx.PIVOT_Y
F_gate = F_KNOB * Lk / Lg
lig = (tx.CAGE_Z1 + 3) - (tx.LUG_Z + tx.GATE_DZ + 6.8)       # 칸 끝 ~ 게이트 판 끝
tau_gate = F_gate / (2 * lig * tx.GATE_T)
M_rod = F_KNOB * (Lk - Lg)
s_rod = M_rod * 32 / (math.pi * 12 ** 3)
lock_r = tx.LOCK_RHO
F_lip = F_KNOB * Lk / lock_r
lip_w = 30.0; lip_h = tx.GATE_Y - tx.GATE_T / 2 - tx.LIP_Y0
s_lip = F_lip * lip_h / Zrect(lip_w, 17.0)
R['lever'] = {'손잡이 하중 N': F_KNOB, '손잡이 팔 mm': round(Lk, 1), '게이트 팔 mm': round(Lg, 1),
              '게이트 칸 끝 힘 N': round(F_gate, 1), '칸 끝 전단 MPa': round(tau_gate, 1),
              'SF(전단 ≈0.6x인장)': round(0.6 * PLA['UTS_XY'] / tau_gate, 1),
              '피벗 반력 N': round(F_gate - F_KNOB, 1), '레버봉 굽힘 MPa': round(s_rod, 1), 'SF 레버봉': round(STEEL['Y'] / s_rod, 1),
              '후진 턱 힘 N(안 누르고 R)': round(F_lip, 1), '후진 턱 굽힘 MPa': round(s_lip, 1),
              'SF 후진 턱': round(PLA['UTS_XY'] / s_lip, 1),
              '손잡이 접착 MPa': round(F_KNOB / (math.pi * 12 * 15), 2)}

# ================= 12. 클러치 부품 =================
d5 = 5.0
F1 = TC_MAX / tx.CPL_PIN_R                                    # 최악: 핀 1개
arm = (tx.Z_FRONT[0] - tx.Z_SPROCKET[0]) - 2.0                # 앞판 면 ~ 스프로킷 이 가운데
R['clutch_parts'] = {'커플링 핀 1개 힘 N': round(F1, 1), '핀 굽힘 MPa(강)': round(F1 * arm * 32 / (math.pi * d5 ** 3), 1),
                     '핀 구멍 압력 MPa': round(F1 / (d5 * 15) * (4 + 6 * arm / 15), 1),
                     '기둥 M4 인장 N(스프링 최대)': round(F_MAX / 3, 1),
                     '디스크 허브 D면 MPa(양면D)': R['disc_hub_D_MPa'], '와셔 에폭시 전단 MPa': R['washer_epoxy_MPa'],
                     '포크 브래킷 볼 반력 N': round(F_rel * (1 + 1 / fork_ratio) / 2, 1)}

# ================= 13. 전기 =================
Kt = T_RATED_MOTOR / (5.9 - 0.6)
A['motor_Kt'] = '토크상수 = 정격토크 / (정격전류 - 무부하전류 0.6A 가정)'
I_slip = TC_MAX / 1e3 / RATIO_GH / 0.81 / Kt + 0.6
R['electric'] = {'토크상수 N·m/A(추정)': round(Kt, 4), '클러치 최대 토크 때 모터 전류 A': round(I_slip, 1),
                 '정격 전류 A(라벨)': 5.9, '퓨즈': '15A 블레이드 (전선 1.5mm² 이상)', '감속기 효율 가정': 0.81}
A['gearhead_eff'] = '감속기 효율 0.81 가정 (미확인)'

# ================= 14. 모터 받침 =================
R['motor_mount'] = {'반력 토크 N·m(클러치 최대)': round(TC_MAX / 1e3, 2),
                    '받침 볼트 좌우 줄(간격 128) 힘 N': round(TC_MAX / tx.MOTOR_FOOT_HOLE, 1)}

# ================= 15. 디텐트 =================
R['detent'] = {'디텐트 스프링 최대 힘 N': F_det, '설명': '레버 느낌용(가벼움). 기어 유지는 핀 마찰·카트리지 예압이 담당'}

json.dump(R, open(os.path.join(ROOT, 'calc', 'calc_result.json'), 'w'), ensure_ascii=False, indent=1, default=float)
print(json.dumps({k: v for k, v in R.items() if k not in ('src',)}, ensure_ascii=False, indent=1, default=float))
