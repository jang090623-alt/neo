"""v4 조립 배치 + 간섭 검사.
state: 'N','1'..'5','R' / push=True: 레버를 누른 상태 / clutch: 'in'(물림) 'out'(밟음)
blocked=True: 레버·레일은 끝까지 갔는데 슬리브가 핀 끝에 막힌 상태(카트리지 스프링 5mm 압축)"""
import math, itertools
import numpy as np
import manifold3d as mf
import tx
from tx import M, C, H, FW, cyl, tube, boxm, ext, d_hole_poly

SHIFT = {'N': ('34', 0.0), '1': ('12', +tx.TRAVEL), '2': ('12', -tx.TRAVEL), '3': ('34', +tx.TRAVEL),
         '4': ('34', -tx.TRAVEL), '5': ('5R', +tx.TRAVEL), 'R': ('5R', -tx.TRAVEL)}
GEAR_GROUP = {'R': '5R', '5': '5R', '4': '34', '3': '34', '2': '12', '1': '12'}
FRONT = {'R', '4', '2'}          # 그룹 앞(작은 z) 기어 → 핀이 +z

def xf(m, R=np.eye(3), t=(0, 0, 0)):
    A = np.zeros((3, 4)); A[:, :3] = R; A[:, 3] = t
    return m.transform(A)

def mesh_phase(ca, za, phia, cb, zb):
    al = math.atan2(cb[1] - ca[1], cb[0] - ca[0])
    pa = 2 * math.pi / za
    d = ((al - phia) % pa); d = d if d < pa / 2 else d - pa
    return al + math.pi + math.pi / zb + d * za / zb

def place_gear(m, xy, z0, phase, up=True):
    m = m.rotate([0, 0, math.degrees(phase)])
    if not up:
        m = m.mirror([0, 0, 1]).translate([0, 0, FW])
    return m.translate([xy[0], xy[1], z0])

def d_shaft(x, z0, length):
    return ext(d_hole_poly(12.0, 5.0, double=True), length, z0).translate([x, H, 0])

IN_SHAFT = (tx.Z_SHAFT_IN_END, tx.STACK + tx.PLATE_T + 12.0)            # 입력축 z 범위
OUT_SHAFT = (-27.0, tx.Z_WHEEL + tx.WHEEL_T + 4.0)                     # 출력축 z 범위

def brg(x, y, z0, od=28.0, idd=12.1, w=8.0):
    return tube(od / 2, idd / 2, w, z0).translate([x, y, 0])

