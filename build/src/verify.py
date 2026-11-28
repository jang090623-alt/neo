"""v4 최종 검증: 단별 정지 상태(클러치 물림/끊김) 간섭, 막힘 상태, 레버 경로(1mm), 후진 잠금, 맞물림 스윕, STL 닫힘"""
import json, os, sys, time, asm, tx, trimesh
ROOT = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(ROOT, '..', 'stl')
t0 = time.time()
R = {}
st = {}
for s in ['N', '1', '2', '3', '4', '5']:
    for cs in ([1, -1] if s in 'N34' else [0]):
        for cl in ('in', 'out'):
            st[f'{s}/{cs}/{cl}'] = asm.collisions(asm.assemble(s, carrier_side=cs, clutch_state=cl))
st['R(눌러서)'] = asm.collisions(asm.assemble('R', push=True))
st['R(안 누름)'] = asm.collisions(asm.assemble('R', push=False))
for s in ['1', '2', '3', '4', '5', 'R']:
    st[f'{s} 막힘'] = asm.collisions(asm.assemble(s, push=(s == 'R'), blocked=True))
R['states'] = st
print('states done', round(time.time() - t0), flush=True)
R['mesh'] = asm.mesh_sweep(60)
print('mesh done', round(time.time() - t0), flush=True)
if '--sweep' in sys.argv:
    sw = asm.lever_sweep(1.0)
    R['sweep_total'] = len(sw)
    R['sweep_non_reverse_lock'] = [x for x in sw if not (x[2] == 'gate' and x[3] == 'lock_collar')]
    R['reverse_blocked_at'] = sorted(set(float(x[1]) for x in sw if x[3] == 'lock_collar'))
    print('sweep done', round(time.time() - t0), flush=True)
R['pedal'] = asm.pedal_check()
print('pedal done', round(time.time() - t0), flush=True)
# 2026-11: 클러치 허브·슬리브 추가 검사 (모양 겹침만으로는 못 잡는 것)
import numpy as np, export
from tx import cyl
def _clutch_checks():
    C = {}
    H = tx.H
    sleeve = tx.cl_hub_sleeve().translate([0, H, 0])
    hub_l = tx.cl_disc_hub()
    shaft = cyl(6.0, 450, tx.Z_SHAFT_IN_END).translate([0, H, 0])
    # 조립 경로: 허브를 모터 쪽에서 밀어 넣기 / 와셔를 허브 목 쪽에서 끼우기 / 뒷판을 굳은 슬리브 위로
    C['hub_path_hits'] = [float(z) for z in np.arange(tx.Z_SHAFT_IN_END - 15, tx.HUB2_Z[0] + 0.01, 0.5)
                          if (hub_l.translate([0, H, z]) ^ sleeve).volume() > 0.01 or (hub_l.translate([0, H, z]) ^ shaft).volume() > 0.01]
    w = tx.steel_washer()
    C['washer_path_hits'] = [float(z) for z in np.arange(-30, 0.01, 0.5) if (w.translate([0, 0, z]) ^ hub_l).volume() > 0.01]
    back = tx.cl_back().translate([0, H, tx.Z_BACK[1]])
    C['back_over_sleeve_hits'] = [float(d) for d in np.arange(-80, 0.01, 1.0) if (back.translate([0, 0, d]) ^ sleeve).volume() > 0.01]
    # 허브가 슬리브 위에서 움직일 수 있는 범위 (물린 자리 0 기준)
    free = [float(d) for d in np.arange(-3, 3.01, 0.1) if (hub_l.translate([0, H, tx.HUB2_Z[0] + d]) ^ sleeve).volume() < 0.01]
    C['hub_free_travel_mm'] = [round(min(free), 1), round(max(free), 1)]
    # 페달 끝 멈춤(릴리스 링 REL_STOP 이동)에서 링과 허브·슬리브 틈
    ring = tx.cl_ring().translate([0, H, tx.Z_RING[0] - tx.REL_STOP])
    C['ring_at_stop^hub'] = round((ring ^ hub_l.translate([0, H, tx.HUB2_Z[0]])).volume(), 3)
    C['ring_at_stop^sleeve'] = round((ring ^ sleeve).volume(), 3)
    C['ring_stop_gap_to_hub_mm'] = round(tx.Z_RING[0] - tx.REL_STOP - tx.HUB2_Z[1], 2)
    # 출력 방향에서 층마다 한 덩어리인지 (목·몸통이 실처럼 붙은 부품 잡기) + 받침 없는 아래쪽 면
    for name in ('74_cl_disc_hub', '74b_cl_hub_sleeve'):
        t = trimesh.load(os.path.join(STL, name + '.stl'))
        zs = np.arange(0.15, t.bounds[1][2], 0.28)
        prev = None; worst = 1e9
        for z in zs:
            sec = t.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
            if sec is None: continue
            p = sec.to_planar()[0].polygons_full
            area = sum(q.area for q in p)
            if prev is not None:
                worst = min(worst, area / prev)
            prev = area
        fn = t.face_normals; zc = t.triangles_center[:, 2]
        flat_down = float(t.area_faces[(fn[:, 2] < -0.99) & (zc > 0.3)].sum())
        C[name] = {'min_layer_area_ratio': round(worst, 3), 'flat_overhang_mm2': round(flat_down, 1)}
    return C
