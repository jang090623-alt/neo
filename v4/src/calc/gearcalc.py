"""기어 이뿌리 응력 계수 계산 (v4)
1) 이 모양: v3(뿌리 모서리 각짐) / v4(뿌리 필렛 0.38m + 이끝 라운드)
2) ISO 6336-3 방법 B 식을 실제 이 모양(다각형)에 적용 → Y_F, Y_S (이끝 하중)
3) 2D 유한요소(평면응력)로 같은 하중을 걸어 이뿌리 최대 인장응력 → Y_FS 직접 계산
"""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString
from shapely import affinity

MOD, PA, BL = 3.0, math.radians(20), 0.20
inv = lambda a: math.tan(a) - a


def gear_poly_v3(z, m=MOD, n_flank=14):
    """v3 tx.py 와 같은 식 (뿌리: 기초원~이뿌리원 사이 반지름 방향 직선, 모서리 각짐)"""
    rp = m * z / 2; rb = rp * math.cos(PA); ra = rp + m; rf = rp - 1.25 * m
    sp = math.pi * m / 2 - BL
    def psi(r):
        a = math.acos(min(1, rb / r)); return sp / (2 * rp) + inv(PA) - inv(a)
    rs = np.linspace(max(rb, rf), ra, n_flank)
    pts = []
    for k in range(z):
        c = 2 * math.pi * k / z
        flank = [(r, psi(r)) for r in rs]
        if rf < rb: flank = [(rf, psi(rb))] + flank
        for r, p in flank: pts.append((r * math.cos(c - p), r * math.sin(c - p)))
        for r, p in reversed(flank): pts.append((r * math.cos(c + p), r * math.sin(c + p)))
        a0 = c + psi(max(rb, rf)); a1 = c + 2 * math.pi / z - psi(max(rb, rf))
        for a in np.linspace(a0, a1, 6)[1:-1]: pts.append((rf * math.cos(a), rf * math.sin(a)))
    return Polygon(pts)


def gear_poly_v4(z, m=MOD, fillet=0.38, tip=0.25):
    """v4: 뿌리 오목 모서리를 반지름 fillet*m 로 둥글게(닫힘 연산), 이끝 볼록 모서리를 tip(mm)로 둥글게(열림 연산).
    플랭크(인벌류트)는 그대로라 기어비·맞물림은 변하지 않음."""
    p = gear_poly_v3(z, m, n_flank=40)
    r = fillet * m
    p = p.buffer(r, 64, join_style=1).buffer(-r, 64, join_style=1)
    if tip > 0:
        p = p.buffer(-tip, 64, join_style=1).buffer(tip, 64, join_style=1)
    return p


def tooth_geometry(z, m=MOD):
    rp = m * z / 2; rb = rp * math.cos(PA); ra = rp + m; rf = rp - 1.25 * m
    sp = math.pi * m / 2 - BL
    def psi(r):
        a = math.acos(min(1, rb / r)); return sp / (2 * rp) + inv(PA) - inv(a)
    return rp, rb, ra, rf, psi