def clutch(P, state='in'):
    """클러치·모터 연결 부품 (조립 좌표). state='out' 이면 릴리스 쪽이 -z 로 이동"""
    rel = 1.5 if state == 'out' else 0.0          # 압력판 이동량
    mv = rel + 1.0 if state == 'out' else 0.0     # 릴리스 링·베어링·캐리어·포크 팔 이동 = 누름 볼트 틈 1.0(M5x20) + 1.5
    P['cl_front'] = tx.cl_front().translate([0, H, tx.Z_FRONT[0]])
    P['cl_back'] = tx.cl_back().translate([0, H, tx.Z_BACK[1]])
    P['cl_press'] = tx.cl_pressure().translate([0, H, tx.Z_PRESS[0] - rel])
    for k, (x, y) in enumerate(tx._ring_pts(tx.CL_STANDOFF_R, tx.STANDOFF_A)):
        P[f'cl_standoff{k}'] = tx.cl_standoff().translate([x, H + y, tx.Z_FRONT[1]])
        P[f'cl_bolt{k}'] = cyl(2.0, tx.Z_BACK[1] - tx.Z_FRONT[0] + 3.0, tx.Z_FRONT[0] - 0.5).translate([x, H + y, 0])
    P['cl_hub'] = tx.cl_disc_hub().translate([0, H, tx.Z_HUB[0]])
    P['cl_washer'] = tx.steel_washer().translate([0, H, tx.Z_WASH[0]])
    P['cl_cork_b'] = tx.cork_ring().translate([0, H, tx.Z_BACK[0] - tx.CORK[2]])
    P['cl_cork_p'] = tx.cork_ring().translate([0, H, tx.Z_PRESS[1] - rel])
    zf1 = tx.Z_FRONT[1]
    for k, (x, y) in enumerate(tx._ring_pts(tx.CL_SPRING_R, tx.SPRING_A)):
        s = 3.0                                          # 조절나사 M5x10 끝까지 조임 (s = 13 - 10) = 설정값
        cup_bot = zf1 - s - 3.0                          # 조절나사 끝이 미는 컵 밑면
        cup_top = cup_bot + tx.CUP_T                     # 스프링이 앉는 컵 판 윗면
        P[f'cl_cup{k}'] = tx.cl_spring_cup().translate([x, H + y, cup_bot])
        z_top = tx.Z_PRESS[0] - rel + 2.0                            # 압력판 스프링 자리(홈 2) 바닥
        P[f'cl_spring{k}'] = tube(9.0, 7.6, z_top - cup_top - 0.2, cup_top + 0.1).translate([x, H + y, 0])
        P[f'cl_adj{k}'] = cyl(2.4, cup_bot - (tx.Z_FRONT[0] - 4.0) - 0.1, tx.Z_FRONT[0] - 4.0).translate([x, H + y, 0])
    P['cl_ring'] = tx.cl_ring().translate([0, H, tx.Z_RING[0] - mv])
    for k, (x, y) in enumerate(tx._ring_pts(tx.CL_PUSH_R, tx.PUSH_A)):
        # M5x20 누름 볼트 (머리가 링 판 끝판 쪽 면): 물림 상태 끝이 압력판 뒷면에서 1.0, 밟으면 닿아서 1.5 더 밂
        z_tip = tx.Z_PRESS[1] + 1.0 - mv
        P[f'cl_push{k}'] = cyl(2.4, (tx.Z_RING[0] - mv) - z_tip, z_tip).translate([x, H + y, 0])
    P['cl_relbrg'] = brg(0, H, tx.Z_REL[0] - mv, 35.0, 17.1, 10.0)
    P['cl_carrier'] = tx.cl_carrier().translate([0, H, tx.CARRIER_Z[1] - mv])
    # 포크: 밟으면 피벗 둘레로 회전 → 트러니언 쪽이 -z 로 mv
    ang = math.atan2(mv, tx.FORK_PIV_Y - H)
    piv = np.array([0.0, tx.FORK_PIV_Y, tx.FORK_PIV_Z])
    R = np.array([[1, 0, 0], [0, math.cos(ang), -math.sin(ang)], [0, math.sin(ang), math.cos(ang)]])
    P['cl_fork'] = xf(tx.cl_fork().translate(list(-piv)), R, piv)
    P['cl_bracket'] = tx.cl_fork_bracket()
    P['cl_pivot_bolt'] = (tx.along_x(cyl(2.4, 70, -39.5)) + tx.along_x(cyl(4.25, 5, 30.5))      # M5x70 (머리 30.5~35.5)
                          + tx.along_x(cyl(4.6, 5, -35.5))).translate(list(piv))                    # 나일론 너트 (두께 5)
    # 파일럿 베어링·끝 와셔·끝 칼라
    P['cl_pilot'] = brg(0, H, tx.Z_FRONT[0])
    P['cl_endsp'] = tx.cl_end_spacer().translate([0, H, tx.Z_FRONT[0] - 1.0])
    P['cl_endcollar'] = tx.collar(w=8.0).translate([0, H, tx.Z_SHAFT_IN_END])
    # 커플링 핀 6 (Ø5x40, 앞판에 15 박힘) + 스프로킷(이뿌리 원판으로 근사) + 감속기 축·몸체 + 모터
    for k, (x, y) in enumerate(tx._ring_pts(tx.CPL_PIN_R, tx.CPL_PIN_A)):
        P[f'cpl_pin{k}'] = cyl(2.5, tx.CPL_PIN_LEN - 15.0, tx.Z_FRONT[0] - (tx.CPL_PIN_LEN - 15.0)).translate([x, H + y, 0])
    rr = tx.CPL_PIN_R - 2.54 - 0.06
    P['m_sprocket'] = cyl(rr, tx.Z_SPROCKET[1] - tx.Z_SPROCKET[0], tx.Z_SPROCKET[0]).translate([0, H, 0])
    P['m_shaft'] = cyl(7.5, tx.Z_SHAFT_IN_END - 2.0 - tx.Z_GEARHEAD_FRONT, tx.Z_GEARHEAD_FRONT).translate([0, H, 0])
    # 감속기·모터 몸체: □90 (축 중심), 위는 60 까지 여유, 브래킷 앞판 뒤 (정확한 외형 미확인 → 직육면체 근사)
    P['m_body'] = boxm(-45, 45, H - 45, H + 60, tx.Z_GEARHEAD_FRONT - tx.MOTOR_LEN, tx.Z_GEARHEAD_FRONT - 9.0)
    P['m_bracket'] = tx.motor_bracket()
    P['m_riser'] = tx.motor_riser()