R['clutch'] = _clutch_checks()
print('clutch checks', R['clutch'], flush=True)
# 2026-11: 변속 느낌 (홈 딸깍·중립 복귀) + 스프링 한계 + 핑거 물림 + 후진 잠금
def _shifter_checks():
    S = {}
    K, L0, SOLID = tx.SPRING_K, tx.SPRING_L0, tx.SPRING_SOLID
    dmax = tx.SPRING_FMAX / 1.1 / K                                   # 스프링 1개 허용 눌림 (+10% 여유)
    kb = tx.knob().bounding_box(); L2 = (kb[1] + kb[4]) / 2 - tx.PIVOT_Y   # 피벗 → 손잡이 가운데
    S['L2_knob_mm'] = round(L2, 1)
    # 핑거 물림: 고른 러그를 레일 방향 ±1 밀면 양쪽 다 핑거에 닿아야 (홈 안에 갇힘)
    eng = {}
    for s in ['1', '2', '3', '4', '5', 'R']:
        P = asm.assemble(s, push=(s == 'R'))
        g = asm.SHIFT[s][0]
        hit = [(P['lower_lever'] ^ P[f'lug_{g}'].translate([0, 0, d])).volume() > 0.01 for d in (-1.0, 1.0)]
        eng[s] = all(hit)
    S['finger_captured_both_ways'] = eng
    # 후진 잠금: 안 누르면 칼라가 게이트 턱에 막혀야, 누르면 깨끗
    def has(st, a, b): return any({x[0], x[1]} == {a, b} for x in st)
    st = R['states']
    S['R_unpushed_blocked_by_lip'] = has(st['R(안 누름)'], 'gate', 'lock_collar')
    S['R_pushed_clear'] = len(st['R(눌러서)']) == 0
    # 잠금 스프링 (칼라를 게이트 밑면에 누름): 길 / 단 홈 안 / 후진 누름
    Lk = L0 - tx.LOCK_F0 / K
    lock = {'lane': Lk, 'gear': Lk + tx.POCKET_D, 'R_pushed': Lk - tx.REV_PUSH}
    S['lock_spring'] = {k: {'len': round(l, 2), 'F_N': round(K * (L0 - l), 2), 'ok': SOLID < l and L0 - l <= dmax} for k, l in lock.items()}
    rim = math.sqrt((tx.LOCK_RHO + tx.RISE_LANE + tx.POCKET_D) ** 2 - 14.0 ** 2)
    S['click_hold_at_knob_N'] = round(K * (L0 - lock['gear']) / 0.7 * rim / L2, 2)          # 홈 벽 기울기 0.7, 마찰 무시
    S['lane_drag_at_knob_N(mu0.2~0.3)'] = [round(K * (L0 - Lk) * mu * tx.LOCK_RHO / L2, 2) for mu in (0.2, 0.3)]
    S['reverse_push_at_knob_N'] = round(K * (L0 - lock['R_pushed']), 2)
    # 중립 복귀: 레버 자세별 피스톤 밀림
    cen = {}
    for s in ['N', '1', '2', '3', '4', '5', 'R']:
        P = asm.assemble(s, push=(s == 'R'))
        dl, dr = tx.cen_push(P['spring_spacer'])
        d = max(dl, dr)
        per = (tx.CEN_D0 + d) / tx.CEN_N
        cen[s] = {'push_mm': round(d, 2), 'per_spring_defl': round(per, 2), 'spring_len': round(L0 - per, 2),
                  'ok': L0 - per > SOLID and per <= dmax,
                  'return_at_knob_N': round(tx.CEN_K * (tx.CEN_D0 + d) * tx.CEN_H / L2, 2)}
    S['centering'] = cen
    S['centering_preload_at_knob_N'] = round(tx.CEN_K * tx.CEN_D0 * tx.CEN_H / L2, 2)
    # 페달 복귀 스프링 (3개)
    pl = R['pedal']['spring_len_rest_stop']
    S['pedal_spring'] = {'len_rest_stop': pl, 'ok': pl[1] > SOLID and L0 - pl[1] <= dmax,
                         'F_rest_stop_total_N': [round(len(tx.PEDAL_SPR_X) * K * (L0 - l), 1) for l in pl],
                         'F_return_springs_at_pad_stop_N': round(len(tx.PEDAL_SPR_X) * K * (L0 - pl[1]) * tx.PEDAL_SPR_B / tx.PEDAL_PAD_B, 1),
                         'travel_deg': round(tx.PEDAL_TRAVEL, 2),
                         'pad_stroke_mm': round(math.radians(tx.PEDAL_TRAVEL) * tx.PEDAL_PAD_B, 1)}
    S['all_ok'] = (all(eng.values()) and S['R_unpushed_blocked_by_lip'] and S['R_pushed_clear']
                   and all(x['ok'] for x in S['lock_spring'].values()) and all(x['ok'] for x in cen.values()) and S['pedal_spring']['ok'])
    return S
import math
R['shifter'] = _shifter_checks()
print('shifter checks', R['shifter'], flush=True)
R['stl_bad'] = [f for f in sorted(os.listdir(STL)) if not trimesh.load(os.path.join(STL, f)).is_watertight]
R['stl_count'] = len(os.listdir(STL))
R['stl_multi_body'] = [f for f in sorted(os.listdir(STL)) if len(trimesh.load(os.path.join(STL, f)).split(only_watertight=False)) != 1]   # 얇은 조각·떨어진 덩어리
json.dump(R, open(os.path.join(ROOT, 'verify_result.json'), 'w'), ensure_ascii=False, indent=1, default=str)
print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
