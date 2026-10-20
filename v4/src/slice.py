"""PrusaSlicer 로 부품별 출력 시간·무게 추정 (Ultimaker 2+ 근사 설정)"""
import subprocess, re, os, sys, json
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(ROOT, '..', 'stl'); GC = os.path.join(ROOT, 'gcode'); os.makedirs(GC, exist_ok=True)
BASE = ['--bed-shape', '0x0,223x0,223x223,0x223', '--max-print-height', '205', '--nozzle-diameter', '0.4',
        '--filament-diameter', '2.85', '--filament-density', '1.24', '--temperature', '210', '--bed-temperature', '60',
        '--first-layer-temperature', '210', '--first-layer-bed-temperature', '60', '--gcode-flavor', 'marlin2',
        '--layer-height', '0.2', '--first-layer-height', '0.25', '--fill-pattern', 'gyroid',
        '--perimeter-speed', '40', '--external-perimeter-speed', '30', '--infill-speed', '60', '--solid-infill-speed', '40',
        '--top-solid-infill-speed', '30', '--travel-speed', '150', '--first-layer-speed', '20', '--skirts', '0',
        '--center', '111.5,111.5']
STRONG = ['--perimeters', '4', '--top-solid-layers', '5', '--bottom-solid-layers', '5', '--fill-density', '40%']
FRAME = ['--perimeters', '3', '--top-solid-layers', '4', '--bottom-solid-layers', '4', '--fill-density', '20%']
GEAR = ['--perimeters', '5', '--top-solid-layers', '5', '--bottom-solid-layers', '5', '--fill-density', '25%']
FRAME_PARTS = ('00_', '02_', '40_', '41_', '42_', '43_', '44_', '45_', '46_', '47_', '48_', '49_', '52_', '53_', '54_', '60_', '78_', '80_', '81_')
GEAR_PARTS = ('10_', '11_', '12_')

def slice_one(fn):
    prof = FRAME if fn.startswith(FRAME_PARTS) else GEAR if fn.startswith(GEAR_PARTS) else STRONG
    out = os.path.join(GC, fn.replace('.stl', '.gcode'))
    r = subprocess.run(['prusa-slicer', '--export-gcode', *BASE, *prof, '-o', out, os.path.join(STL, fn)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return fn, None, None, r.stderr[-300:]
    txt = subprocess.run(['grep', '-E', 'estimated printing time \\(normal|filament used \\[g\\]', out], capture_output=True, text=True).stdout
    t = re.search(r'estimated printing time \(normal mode\) = (.+)', txt).group(1).strip()
    g = float(re.search(r'filament used \[g\] = ([\d.]+)', txt).group(1))
    secs = sum(int(n) * {'d': 86400, 'h': 3600, 'm': 60, 's': 1}[u] for n, u in re.findall(r'(\d+)([dhms])', t))
    return fn, secs, g, ''

if __name__ == '__main__':
    files = sorted(f for f in os.listdir(STL) if f.endswith('.stl'))
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(slice_one, files))
    json.dump(res, open(os.path.join(ROOT, 'slice_result.json'), 'w'), ensure_ascii=False)
    for r in res: print(r)
