import json, os, export
ROOT = os.path.dirname(os.path.abspath(__file__))
res = {r[0][:-4]: (r[1], r[2]) for r in json.load(open(os.path.join(ROOT, 'slice_result.json')))}
rows = []
for n, m, q, cat, note in export.parts_meta():
    s, g = res[n]; rows.append((n, q, cat, note, s, g))
if __name__ == '__main__':
    cats = {}
    for n, q, cat, note, s, g in rows:
        cats.setdefault(cat, [0, 0, 0]); cats[cat][0] += s * q; cats[cat][1] += g * q; cats[cat][2] += q
    T = sum(s * q for *_, s, g in [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows] for q in [1]) 
    T = sum(r[4] * r[1] for r in rows); G = sum(r[5] * r[1] for r in rows)
    for c in sorted(cats): print(c, cats[c][2], '개', round(cats[c][0] / 3600, 1), 'h', round(cats[c][1]), 'g')
    print('TOTAL', sum(r[1] for r in rows), '개', round(T / 3600, 1), 'h', round(G), 'g')