def assemble(state='N', push=False, carrier_side=0, clutch_state='in', blocked=False):
    P = {}
    grp, sh = SHIFT[state]
    pdn = tx.REV_PUSH if push else 0.0
    sh_lug = sh * (tx.L1 + pdn) / tx.L1
    rail_s = {g: (sh_lug if g == grp else 0.0) for g in tx.RAIL_X}
    fork_s = dict(rail_s)
    if blocked and state != 'N':
        fork_s[grp] = math.copysign(tx.GAP0, sh)          # 슬리브가 핀 끝에 막힘 (3mm 만 이동)
    # 축
    P['shaft_in'] = d_shaft(0.0, IN_SHAFT[0], IN_SHAFT[1] - IN_SHAFT[0])
    P['shaft_out'] = d_shaft(C, OUT_SHAFT[0], OUT_SHAFT[1] - OUT_SHAFT[0])
    ix, iy = tx.IDLER_XY
    P['shaft_idler'] = cyl(6.0, 55.0, -15.0).translate([ix, iy, 0])
    # 끝판·베어링·스페이서·칼라
    P['plate_A'] = tx.end_plate('A'); P['plate_B'] = tx.end_plate('B')
    for x in (0.0, C):
        P[f'brg_A_{int(x)}'] = brg(x, H, -8.0)
        P[f'brg_B_{int(x)}'] = brg(x, H, tx.STACK)
        P[f'pspacer_A_{int(x)}'] = tx.plate_spacer().translate([x, H, -17.0])
        P[f'pspacer_B_{int(x)}'] = tx.plate_spacer().translate([x, H, tx.STACK + 8.0])
        P[f'collar_A_{int(x)}'] = tx.collar().translate([x, H, -27.0])
        P[f'collar_B_{int(x)}'] = tx.collar().translate([x, H, tx.STACK + 17.0])
    # 기어
    phase_out = {}
    for k, (zi, zo) in tx.PAIRS.items():
        z0 = tx.PLANE[k]
        P[f'gin_{k}'] = place_gear(tx.fixed_gear(zi), (0, H), z0, 0.0)
        ph = mesh_phase((0, H), zi, 0.0, (C, H), zo)
        phase_out[k] = ph
        up = k in FRONT
        P[f'gout_{k}'] = place_gear(tx.free_gear(zo), (C, H), z0, ph, up)
        face = z0 + FW if up else z0
        P[f'pins_{k}'] = tx.pin_solids(face, up).rotate([0, 0, math.degrees(ph)]).translate([C, H, 0])
    zr = tx.PLANE['R']
    ri, rid, ro = tx.REV
    P['gin_R'] = place_gear(tx.fixed_gear(ri), (0, H), zr, 0.0)
    phi_id = mesh_phase((0, H), ri, 0.0, (ix, iy), rid)
    P['g_idler'] = place_gear(tx.idler_gear(), (ix, iy), zr, phi_id)
    phi_ro = mesh_phase((ix, iy), rid, phi_id, (C, H), ro)
    phase_out['R'] = phi_ro
    P['gout_R'] = place_gear(tx.free_gear(ro), (C, H), zr, phi_ro, True)
    P['pins_R'] = tx.pin_solids(zr + FW, True).rotate([0, 0, math.degrees(phi_ro)]).translate([C, H, 0])
    P['idler_spacer'] = tx.spacer(3.0).translate([ix, iy, 0.0])
    P['idler_collar'] = tx.collar().translate([ix, iy, zr + FW])
    for k in ['R', '5', '4', '3', '2', '1']:
        z0 = tx.PLANE[k]
        for zb in (z0, z0 + FW - 8):
            P[f'brg_g{k}_{int(zb)}'] = brg(C, H, zb)
    for zb in (zr, zr + FW - 8):
        P[f'brg_idler_{int(zb)}'] = brg(ix, iy, zb)
    # 출력축에 묶인 부품 회전각: 물린 기어의 핀이 포켓 가운데에 오도록
    PSI = math.degrees(phase_out[state]) if state != 'N' else 0.0
    P['shaft_out'] = P['shaft_out'].translate([-C, -H, 0]).rotate([0, 0, PSI]).translate([C, H, 0])
    # 허브·슬리브·스페이서
    for g, zc in tx.SLEEVE_Z.items():
        s = fork_s[g]
        P[f'hub_{g}'] = tx.hub().rotate([0, 0, PSI]).translate([C, H, zc - tx.HUB_BODY / 2])
        P[f'hubw_a_{g}'] = tx.spacer(1.0).translate([C, H, zc - tx.HUB_LEN / 2])
        P[f'hubw_b_{g}'] = tx.spacer(1.0).translate([C, H, zc + tx.HUB_LEN / 2 - 1.0])
        h1 = tx.sleeve_half().mirror([0, 0, 1]).translate([0, 0, zc - tx.SLV_BODY / 2 + tx.SLV_HALF + s])
        h2 = tx.sleeve_half().translate([0, 0, zc + tx.SLV_BODY / 2 - tx.SLV_HALF + s])
        sl = h1 + h2 + tx.sleeve_ring().translate([0, 0, zc - tx.GROOVE_W / 2 + s])
        P[f'slv_{g}'] = sl.rotate([0, 0, PSI]).translate([C, H, 0])
        P[f'sp_in_{g}'] = tx.spacer(tx.HUB_LEN).translate([0, H, zc - tx.HUB_LEN / 2])
    for zs in (0.0, tx.GROUP + 3, 2 * tx.GROUP + 6, tx.STACK - 3):
        P[f'sp_out_end_{int(zs)}'] = tx.spacer(3.0).translate([C, H, zs])
        P[f'sp_in_end_{int(zs)}'] = tx.spacer(3.0).translate([0, H, zs])
    # 레일·포크(카트리지)·러그
    for g, xr in tx.RAIL_X.items():
        rs, fs = rail_s[g], fork_s[g]
        P[f'rail_{g}'] = cyl(3.0, tx.RAIL_LEN, tx.RAIL_Z0 + rs).translate([xr, tx.RAIL_Y, 0])
        P[f'fork_{g}'] = tx.fork(g).translate([0, 0, fs])
        P[f'fcap_{g}'] = tx.cap_placed(g).translate([0, 0, fs])
        zi0, zi1 = tx.cart_inner_z(g)
        d = rs - fs                                   # 레일이 포크보다 더 간 양 (막힘)
        # 와셔·칼라: 레일 쪽 칼라는 레일과 함께, 반대쪽 와셔는 하우징 끝벽에 붙어 있음
        wa0 = zi0 + fs + max(d, 0.0); wb0 = zi1 + fs + min(d, 0.0) - tx.CART_WASH_T
        P[f'fwash_a_{g}'] = tx.cart_washer().translate([xr, tx.RAIL_Y, wa0])
        P[f'fwash_b_{g}'] = tx.cart_washer().translate([xr, tx.RAIL_Y, wb0])
        P[f'fspring_{g}'] = tube(9.0, 7.0, (wb0 - (wa0 + tx.CART_WASH_T)) - 0.2, wa0 + tx.CART_WASH_T + 0.1).translate([xr, tx.RAIL_Y, 0])
        rc_od, rc_w = tx.RAIL_COLLAR
        P[f'rcol_a_{g}'] = tube(rc_od / 2, 3.05, rc_w, zi0 - rc_w + rs).translate([xr, tx.RAIL_Y, 0])
        P[f'rcol_b_{g}'] = tube(rc_od / 2, 3.05, rc_w, zi1 + rs).translate([xr, tx.RAIL_Y, 0])
        P[f'lug_{g}'] = tx.lug(g).translate([0, 0, rs])
    P['cage'] = tx.cage()
    P['gate'] = tx.gate()
    P['pivot_lo'] = tx.pivot_half(False); P['pivot_hi'] = tx.pivot_half(True)
    dx = tx.RAIL_X[grp] - C if state != 'N' else 0.0
    dz = sh
    R = tx.lever_rot(dx, dz)
    piv = tx.PIVOT
    def lev(m, slide=True):
        m = m.translate([0, -pdn, 0]) if slide else m
        return xf(m.translate(list(-piv)), R, piv)
    P['ball'] = lev(tx.ball_half(True) + tx.ball_half(False), slide=False)
    P['lower_lever'] = lev(tx.lower_lever())
    P['rod'] = lev(tx.along_y(cyl(6.0, tx.ROD_LEN, 0)).translate([C, tx.ROD_Y0, tx.LUG_Z]))
    sp, _ = tx.spring_spacer()
    P['spring_spacer'] = lev(sp, slide=False)
    P['lock_collar'] = lev(tx.lock_collar())
    P['knob'] = lev(tx.knob())
    fx = tx.lever_point(dx, dz, tx.FINGER_YC - tx.PIVOT_Y, push=pdn)[0]
    side = carrier_side if carrier_side else (1 if dx < 0 else -1)
    P['carrier'] = tx.carrier().translate([fx + side * (tx.WIN - tx.FINGER_HALF), 0, 0])
    P['wheel'] = tx.display_wheel().rotate([0, 0, PSI]).translate([C, H, tx.Z_WHEEL])
    P['wheel_guard'] = tx.wheel_guard()
    clutch(P, clutch_state)
    guards(P)
    return P

