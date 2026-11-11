from data import *
mid = lambda lo, hi: [(a + b) / 2 for a, b in zip(lo, hi)]
print('== 실험 1 유동 시간')
for k, v in FLOW.items(): print(f"{OILS[k]:14s} {v}  상온→100℃ 감소 {100*(v[0]-v[-1])/v[0]:.0f}%  ({v[0]/v[-1]:.1f}배)")
for i, t in enumerate(FLOW_T): print(f"  {t}℃: G-EP/ATF = {FLOW['GEP'][i]/FLOW['ATF'][i]:.2f}, TOP/ATF = {FLOW['TOP'][i]/FLOW['ATF'][i]:.2f}, 최대-최소 = {max(v[i] for v in FLOW.values())-min(v[i] for v in FLOW.values())} s")
for name, D in (('실험 2 상온', ROOM), ('실험 3 50℃ 시작', HOT)):
    print('==', name)
    for k, (t, T, lo, hi) in D.items():
        m = mid(lo, hi); w = [b - a for a, b in zip(lo, hi)]
        s = f"{OILS[k]:14s} 중간값 평균 {sum(m)/len(m):6.1f} (처음 {m[0]:.1f} → 끝 {m[-1]:.1f}), 전체 범위 {min(lo)}~{max(hi)}, 평균 변동폭 {sum(w)/len(w):.1f}"
        if T: s += f", 온도 {T[0]}→{T[-1]} (변화 {T[-1]-T[0]:+.1f}, 최고 {max(T)}), 첫 3분 변화 {T[1]-T[0]:+.1f}"
        print(s)
