"""클러치·크랭크·페달 출력 판 배치 (UM2+ 223x223, 가장자리 16 여유: 유리 클립 피함, 부품 사이 6 이상)"""
import os, math, trimesh, numpy as np
from shapely.geometry import MultiPoint, box
from shapely import affinity
ROOT = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(ROOT, '..', 'stl'); OUT = os.path.join(ROOT, '..', 'plates')
HALF, GAP = 95.0, 6.0
PLATES = {
    'C1_clutch_front_press': [('70_cl_front', 1), ('72_cl_pressure', 1), ('35_collar_end_8', 1), ('79_cl_spring_cup', 3), ('73_cl_standoff', 3), ('79b_cl_end_spacer', 1)],
    'C2_clutch_back_release': [('71_cl_back', 1), ('77_cl_fork', 1), ('75_cl_ring', 1), ('76_cl_carrier', 1), ('74_cl_disc_hub', 1)],
    'C3_pedal_arm_wheel': [('80_pedal_arm', 1), ('43_display_wheel', 1), ('78_cl_fork_bracket', 1), ('81_pedal_pad', 1)],
    'C4_pedal_base': [('82_pedal_base', 1)],
    'C5_motor_riser': [('45_motor_riser', 1)],
    'C6_wheel_guard': [('44_wheel_guard', 1)],
}
def foot(m):
    return MultiPoint(m.vertices[:, :2]).convex_hull
def place(items):
    placed = []   # (mesh, poly)
    bed = box(-HALF, -HALF, HALF, HALF)
    for name, q in items:
        for _ in range(q):
            m0 = trimesh.load(os.path.join(STL, name + '.stl'))
            best = None
            for ang in range(0, 180, 15):
                m = m0.copy(); m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(ang), [0, 0, 1]))
                p = foot(m)
                for y in np.arange(-HALF, HALF, 2.0):
                    for x in np.arange(-HALF, HALF, 2.0):
                        b = p.bounds
                        dx, dy = x - b[0], y - b[1]
                        if x + (b[2] - b[0]) > HALF or y + (b[3] - b[1]) > HALF: continue
                        pp = affinity.translate(p, dx, dy)
                        if any(pp.distance(o) < GAP for _, o in placed): continue
                        score = (y + (b[3] - b[1])) * 1000 + x      # 아래·왼쪽부터
                        if best is None or score < best[0]: best = (score, ang, dx, dy, pp)
                        break
            assert best, name
            _, ang, dx, dy, pp = best
            m = m0.copy(); m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(ang), [0, 0, 1])); m.apply_translation([dx, dy, -m.bounds[0][2]])
            placed.append((m, pp))
    m = trimesh.util.concatenate([a for a, _ in placed])
    c = m.bounds.mean(0); m.apply_translation([-c[0], -c[1], -m.bounds[0][2]])
    return m, [p for _, p in placed]
if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for k, items in PLATES.items():
        m, polys = place(items)
        m.export(os.path.join(OUT, k + '.stl'))
        print(k, [round(x) for x in m.extents], len(m.split(only_watertight=False)), 'parts')