def guards(P):
    """v4.1 덮개·받침 브래킷 (조립 좌표)"""
    P['hood'] = tx.clutch_hood()
    P['hood_front'] = tx.hood_front()
    P['cap_A'] = tx.collar_cap()
    P['cap_B'] = tx.collar_cap().translate([-C, 0, 0]).mirror([0, 0, 1]).translate([0, 0, tx.STACK])
    P['filler_A'] = tx.end_filler().translate([0, 0, -tx.PLATE_T])
    P['filler_B'] = tx.end_filler().translate([0, 0, tx.STACK])
    P.update(tx.acrylic_panels())
    fb = tx.foot_bracket()
    for xb in (-12.0, 165.0):
        P[f'foot_A_{int(xb)}'] = fb.rotate([0, 90, 0]).translate([xb - 15, 0, -tx.PLATE_T])
        P[f'foot_B_{int(xb)}'] = fb.rotate([0, -90, 0]).translate([xb + 15, 0, tx.STACK + tx.PLATE_T])

# 일부러 닿거나 겹치는 쌍 (압입·접착·클램프·볼 소켓·핀 커플링)
ALLOWED = [('shaft_idler', 'plate_A'), ('rod', 'lower_lever'), ('rod', 'knob'), ('rod', 'lock_collar'),
           ('rod', 'ball'), ('rod', 'spring_spacer'), ('ball', 'spring_spacer'),
           ('cl_washer', 'cl_hub'), ('cl_cork_b', 'cl_back'), ('cl_cork_p', 'cl_press'),
           ('cl_cork_b', 'cl_washer'), ('cl_cork_p', 'cl_washer'),
           ('cl_bolt', 'cl_standoff'), ('cl_bolt', 'cl_front'), ('cl_bolt', 'cl_back'),
           ('cl_push', 'cl_ring'), ('cl_adj', 'cl_front'), ('cl_relbrg', 'cl_ring'), ('cl_relbrg', 'cl_carrier'),
           ('cl_bracket', 'plate_A'),
           ('cl_pilot', 'cl_front'), ('cpl_pin', 'cl_front'), ('cpl_pin', 'm_sprocket'),
           ('m_shaft', 'm_sprocket'), ('m_shaft', 'm_body'), ('m_shaft', 'm_bracket'), ('m_body', 'm_bracket'),
           ('rcol', 'rail'), ('fwash', 'rail'), ('rail', 'lug'), ('fcap', 'fork'),
           ('cl_spring', 'cl_cup'), ('cl_spring', 'cl_press'), ('cl_cup', 'cl_adj')]