def iso_method_b(poly, z, m=MOD, tip_r=0.25):
    """ISO 6336-3 방법 B (이끝 하중, 하중 분담 없음) 을 다각형 이 모양에 직접 적용.
    0번 이는 +x 축 대칭. 위쪽(y>0) 플랭크에 하중 → 30° 접선점에서 단면."""
    rp, rb, ra, rf, psi = tooth_geometry(z, m)
    # 0번 이 위쪽 경계 점들 (각도 0 ~ π/z)
    ring = np.array(poly.exterior.coords)
    ang = np.arctan2(ring[:, 1], ring[:, 0])
    rad = np.hypot(ring[:, 0], ring[:, 1])
    sel = (ang > 0) & (ang < math.pi / z) & (rad < rp)
    pts = ring[sel]
    # 반지름 순으로 정렬해 뿌리 → 플랭크 곡선
    order = np.argsort(np.hypot(pts[:, 0], pts[:, 1]))
    pts = pts[order]
    # 접선 각 (중심선 = x축과 이루는 각)
    best = None
    for i in range(1, len(pts) - 1):
        d = pts[i + 1] - pts[i - 1]
        if np.linalg.norm(d) < 1e-9: continue
        t = math.degrees(math.atan2(abs(d[1]), abs(d[0])))   # 0°=중심선과 평행, 90°=수직
        if best is None or abs(t - 30) < abs(best[0] - 30):
            best = (t, i)
    i = best[1]; P = pts[i]
    # 곡률 반지름: 이웃 점들로 원 맞춤
    nb = pts[max(0, i - 4): i + 5]
    A = np.c_[2 * nb[:, 0], 2 * nb[:, 1], np.ones(len(nb))]
    bb = (nb ** 2).sum(1)
    cx, cy, cc = np.linalg.lstsq(A, bb, rcond=None)[0]
    rho = math.sqrt(cc + cx ** 2 + cy ** 2)
    s_Fn = 2 * P[1]
    # 이끝 하중점: 이끝 라운드 시작점(반지름 ra - tip_r 근처)의 인벌류트 위 점
    r_load = ra - tip_r
    a_l = math.acos(rb / r_load)
    g = psi(r_load)
    T = np.array([r_load * math.cos(g), r_load * math.sin(g)])
    B = np.array([rb * math.cos(g - a_l), rb * math.sin(g - a_l)])
    u = (B - T) / np.linalg.norm(B - T)                 # 하중 방향 (이 안쪽으로)
    # 하중선과 중심선(x축) 교점
    tq = -T[1] / u[1]; Q = T + tq * u
    h_Fe = Q[0] - P[0]
    a_Fen = math.atan2(abs(u[0]), abs(u[1]))            # 하중과 중심선 수직 방향 사이 각
    Y_F = (6 * (h_Fe / m) * math.cos(a_Fen)) / ((s_Fn / m) ** 2 * math.cos(PA))
    L = s_Fn / h_Fe; q_s = s_Fn / (2 * rho)
    Y_S = (1.2 + 0.13 * L) * q_s ** (1 / (1.21 + 2.3 / L))
    return dict(z=z, s_Fn_m=s_Fn / m, h_Fe_m=h_Fe / m, rho_m=rho / m, a_Fen=math.degrees(a_Fen),
                Y_F=Y_F, Y_S=Y_S, Y_FS=Y_F * Y_S, tangent=best[0], load_point=T, force_dir=u)


def lewis_Y(z):
    tab = {12: .245, 13: .261, 14: .277, 15: .290, 16: .296, 17: .303, 18: .309, 19: .314, 20: .322, 21: .328,
           22: .331, 24: .337, 26: .346, 28: .353, 30: .359, 34: .371, 38: .384, 43: .397, 50: .409, 60: .422,
           75: .435, 100: .447, 150: .460, 300: .472}
    ks = sorted(tab)
    if z in tab: return tab[z]
    lo = max(k for k in ks if k < z); hi = min(k for k in ks if k > z)
    return tab[lo] + (tab[hi] - tab[lo]) * (z - lo) / (hi - lo)


