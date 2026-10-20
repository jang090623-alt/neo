"""v4: 출력 방향으로 돌려 STL 저장 + 부품표(수량·분류·비고)"""
import os
import numpy as np, trimesh
import tx

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, '..', 'stl')   # v4/stl (배포 폴더에 바로 저장)

def to_print(m, rot=(0, 0, 0)):
    """rot(도) 회전 → 바닥 z=0, xy 중심 0"""
    m = m.rotate(list(rot))
    b = m.bounding_box()
    return m.translate([-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]])

def save(m, name):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(vertices=np.array(mesh.vert_properties)[:, :3], faces=np.array(mesh.tri_verts))
    t.merge_vertices(digits_vertex=5)
    path = os.path.join(OUT, name + '.stl'); t.export(path)
    return path

def parts():
    """(파일명, 메시(출력방향), 수량, 분류, 비고)"""
    L = []
    add = lambda n, m, q, cat, note='': L.append((n, m, q, cat, note))
    flip = (180, 0, 0)
    # 0 시험편
    add('00_coupon_tolerance', to_print(tx.coupon()), 1, '0 시험', '구멍 공차 (v3와 같음)')
    add('01_fit_hub_sleeve', to_print(tx.fit_test()), 1, '0 시험', '허브-슬리브 키 (v3와 같음)')
    add('02_fit_pins_6003', to_print(tx.pin_fit_test()), 1, '0 시험', 'Ø5 핀 압입 4.8/4.9/5.0, 6003 자리 34.9/35.05/35.2 (핀·베어링 도착 후)')
    # 1 기어
    for k, (zi, zo) in tx.PAIRS.items():
        add(f'10_gear_in_{k}_z{zi}', to_print(tx.fixed_gear(zi)), 1, '1 기어', f'{k}단 입력 (양면 D구멍)')
        add(f'11_gear_out_{k}_z{zo}', to_print(tx.free_gear(zo)), 1, '1 기어', f'{k}단 출력 (베어링 2, 핀 구멍 면이 위)')
    add('10_gear_in_R_z17', to_print(tx.fixed_gear(17)), 1, '1 기어', '후진 입력 (양면 D구멍)')
    add('11_gear_out_R_z41', to_print(tx.free_gear(41)), 1, '1 기어', '후진 출력 (베어링 2, 핀 구멍 면이 위)')
    add('12_gear_idler_z17', to_print(tx.idler_gear()), 1, '1 기어', '후진 아이들러 (베어링 2)')
    # 2 슬리브·허브
    add('20_hub', to_print(tx.hub()), 3, '2 슬리브', '양면 D구멍, 세워서')
    add('21_sleeve_half', to_print(tx.sleeve_half()), 6, '2 슬리브', '포켓 면이 위, M3x20 3개 + 너트로 링과 결합 (머리·너트는 육각 자리 안)')
    add('22_sleeve_ring', to_print(tx.sleeve_ring()), 3, '2 슬리브', '포크 홈')
    # 3 축 부속
    add('30_spacer_3', to_print(tx.spacer(3.0)), 9, '3 축 부속', '출력 4 + 입력 4 + 아이들러 1')
    add('31_spacer_1', to_print(tx.spacer(1.0)), 6, '3 축 부속', '허브 양 끝 (베어링 내륜만 누름)')
    add('32_spacer_43', to_print(tx.spacer(tx.HUB_LEN)), 3, '3 축 부속', '입력축: 그룹 안 두 기어 사이')
    add('33_spacer_plate_9', to_print(tx.plate_spacer()), 4, '3 축 부속', '끝판 베어링 ~ 칼라')
    add('34_collar_M3', to_print(tx.collar()), 5, '3 축 부속', '축 끝 4 + 아이들러 1 (M3x12 자가탭 1)')
    add('35_collar_end_8', to_print(tx.collar(w=8.0)), 1, '3 축 부속', '입력축 맨 끝 (파일럿 베어링 고정, M3x12 자가탭 1)')
    # 4 프레임
    add('40_plate_A', to_print(tx.end_plate('A')), 1, '4 프레임', '바깥면 바닥 (모터 쪽, 아이들러 축, 포크 브래킷)')
    add('41_plate_B', to_print(tx.end_plate('B'), flip), 1, '4 프레임', '바깥면 바닥 (셀렉터·rpm 센서 쪽)')
    add('42_foot_bracket', to_print(tx.foot_bracket()), 4, '4 프레임', 'MDF 고정')
    add('43_display_wheel', to_print(tx.display_wheel()), 1, '4 프레임', '출력축 표시 바퀴 (끝판 B 바깥, 자석 Ø6x3 1, M3 무두볼트 1)')
    add('44_wheel_guard', to_print(tx.wheel_guard()), 1, '4 프레임', '바퀴 덮개 + A3144 자리 (끝판 B, M3 4)')
    add('45_motor_riser', to_print(tx.motor_riser(), (-90, 0, 0)), 1, '4 프레임', 'K9B 브래킷 아래, 높이 19, 윗면이 바닥 (밑면 너트 홈에 M6 너트 4 → MDF 에 붙이기 전에)')
    add('46_clutch_hood', to_print(tx.clutch_hood(), flip), 1, '4 프레임', '클러치 덮개: 탭 쪽 끝이 바닥 (M3 3 + 목재나사 4)')
    add('47_hood_front', to_print(tx.hood_front()), 1, '4 프레임', '클러치 덮개 앞판 (M3 4)')
    add('48_end_cap', to_print(tx.collar_cap()), 2, '4 프레임', '축 끝 덮개: 끝판 A 출력축 + 끝판 B 입력축 (M3 2씩)')
    add('49_end_filler', to_print(tx.end_filler()), 2, '4 프레임', '끝 채움판: 끝판 A·B 왼쪽 (M3x50 2씩)')
    # 5 변속
    for g in ('12', '34', '5R'):
        add(f'50_fork_{g}', to_print(tx.fork(g), (0, 0, 0) if tx.CART_DIR[g] > 0 else flip), 1, '5 변속', f'{g} 포크 (립 면이 바닥)')
    add('50a_fork_cap', to_print(tx.fork_cap()), 3, '5 변속', '카트리지 뚜껑 (M3x8 자가탭 2)')
    add('50b_cart_washer', to_print(tx.cart_washer()), 6, '5 변속', '카트리지 와셔')
    add('51_lug', to_print(tx.lug('34')), 3, '5 변속', '세 레일 공통 (자석 1, M3x30 2)')
    add('52_selector_cage', to_print(tx.cage()), 1, '5 변속', '플랜지 바닥')
    add('53_pivot_lower', to_print(tx.pivot_half(False), (90, 0, 0)), 1, '5 변속', '')
    add('54_pivot_upper', to_print(tx.pivot_half(True), (-90, 0, 0)), 1, '5 변속', '')
    add('55_ball_half', to_print(tx.ball_half(True), (90, 0, 0)), 2, '5 변속', '평면 바닥')
    add('56_carrier_lockplate', to_print(tx.carrier(), (-90, 0, 0)), 1, '5 변속', '브리지 바닥')
    add('57_lower_lever_finger', to_print(tx.lower_lever(), (-90, 0, 0)), 1, '5 변속', '핑거 바닥 (레버봉 접착)')
    add('58_spring_spacer', to_print(tx.spring_spacer()[0], (-90, 0, 0)), 1, '5 변속', '')
    add('59_lock_collar', to_print(tx.lock_collar(), (90, 0, 0)), 1, '5 변속', '구면이 위')
    add('60_gate', to_print(tx.gate(), (-90, 0, 0)), 1, '5 변속', '후진 턱 위로 (두께 8)')
    add('61_knob', to_print(tx.knob(), (90, 0, 0)), 1, '5 변속', '')
    # 6 클러치
    add('70_cl_front', to_print(tx.cl_front()), 1, '6 클러치', '앞판(플라이휠): 모터 쪽 면이 바닥')
    add('71_cl_back', to_print(tx.cl_back(), flip), 1, '6 클러치', '뒷판: 끝판 쪽 면(너트 홈)이 바닥')
    add('72_cl_pressure', to_print(tx.cl_pressure()), 1, '6 클러치', '압력판: 스프링 자리 면이 바닥')
    add('73_cl_standoff', to_print(tx.cl_standoff()), 3, '6 클러치', '기둥 (M4x60)')
    add('74_cl_disc_hub', to_print(tx.cl_disc_hub(), flip), 1, '6 클러치', '디스크 허브: 플랜지가 바닥 (강철 와셔 에폭시)')
    add('75_cl_ring', to_print(tx.cl_ring()), 1, '6 클러치', '릴리스 링: 판이 바닥 (누름 볼트 M5x20 3)')
    add('76_cl_carrier', to_print(tx.cl_carrier(), flip), 1, '6 클러치', '릴리스 캐리어: 턱 면이 바닥 (6003)')
    add('77_cl_fork', to_print(tx.cl_fork(), flip), 1, '6 클러치', '클러치 포크: 끝판 쪽 면이 바닥 (피벗 M5x35)')
    add('78_cl_fork_bracket', to_print(tx.cl_fork_bracket(), flip), 1, '6 클러치', '끝판 A 에 붙는 면이 바닥')
    add('79_cl_spring_cup', to_print(tx.cl_spring_cup()), 3, '6 클러치', '스프링 컵')
    add('79b_cl_end_spacer', to_print(tx.cl_end_spacer()), 1, '6 클러치', '파일럿 베어링 끝 와셔 (두께 1)')
    # 7 페달
    add('80_pedal_arm', to_print(tx.pedal_arm()), 2, '7 페달', '클러치·브레이크 공용 (옆면 바닥)')
    add('81_pedal_pad', to_print(tx.pedal_pad()), 2, '7 페달', '발판 (M4x16 2)')
    add('82_pedal_base', to_print(tx.pedal_base(), (90, 0, 0)), 2, '7 페달', '바닥판이 바닥')
    return L

def parts_meta():
    return [(n, None, q, c, note) for n, m, q, c, note in parts()]

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.startswith('03_'): continue   # v3에서 출력·확인 끝난 파일 (생성 코드 없음)
        os.remove(os.path.join(OUT, f))
    for n, m, q, cat, note in parts():
        save(m, n)
        b = m.bounding_box()
        size = (b[3] - b[0], b[4] - b[1], b[5] - b[2])
        flag = '' if max(size[0], size[1]) <= 223 and size[2] <= 205 else '  <-- 출력 공간 초과!'
        print(n, q, [round(v, 1) for v in size], flag, flush=True)
    print('03 시험 캡: v3 파일 그대로 둠')