def allowed(a, b):
    for x, y in ALLOWED:
        if (a.startswith(x) and b.startswith(y)) or (a.startswith(y) and b.startswith(x)):
            return True
    return False

def collisions(P, tol=0.5):
    names = list(P)
    bbs = {n: P[n].bounding_box() for n in names}
    out = []
    for a, b in itertools.combinations(names, 2):
        A, B = bbs[a], bbs[b]
        if any(A[i] > B[i + 3] or B[i] > A[i + 3] for i in range(3)):
            continue
        if allowed(a, b):
            continue
        v = (P[a] ^ P[b]).volume()
        if v > tol:
            out.append((a, b, round(v, 2)))
    return out

def mesh_sweep(n=60):
    """2D 맞물림을 한 피치 동안 n 단계로 돌리며: 이 사이 최소 간격 / 겹침 면적 (필렛·이끝 간섭 확인)"""
    from shapely import affinity
    from shapely.geometry import Point
    out = []
    def pair(za, ca, pa, zb, cb, pb, name):
        A0, B0 = tx.gear_poly(za), tx.gear_poly(zb)
        mid = ((ca[0] * zb + cb[0] * za) / (za + zb), (ca[1] * zb + cb[1] * za) / (za + zb))
        win = Point(*mid).buffer(16)
        dmin, amax = 9.0, 0.0
        for i in range(n):
            th = 2 * math.pi / za * i / n
            A = affinity.translate(affinity.rotate(A0, pa + th, origin=(0, 0), use_radians=True), *ca)
            B = affinity.translate(affinity.rotate(B0, pb - th * za / zb, origin=(0, 0), use_radians=True), *cb)
            a, b = A.intersection(win), B.intersection(win)
            dmin = min(dmin, a.distance(b)); amax = max(amax, a.intersection(b).area)
        out.append((name, round(dmin, 3), round(amax, 4)))
    for k, (zi, zo) in tx.PAIRS.items():
        pair(zi, (0, H), 0.0, zo, (C, H), mesh_phase((0, H), zi, 0.0, (C, H), zo), k)
    ix, iy = tx.IDLER_XY; ri, rid, ro = tx.REV
    p1 = mesh_phase((0, H), ri, 0.0, (ix, iy), rid); p2 = mesh_phase((ix, iy), rid, p1, (C, H), ro)
    pair(ri, (0, H), 0.0, rid, (ix, iy), p1, 'R 입력-아이들러')
    pair(rid, (ix, iy), p1, ro, (C, H), p2, 'R 아이들러-출력')
    A, B = tx.gear_poly(ri), tx.gear_poly(ro)
    from shapely import affinity as af
    d = af.translate(A, 0, H).distance(af.translate(af.rotate(B, p2, origin=(0, 0), use_radians=True), C, H))
    out.append(('R 입력-출력(떨어져야)', round(d, 3), 0))
    return out