# ---------------- 2D 유한요소 (평면응력, 선형 탄성) ----------------
def fe_root_stress(poly, z, m=MOD, b=1.0, E=3200.0, nu=0.36, max_area=0.02, tip_r=0.25, plot=None):
    """이 3개 + 림 영역(반지름 rf-2.5m 에서 고정). 가운데 이의 위쪽 플랭크 이끝 하중점에 법선 하중 F_n.
    반환: 뿌리 최대 주응력 σ1(MPa) 과 F_t=1N 기준 Y_FS = σ1·b·m/F_t"""
    import triangle as tr
    import skfem
    from skfem.models.elasticity import linear_elasticity, lame_parameters
    from skfem.helpers import dot
    rp, rb, ra, rf, psi = tooth_geometry(z, m)
    r_in = rf - 2.5 * m
    pitch = 2 * math.pi / z
    wedge = Polygon([(0, 0)] + [(1.5 * ra * math.cos(a), 1.5 * ra * math.sin(a))
                                for a in np.linspace(-1.5 * pitch, 1.5 * pitch, 60)])
    region = poly.intersection(wedge).difference(Point(0, 0).buffer(r_in, 256))
    if region.geom_type != 'Polygon':
        region = max(region.geoms, key=lambda g: g.area)
    region = region.simplify(0.002)
    xy = np.array(region.exterior.coords)[:-1]
    n = len(xy)
    segs = np.c_[np.arange(n), (np.arange(n) + 1) % n]
    T = tr.triangulate({'vertices': xy, 'segments': segs}, f'pq30a{max_area}')
    p = T['vertices'].T; t = T['triangles'].T
    mesh = skfem.MeshTri(p, t)
    e = skfem.ElementVector(skfem.ElementTriP2())
    ib = skfem.Basis(mesh, e)
    K = skfem.asm(linear_elasticity(*lame_parameters(E, nu)), ib)
    # 평면응력: lame λ* = 2λμ/(λ+2μ)
    lam, mu = lame_parameters(E, nu)
    lam_ps = 2 * lam * mu / (lam + 2 * mu)
    K = skfem.asm(linear_elasticity(lam_ps, mu), ib)
    # 고정: 안쪽 원호 (반지름 ≈ r_in)
    rr = np.hypot(*mesh.p)
    fixed_nodes = np.where(np.abs(rr - r_in) < 0.05)[0]
    D = ib.get_dofs(lambda x: np.abs(np.hypot(x[0], x[1]) - r_in) < 0.05).all()
    # 하중: 가운데 이 위쪽 플랭크, 이끝 하중점 근처 노드에 집중하중 F_n (F_t=1N → F_n = 1/cos20)
    r_load = ra - tip_r; a_l = math.acos(rb / r_load); g = psi(r_load)
    Tp = np.array([r_load * math.cos(g), r_load * math.sin(g)])
    Bp = np.array([rb * math.cos(g - a_l), rb * math.sin(g - a_l)])
    u = (Bp - Tp) / np.linalg.norm(Bp - Tp)
    Fn = 1.0 / math.cos(PA) / b          # 두께 b 당 (평면응력: 단위 두께 b=1 → 결과에 b 반영)
    # 가장 가까운 경계 노드
    bnodes = mesh.boundary_nodes()
    k = bnodes[np.argmin(np.hypot(mesh.p[0, bnodes] - Tp[0], mesh.p[1, bnodes] - Tp[1]))]
    f = np.zeros(K.shape[0])
    dofs = ib.nodal_dofs[:, k]
    f[dofs[0]] += Fn * u[0]; f[dofs[1]] += Fn * u[1]
    x = skfem.solve(*skfem.condense(K, f, D=D))
    # 응력 (요소 중심이 아니라 P1 투영)
    from skfem.helpers import sym_grad
    ib1 = ib.with_element(skfem.ElementVector(skfem.ElementTriP1()))
    sb = skfem.Basis(mesh, skfem.ElementTriP1())
    ux = ib.interpolate(x)
    eps = sym_grad(ux)
    def proj(field):
        @skfem.LinearForm
        def lf(v, w): return field(w) * v
        @skfem.BilinearForm
        def mf(u_, v, w): return u_ * v
        return skfem.solve(skfem.asm(mf, sb), skfem.asm(lf, sb))
    exx = eps[0, 0]; eyy = eps[1, 1]; exy = eps[0, 1]
    c = E / (1 - nu ** 2)
    sxx = c * (exx + nu * eyy); syy = c * (eyy + nu * exx); sxy = E / (1 + nu) * exy
    Sxx = proj(lambda w: c * (sym_grad(w['u'])[0, 0] + nu * sym_grad(w['u'])[1, 1])) if False else None
    # 간단히: 요소 적분점 응력 → 최대 주응력
    s1 = 0.5 * (sxx + syy) + np.sqrt((0.5 * (sxx - syy)) ** 2 + sxy ** 2)
    qp = ib.global_coordinates().value       # (2, nelem, nqp)
    rq = np.hypot(qp[0], qp[1])
    aq = np.arctan2(qp[1], qp[0])
    # 가운데 이의 하중 반대쪽(인장) 뿌리: 하중이 -y로 미므로 위쪽(y>0) 뿌리가 인장
    mask = (rq < rp) & (rq > rf - 0.5) & (aq > 0) & (aq < pitch / 2 + 0.05)
    s1_root = float(np.max(s1[mask]))
    Y_FS = s1_root * b * m / 1.0             # F_t = 1 N 일 때
    return dict(sigma_root=s1_root, Y_FS_FE=Y_FS, nelem=mesh.t.shape[1], nnode=mesh.p.shape[1])


