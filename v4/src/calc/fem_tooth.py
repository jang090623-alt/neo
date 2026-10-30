"""평기어 이뿌리 응력 2D 유한요소 해석 (선형 삼각형 요소, 평면변형)
실제 출력할 이 모양(gear_poly, 이뿌리 필렛 포함)에 이끝 하중 1 N/mm(면폭당, 작용선 방향 = 법선 하중)을 줘서
이뿌리 최대 인장응력을 구합니다. 결과 = 응력계수 [MPa / (법선 하중 N/mm)] → calc 에서 Fn = Ft / cos20° 를 곱함.
"""
import math, numpy as np, triangle
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from shapely.geometry import Point, Polygon, LineString
from shapely import affinity

def tooth_domain(gpoly, z, m, n_teeth=3, x=0.0):
    """이 n_teeth 개를 포함하는 부채꼴 (가운데 이가 +x 축 방향)"""
    rf = m * z / 2 - (1.25 - x) * m
    half = math.pi / z * n_teeth
    r_in = rf - 2.5 * m
    R = m * z / 2 + 3 * m
    sector = Polygon([(0, 0)] + [(R * math.cos(a), R * math.sin(a)) for a in np.linspace(-half, half, 60)])
    return gpoly.intersection(sector).difference(Point(0, 0).buffer(r_in, 256)), r_in, half