def lever_sweep(step=2.0):
    fixed = {'gate': tx.gate(), 'cage': tx.cage(), 'pivot_lo': tx.pivot_half(False), 'pivot_hi': tx.pivot_half(True)}
    bad = []
    for path in tx.lever_paths(step):
        for dx, dz in path:
            col = min(tx.RAIL_X, key=lambda g: abs(tx.RAIL_X[g] - C - dx))
            on_col = abs(tx.RAIL_X[col] - C - dx) < 1e-6
            R = tx.lever_rot(dx, dz); piv = tx.PIVOT
            def lev(m):
                return xf(m.translate(list(-piv)), R, piv)
            parts = {'lower_lever': lev(tx.lower_lever()), 'ball': lev(tx.ball_half(True) + tx.ball_half(False)),
                     'rod': lev(tx.along_y(cyl(6.0, tx.ROD_LEN, 0)).translate([C, tx.ROD_Y0, tx.LUG_Z])),
                     'spring_spacer': lev(tx.spring_spacer()[0]), 'lock_collar': lev(tx.lock_collar()), 'knob': lev(tx.knob())}
            fx = tx.lever_point(dx, dz, tx.FINGER_YC - tx.PIVOT_Y)[0]
            side = 1 if dx < 0 else -1
            mov = {'carrier': tx.carrier().translate([fx + side * (tx.WIN - tx.FINGER_HALF), 0, 0])}
            for g in tx.RAIL_X:
                s = dz if (on_col and g == col) else 0.0
                mov[f'lug_{g}'] = tx.lug(g).translate([0, 0, s])
            allp = {**fixed, **mov, **parts}
            for a, b, v in collisions(allp):
                if a in parts or b in parts or a == 'carrier' or b == 'carrier':
                    bad.append((round(dx, 1), round(dz, 1), a, b, v))
    return bad