if __name__ == '__main__':
    for z in (17, 22, 27, 31, 30, 35, 36, 39, 41, 44, 49):
        old = gear_poly_v3(z, n_flank=40); new = gear_poly_v4(z)
        r_old = iso_method_b(old, z); r_new = iso_method_b(new, z)
        print(f"z{z}: Lewis 1/Y={1/lewis_Y(z):.2f} | v3 ISO Y_F={r_old['Y_F']:.2f} Y_S={r_old['Y_S']:.2f} YFS={r_old['Y_FS']:.2f} rho/m={r_old['rho_m']:.3f}"
              f" | v4 Y_F={r_new['Y_F']:.2f} Y_S={r_new['Y_S']:.2f} YFS={r_new['Y_FS']:.2f} rho/m={r_new['rho_m']:.3f} s/m={r_new['s_Fn_m']:.2f} h/m={r_new['h_Fe_m']:.2f} tan={r_new['tangent']:.1f}")


# ---------------- v4: 랙 커터 창성 (실제 호브 가공과 같은 트로코이드 필렛) ----------------
def rack_cutter_tooth(m=MOD, bl=BL, rho=0.38, h_cut=1.25, x_shift=0.0, ext=12.0):
    """기준선이 x = 0 (반지름 방향 바깥이 +x), 커터 이가 -x(블랭크 안쪽)로 h_cut*m 들어감.
    이두께(기준선) = πm/2 + bl → 깎인 기어 이두께 = πm/2 - bl. 끝 모서리 반지름 rho*m."""
    a = PA
    w0 = (math.pi * m / 2 + bl) / 2
    d = h_cut * m - x_shift * m          # 전위: 커터를 바깥으로 x·m 이동 → 깊이 감소
    tip_x = -d
    pts = [(ext, w0 + ext * math.tan(a)), (tip_x, w0 - d * math.tan(a)),
           (tip_x, -(w0 - d * math.tan(a))), (ext, -(w0 + ext * math.tan(a)))]
    p = Polygon(pts)
    r = rho * m
    p = p.buffer(-r, 64, join_style=1).buffer(r, 64, join_style=1)
    return p


def gear_poly_gen(z, m=MOD, bl=BL, rho=0.38, x_shift=0.0, tip=0.25, steps=900):
    """랙 커터를 굴려 창성한 기어 외형 (전위 x_shift). 0번 이가 +x 축 대칭."""
    rp = m * z / 2
    ra = rp + m + x_shift * m
    cutter = rack_cutter_tooth(m, bl, rho, x_shift=x_shift)
    # 커터 기준선이 x = rp + x·m 에 오도록 (전위 = 커터를 바깥으로)
    cut_pieces = []
    span = 2.2 * math.pi / z + 0.35
    for phi in np.linspace(-span, span, steps):
        c = affinity.translate(cutter, rp + x_shift * m, rp * phi)   # 커터가 y 로 rp·φ 이동
        c = affinity.rotate(c, -phi, origin=(0, 0), use_radians=True)
        cut_pieces.append(c)
    from shapely.ops import unary_union
    space = unary_union(cut_pieces)
    # 한 이 홈(각도 0 에 홈) → 반 피치 돌려 이가 0에 오게
    blank = Point(0, 0).buffer(ra, 720)
    sector = Polygon([(0, 0)] + [(2 * ra * math.cos(t), 2 * ra * math.sin(t))
                                 for t in np.linspace(-math.pi / z * 1.02, math.pi / z * 1.02, 40)])
    one = space.intersection(sector)
    cuts = unary_union([affinity.rotate(one, 2 * math.pi * k / z + math.pi / z, origin=(0, 0), use_radians=True)
                        for k in range(z)])
    g = blank.difference(cuts)
    if tip > 0:
        g = g.buffer(-tip, 32, join_style=1).buffer(tip, 32, join_style=1)
    return g.simplify(0.003)