def solve(gpoly, z, m, E=3000.0, nu=0.35, max_area=0.02, xsh=0.0):
    dom, r_in, half = tooth_domain(gpoly, z, m, x=xsh)
    if dom.geom_type != 'Polygon':
        dom = max(dom.geoms, key=lambda g: g.area)
    ext = np.array(dom.exterior.coords)[:-1]
    n = len(ext)
    seg = np.c_[np.arange(n), (np.arange(n) + 1) % n]
    T = triangle.triangulate({'vertices': ext, 'segments': seg}, f'pq32a{max_area}')
    P, tri = T['vertices'], T['triangles']
    N = len(P)
    D = E / ((1 + nu) * (1 - 2 * nu)) * np.array([[1 - nu, nu, 0], [nu, 1 - nu, 0], [0, 0, (1 - 2 * nu) / 2]])  # 평면변형
    x = P[tri, 0]; y = P[tri, 1]
    b = np.stack([y[:, 1] - y[:, 2], y[:, 2] - y[:, 0], y[:, 0] - y[:, 1]], 1)
    c = np.stack([x[:, 2] - x[:, 1], x[:, 0] - x[:, 2], x[:, 1] - x[:, 0]], 1)
    A2 = (x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0]) - (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0])
    B = np.zeros((len(tri), 3, 6))
    B[:, 0, 0::2] = b; B[:, 1, 1::2] = c; B[:, 2, 0::2] = c; B[:, 2, 1::2] = b
    B /= A2[:, None, None]
    Ke = np.einsum('eji,jk,ekl->eil', B, D, B) * (A2 / 2)[:, None, None]
    dof = np.stack([2 * tri[:, 0], 2 * tri[:, 0] + 1, 2 * tri[:, 1], 2 * tri[:, 1] + 1, 2 * tri[:, 2], 2 * tri[:, 2] + 1], 1)
    I = np.repeat(dof, 6, 1).ravel(); J = np.tile(dof, (1, 6)).ravel()
    K = coo_matrix((Ke.ravel(), (I, J)), shape=(2 * N, 2 * N)).tocsr()
    r = np.hypot(P[:, 0], P[:, 1]); ang = np.arctan2(P[:, 1], P[:, 0])
    fixed = (r < r_in + 1e-3) | (np.abs(np.abs(ang) - half) < 1e-4)
    # 하중: 가운데 이(+x 방향) 의 +y 쪽 이끝 근처 → 작용선 방향(-y 성분, 이를 -y로 굽힘)
    rb = m * z / 2 * math.cos(math.radians(20)); ra = m * z / 2 + m * (1 + xsh)
    # v4.1 수정(독립 검산 E2): 하중점 = 이끝 둥글림(0.25) 바로 아래 플랭크 = 인벌류트 끝 (이전: 1mm 아래 점이 골라짐)
    r_load = ra - 0.25
    cand = np.where((np.abs(r - r_load) < 0.15) & (P[:, 1] > 0) & (np.abs(ang) < math.pi / z))[0]
    k0 = cand[np.argmax(ang[cand])]                     # 그 반지름에서 가장 플랭크 쪽 점
    p0 = P[k0]
    near = np.where(np.hypot(P[:, 0] - p0[0], P[:, 1] - p0[1]) < 0.4)[0]
    # 작용선: 기초원 접선, 하중점에서 이에 수직 방향 (인벌류트 법선)
    th = math.atan2(p0[1], p0[0]); rr = math.hypot(*p0)
    alpha = math.acos(min(1, rb / rr))          # 그 점의 압력각
    # 법선은 반지름 방향에서 (90°-alpha) 돌아간 방향, 이를 -y 쪽(회전 반대)으로 미는 방향
    nrm = np.array([math.cos(th - (math.pi / 2 - alpha) - math.pi / 2 * 0), 0.0])
    t_hat = np.array([-math.sin(th), math.cos(th)]); r_hat = np.array([math.cos(th), math.sin(th)])
    force_dir = -(math.cos(alpha) * t_hat) - math.sin(alpha) * r_hat      # 접선 성분(이를 굽힘) + 반지름 안쪽 성분
    force_dir /= np.linalg.norm(force_dir)
    F = np.zeros(2 * N)
    for k in near:
        F[2 * k] += force_dir[0] / len(near); F[2 * k + 1] += force_dir[1] / len(near)
    free = np.where(~np.repeat(fixed, 2))[0]
    u = np.zeros(2 * N)
    u[free] = spsolve(K[free][:, free].tocsc(), F[free])
    eps = np.einsum('eij,ej->ei', B, u[dof])
    sig = eps @ D.T
    sx, sy, txy = sig[:, 0], sig[:, 1], sig[:, 2]
    s1 = (sx + sy) / 2 + np.sqrt(((sx - sy) / 2) ** 2 + txy ** 2)
    cen = P[tri].mean(1)
    rc = np.hypot(cen[:, 0], cen[:, 1]); ac = np.arctan2(cen[:, 1], cen[:, 0])
    rf = m * z / 2 - (1.25 - xsh) * m
    # 이뿌리 영역: 반지름 rf-0.5 ~ rf+1.2m, 가운데 이 근처, 하중점·고정단에서 떨어진 곳
    zone = (rc > rf - 0.5) & (rc < rf + 1.2 * m) & (np.abs(ac) < 1.5 * math.pi / z) & \
           (np.hypot(cen[:, 0] - p0[0], cen[:, 1] - p0[1]) > 2.0)
    i_t = np.argmax(np.where(zone, s1, -1e9))
    s3 = (sx + sy) / 2 - np.sqrt(((sx - sy) / 2) ** 2 + txy ** 2)
    i_c = np.argmin(np.where(zone, s3, 1e9))
    return {'z': z, 'nodes': N, 'elems': len(tri), 'load_r': round(rr, 2), 'load_alpha_deg': round(math.degrees(alpha), 1),
            'sigma_t_per_Nmm': round(float(s1[i_t]), 3), 'at_r': round(float(rc[i_t]), 2),
            'sigma_c_per_Nmm': round(float(s3[i_c]), 3)}

if __name__ == '__main__':
    import sys, json
    import os
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # src/
    sys.path.insert(0, ROOT)
    import tx, gearcalc
    out = []
    for z in (17, 22, 27, 30, 31, 35, 36, 39, 41, 44, 49):
        x = tx.XSH.get(z, 0.0)
        variants = [('gen', tx.gear_poly(z), x),                                              # v4.1 랙 창성 (+전위)
                    (1.0, gearcalc.gear_poly_v3(z, n_flank=40).buffer(1.0, 16).buffer(-1.0, 16), 0.0),   # v4 직선 뿌리 + 필렛 R1
                    (0.0, gearcalc.gear_poly_v3(z, n_flank=40), 0.0)]                         # v3 각진 뿌리
        for name, g, xx in variants:
            res = solve(g, z, tx.MOD, xsh=xx)
            res['fillet'] = name; res['x'] = xx
            out.append(res); print(res, flush=True)
    json.dump(out, open(os.path.join(ROOT, 'calc', 'fem_tooth.json'), 'w'), indent=1)