def pedal_check():
    """페달(받침·팔·M6 볼트·가변저항·케이블·복귀 스프링) 검사. 간섭 부피 mm³ (0 이 정상, 끝 ±1° 는 멈춤이 닿아야 정상)"""
    base = tx.pedal_base()
    py = tx.PEDAL_PIV_Y
    tr, ts = tx.PEDAL_REST, tx.PEDAL_REST + tx.PEDAL_TRAVEL
    R = {'travel_deg': round(tx.PEDAL_TRAVEL, 2)}
    R['arm^base'] = {f'{th:.1f}': round((tx.pedal_arm_placed(th) ^ base).volume(), 2)
                     for th in (tr - 1.0, tr, (tr + ts) / 2, ts, ts + 1.0)}
    bolt = tx.along_x(cyl(3.0, 25, -22.5) + cyl(5.0, 4, -26.5)).translate([0, py, 0])          # M6x25 머리 x=-22.5 바깥
    face = 22.5 - tx.PEDAL_POT_P
    pot = tx.along_x(cyl(8.5, 10, face) + cyl(3.5, 7, face - 7)).translate([0, py, 0])        # 몸통 Ø17 + 부싱
    R['bolt^base'] = round((bolt ^ base).volume(), 2)
    R['pot^base'] = round((pot ^ base).volume(), 2)
    R['bolt^arm'] = max(round((bolt ^ tx.pedal_arm_placed(th)).volume(), 2) for th in (tr, ts))
    R['pot_shaft_tip_in_D_mm'] = round(tx.PEDAL_T / 2 - (face - 15.0), 2)                    # 축 15 (부싱 포함) 가 D 구멍에 들어간 깊이
    cab0, cab1, spr0, spr1, nb, nfm = tx.pedal_points()
    u, nbs, nfs = tx.pedal_dirs(ts)
    cab0s = np.array([py, 0.0]) + tx.PEDAL_CABLE_B * u + tx.PEDAL_W / 2 * nbs
    pull = float(np.linalg.norm(cab1 - cab0s) - np.linalg.norm(cab1 - cab0))
    R['release_ring_travel_mm'] = round(pull * (tx.FORK_PIV_Y - tx.H) / (tx.FORK_CABLE_Y - tx.FORK_PIV_Y), 2)
    for nm, p in (('rest', cab0), ('stop', cab0s)):
        d = cab1 - p; L = float(np.linalg.norm(d))
        R[f'cable_{nm}^base'] = round((tx._yz_cyl(p + 0.5 * d / L, d / L, 0.8, L - 0.5) ^ base).volume(), 2)
    spr0s = np.array([py, 0.0]) + tx.PEDAL_SPR_B * u + (tx.PEDAL_W / 2 - 1.5) * nfs
    R['spring_len_rest_stop'] = [round(float(np.linalg.norm(spr1 - p)) + 3.0, 2) for p in (spr0, spr0s)]
    return R


