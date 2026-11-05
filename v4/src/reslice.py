"""바뀐 STL 만 다시 슬라이스하고 slice_result.json 갱신 (사용: python3 reslice.py [--parse-only] 파일명...)"""
import sys, json, os, re, subprocess
from concurrent.futures import ThreadPoolExecutor
from slice import slice_one, STL, GC

def parse(fn):
    out = os.path.join(GC, fn.replace('.stl', '.gcode'))
    txt = subprocess.run(['grep', '-E', 'estimated printing time \\(normal|filament used \\[g\\]', out], capture_output=True, text=True).stdout
    t = re.search(r'estimated printing time \(normal mode\) = (.+)', txt).group(1).strip()
    g = float(re.search(r'filament used \[g\] = ([\d.]+)', txt).group(1))
    secs = sum(int(n) * {'d': 86400, 'h': 3600, 'm': 60, 's': 1}[u] for n, u in re.findall(r'(\d+)([dhms])', t))
    return [fn, secs, g, '']

args = [a for a in sys.argv[1:] if not a.startswith('--')]
names = [n if n.endswith('.stl') else n + '.stl' for n in args]
if '--parse-only' in sys.argv:
    new = {n: parse(n) for n in names}
else:
    with ThreadPoolExecutor(4) as ex:
        new = {r[0]: list(r) for r in ex.map(slice_one, names)}
old = [list(r) for r in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'slice_result.json')))]
have = set(os.listdir(STL))
res = [new.get(r[0], r) for r in old if r[0] in have] + [r for n, r in new.items() if n not in {o[0] for o in old}]
json.dump(sorted(res), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'slice_result.json'), 'w'), ensure_ascii=False)
for n in names: print(new[n])
