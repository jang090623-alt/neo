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
R['stl_bad'] = [f for f in sorted(os.listdir(STL)) if not trimesh.load(os.path.join(STL, f)).is_watertight]
R['stl_count'] = len(os.listdir(STL))
json.dump(R, open(os.path.join(ROOT, 'verify_result.json'), 'w'), ensure_ascii=False, indent=1, default=str)
print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