def steer_check():
    """핸들 받침 검사. 간섭 부피 mm³ (0 이 정상). 멈춤: ±135° 에서 닿기 시작 → ±137° 는 겹쳐야 정상.
    캠-롤러는 닿아 있어야 함 (틈 0). 복귀 토크 = 스프링 2개 힘 x 캠 기울기 (아르키메데스: 10mm / 135°)"""
    fr, cov, base = tx.steer_frame(), tx.steer_cover(), tx.steer_base()
    hub0, cam0 = tx.steer_hub(), tx.steer_cam()
    z0c, z1c = tx.ST_CAM_Z
    shaft = cyl(6.0, tx.ST_SHAFT[1] - tx.ST_SHAFT[0], tx.ST_SHAFT[0])
    brgs = tube(14.0, 6.05, 8.0, tx.ST_BRG[0]) + tube(14.0, 6.05, 8.0, tx.ST_BRG[1])
    wash = tube(7.5, 6.15, 1.5, tx.ST_CH[0])
    pz = tx.ST_COVER[1]
    pot = cyl(8.5, 10.0, pz) + cyl(3.5, 7.0, pz - 7.0) + cyl(5.8, 3.0, pz - 7.0)             # 몸통 Ø17, 부싱 M7, 너트 (맞변 10)
    pot_shaft0 = cyl(2.9, 15.0, pz - 15.0)                                                       # 톱니 축 (압입 구멍 안)
    table = boxm(-500, 500, -tx.ST_H - 40, -tx.ST_H, tx.ST_EDGE, 600)
    wheel = cyl(165.0, 30.0, tx.ST_HUB[0] - 30.0)                                               # 핸들 Ø330 두께 30 (가정)
    still = {'frame': fr, 'cover': cov, 'pot': pot, 'bearings': brgs}
    R = {'static': {'frame^cover': round((fr ^ cov).volume(), 2), 'frame^base': round((fr ^ base).volume(), 2),
                    'frame^bearings': round((fr ^ brgs).volume(), 2), 'shaft^frame': round((shaft ^ fr).volume(), 2),
                    'pot^frame': round((pot ^ fr).volume(), 2), 'wheel^table': round((wheel ^ table).volume(), 2),
                    'wheel^base': round((wheel ^ base).volume(), 2)}}
    rows = {}
    for th in (-137.0, -135.0, -134.0, -90.0, -45.0, -10.0, 0.0, 10.0, 45.0, 90.0, 134.0, 135.0, 137.0):
        yr = -tx.st_pitch(th)
        hub, cam = hub0.rotate([0, 0, th]), cam0.rotate([0, 0, th])
        yoke = tx.steer_yoke(min(abs(th), tx.ST_RANGE))
        roller = tube(14.0, 6.05, 8.0, z0c).translate([0, yr, 0])
        pin = cyl(6.0, 22.0, tx.ST_CH[0] + 0.5).translate([0, yr, 0])
        rw = (tube(7.5, 6.15, 1.5, tx.ST_CH[0]) + tube(7.5, 6.15, 1.0, z1c)).translate([0, yr, 0])
        spr = M.batch_boolean([tx.along_y(tube(9.0, 7.4, (yr - 20.0) - (tx.ST_CH[3] - 2.0), 0)).translate([s * tx.ST_SPR_X, tx.ST_CH[3] - 2.0, (tx.ST_CH[0] + tx.ST_CH[1]) / 2])
                               for s in (-1, 1)], mf.OpType.Add)
        moving = {'hub': hub, 'cam': cam, 'pot_shaft': pot_shaft0.rotate([0, 0, th]), 'shaft': shaft, 'wash': wash}
        follower = {'yoke': yoke, 'roller': roller, 'pin': pin, 'roller_wash': rw, 'springs': spr}
        r = {}
        for a, ma in list(moving.items()) + list(follower.items()):
            for b, mb in still.items():
                if (a, b) in (('pot_shaft', 'pot'), ('shaft', 'bearings')):
                    continue
                v = (ma ^ mb).volume()
                if v > 0.01:
                    r[f'{a}^{b}'] = round(v, 2)
        for a, ma in moving.items():
            for b, mb in follower.items():
                v = (ma ^ mb).volume()
                if v > 0.01:
                    r[f'{a}^{b}'] = round(v, 2)
        r['cam_roller_gap'] = round(float(tx.affinity.rotate(tx.steer_cam_poly(), th, origin=(0, 0)).distance(tx.Point(0, yr).buffer(14.0, 256))), 3)
        r['spring_len'] = round((yr - 20.0) - (tx.ST_CH[3] - 2.0), 2)
        rows[f'{th:.0f}'] = r
    R['angles'] = rows
    c = tx.ST_LIFT / math.radians(tx.ST_RANGE)                                                 # 캠 기울기 mm/rad
    R['return_torque_Nm'] = {f'{th}': round(2 * tx.SPRING_K * (tx.SPRING_L0 - (tx.ST_SPR_PRE - (tx.st_pitch(th) - tx.ST_PITCH0))) * c / 1000, 3)
                             for th in (0.5, 15, 45, 90, 135)}
    return R

