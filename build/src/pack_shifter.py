"""2026-11 변속기 수정 판 (홈 딸깍·중립 복귀·낮은 피벗). 14번 판(포크·스페이서 9)은 그대로라 원래 파일 사용"""
import os
from pack_clutch import place, OUT
PLATES = {
    'S15_shifter_small_v2': [('57_lower_lever_finger', 1), ('58_spring_spacer', 1), ('32_spacer_43', 3), ('50c_rail_collar', 8),
                             ('56b_cen_piston', 2), ('56d_cen_shoulder', 2), ('51_lug', 3), ('56_carrier_lockplate', 1)],
    'S16_cage_v2': [('52_selector_cage', 1)],
    'S17_pivots_gate_v2': [('53_pivot_lower', 1), ('54_pivot_upper', 1), ('60_gate', 1)],
}
if __name__ == '__main__':
    for k, items in PLATES.items():
        m, polys = place(items)
        m.export(os.path.join(OUT, k + '.stl'))
        print(k, [round(x) for x in m.extents], len(m.split(only_watertight=False)), 'parts', flush=True)
