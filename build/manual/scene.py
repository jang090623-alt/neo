"""설명서 그림용 부품 메시 내보내기 (조립 좌표, mm). 결과: manual/parts/*.stl + parts.json"""
import os, sys, json, math, numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import tx, asm
from tx import cyl, boxm, ext, hexagon, along_x, along_y, tube
OUT = os.path.join(HERE, 'parts'); os.makedirs(OUT, exist_ok=True)

def save(m, name):
    me = m.to_mesh()
    t = trimesh.Trimesh(vertices=np.array(me.vert_properties)[:, :3], faces=np.array(me.tri_verts))
    t.merge_vertices(digits_vertex=4)
    t.export(os.path.join(OUT, name + '.stl'))
    return [list(map(float, t.bounds[0])), list(map(float, t.bounds[1]))]

P = asm.assemble('N', carrier_side=1)
for k in ('acr_left', 'acr_right', 'acr_top'):
    P.pop(k, None)
H = tx.H
# 끝판 A 안쪽 면 M4 너트 4 (클러치 브래킷) + 브래킷 볼트 M4x16
for i, (xb, yb) in enumerate(tx.FORK_BRK_HOLES):
    P[f'nutA_{i}'] = ext(hexagon(7.0), 3.2, -3.6).translate([xb, yb, 0])
# 클러치 브래킷 M4x16 (머리 자리 깊이 3 → 머리 윗면 z = -PLATE_T-5+3-?)
zb = -tx.PLATE_T - 5.0
for i, (xb, yb) in enumerate(tx.FORK_BRK_HOLES):
    P[f'brkbolt_{i}'] = (cyl(2.0, 16.0, zb + 3.0) + cyl(3.5, 4.0, zb + 3.0 - 4.0)).translate([xb, yb, 0])
# 홀센서 A3144 (케이지 홈 6, 바퀴 덮개 1) · 자석 Ø6x3 (러그 밑면 3)
for g, xr in tx.RAIL_X.items():
    for dz in (-tx.TRAVEL, tx.TRAVEL):
        P[f'hall_{g}_{int(dz):+d}'] = boxm(xr + 5.5 - 2.0, xr + 5.5 + 2.0, 161 - 1.5, 161.9, tx.LUG_Z + dz - 1.5, tx.LUG_Z + dz + 1.5)
    P[f'mag_lug_{g}'] = along_y(cyl(3.0, 3.0, 0)).translate([xr + 5.5, tx.RAIL_Y - 8 + 0.1, tx.LUG_Z])
ys = H - tx.GUARD_R[0]; zw = tx.Z_WHEEL + tx.WHEEL_T / 2
P['hall_rpm'] = boxm(tx.C - 2.0, tx.C + 2.0, ys - 1.6, ys - 0.1, zw - 1.5, zw + 1.5)
# 출력 1단 기어의 강철 핀 (Ø5, 나온 길이 PIN_OUT) — 핀 박기 그림용
ph = asm.mesh_phase((0, H), tx.PAIRS['1'][0], 0.0, (tx.C, H), tx.PAIRS['1'][1])
face = tx.PLANE['1']
pins = None
for k in range(tx.PIN_N):
    a = 2 * math.pi * k / tx.PIN_N
    c = cyl(2.5, tx.PIN_OUT, face - tx.PIN_OUT).translate([tx.PIN_R * math.cos(a), tx.PIN_R * math.sin(a), 0])
    pins = c if pins is None else pins + c
P['pinsteel_1'] = pins.rotate([0, 0, math.degrees(ph)]).translate([tx.C, H, 0])
info = {}
for n, m in P.items():
    info[n] = save(m, n)
# 페달 (페달 받침 좌표: 바닥 y=0, 피벗 x 축)
def arm_xf(m, th):
    t = math.radians(th)
    R0 = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]], float)
    Rx = np.array([[1, 0, 0], [0, math.cos(t), -math.sin(t)], [0, math.sin(t), math.cos(t)]])
    A = np.zeros((3, 4)); A[:, :3] = Rx @ R0; A[:, 3] = Rx @ np.array([-tx.PEDAL_T / 2, 0, 0]) + np.array([0, tx.PEDAL_PIV_Y, 0])
    return m.transform(A)
th = tx.PEDAL_REST
Q = {}
Q['ped_base'] = tx.pedal_base()
Q['ped_arm'] = tx.pedal_arm_placed(th)
pad = tx.pedal_pad().rotate([0, 90, 0])            # 두께(z) → x 방향
b = pad.bounding_box()
pad = pad.translate([-tx.PEDAL_W / 2 - b[3], 180.0 - (b[1] + b[4]) / 2, tx.PEDAL_T / 2 - (b[2] + b[5]) / 2])   # 운전자 쪽 면 a=-9 밖
Q['ped_pad'] = arm_xf(pad, th)
py = tx.PEDAL_PIV_Y
Q['ped_bolt'] = along_x(cyl(3.0, 25, -22.5) + cyl(5.0, 4, -26.5)).translate([0, py, 0])
cab0, cab1, spr0, spr1, nb, nfm = tx.pedal_points()
d = spr1 - spr0; L = float(np.linalg.norm(d))
sp1 = tx._yz_cyl(spr0, d / L, 9.0, L) - tx._yz_cyl(spr0 - d / L, d / L, 7.6, L + 2)
Q['ped_spring'] = sum((sp1.translate([xs, 0, 0]) for xs in tx.PEDAL_SPR_X), tx.M())   # 2026-11: 3개
d = cab1 - cab0; L = float(np.linalg.norm(d))
Q['ped_cable'] = tx._yz_cyl(cab0, d / L, 0.9, L + 40.0)
for n, m in Q.items():
    info[n] = save(m, n)
json.dump(info, open(os.path.join(HERE, 'parts.json'), 'w'))
print(len(info), 'parts')
