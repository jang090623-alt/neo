import json, base64, numpy as np, fast_simplification, asm, tx
_gp = tx.gear_poly                                   # 뷰어용: 이 모양을 거칠게 (용량 줄이기, 출력 STL 과 무관)
tx.gear_poly = lambda z, *a, **k: _gp(z, steps=240).simplify(0.02)
P = asm.assemble('N', carrier_side=1)
def cat(n):
    if n.startswith(('gin_', 'gout_', 'g_idler')): return 'gear', None
    for g in tx.RAIL_X:
        if n == f'slv_{g}': return 'sleeve', g
        if n in (f'rail_{g}', f'fork_{g}', f'lug_{g}', f'fcap_{g}', f'fspring_{g}', f'fwash_a_{g}', f'fwash_b_{g}', f'rcol_a_{g}', f'rcol_b_{g}'):
            return 'shift', g
    if n in ('ball', 'lower_lever', 'rod', 'spring_spacer', 'lock_collar', 'knob'): return 'lever', 'lever'
    if n == 'carrier': return 'shift', 'carrier'
    if n.startswith(('hood', 'acr_')): return 'guard', None
    if n.startswith(('plate_', 'wheel', 'cap_', 'filler_', 'foot_', 'm_riser')): return 'frame', None
    if n in ('cage', 'gate', 'pivot_lo', 'pivot_hi'): return 'cage', None
    if n.startswith(('cl_', 'cpl_')): return 'clutch', None
    if n.startswith('m_'): return 'motor', None
    if n.startswith('hub'): return 'sleeve', None
    return 'shaft', None
out = []; tris = 0
for n, m in P.items():
    mesh = m.to_mesh(); v = np.array(mesh.vert_properties)[:, :3].astype(np.float32); f = np.array(mesh.tri_verts).astype(np.int32)
    if len(f) > 1500:
        v, f = fast_simplification.simplify(v, f, target_reduction=0.8 if n.startswith(('gin', 'gout', 'g_', 'slv')) else 0.6)
    v = v.astype(np.float32); f = f.astype(np.uint16 if len(v) < 65535 else np.uint32)
    c, g = cat(n); tris += len(f)
    out.append({'n': n, 'c': c, 'g': g, 'v': base64.b64encode(v.tobytes()).decode(), 'f': base64.b64encode(f.tobytes()).decode(), 'i32': f.dtype == np.uint32})
consts = {'C': tx.C, 'H': tx.H, 'L1': tx.L1, 'PIVOT': list(map(float, tx.PIVOT)), 'TRAVEL': tx.TRAVEL, 'PUSH': tx.REV_PUSH,
          'RAIL_X': tx.RAIL_X, 'WIN': tx.WIN, 'FH': tx.FINGER_HALF, 'FINGER_YC': tx.FINGER_YC}
data = json.dumps({'parts': out, 'k': consts})
open('viewer_data.js', 'w').write('window.TXDATA=' + data + ';')
print(len(out), 'parts', tris, 'tris', round(len(data) / 1e6, 2), 'MB')
