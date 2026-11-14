import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from data import *
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family': fm.FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name(), 'font.size': 12,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#dddddd', 'grid.linewidth': 0.8,
    'axes.unicode_minus': False, 'savefig.dpi': 200, 'figure.figsize': (8, 4.8)})
MK = {'JET': 'P', 'ATF': 'o', 'TOP': 's', 'RAC': '^', 'GEP': 'D', 'GRS': 'v'}
mid = lambda lo, hi: [(a + b) / 2 for a, b in zip(lo, hi)]

def finish(ax, xl, yl, name, legend_kw=None):
    ax.set_xlabel(xl); ax.set_ylabel(yl); ax.legend(frameon=False, **(legend_kw or {}))
    plt.tight_layout(); plt.savefig(f'figs/{name}_v3.png'); plt.close()

# 그림 3: 온도-유동 시간
fig, ax = plt.subplots()
for k, v in FLOW.items(): ax.errorbar(FLOW_T, v, yerr=FLOW_SD[k], marker=MK[k], color=COLOR[k], lw=2, ms=7, capsize=4, label=OILS[k] + ('' if FLOW_SD[k] else ' (1회)'))
for k, v in FLOW.items():
    if k in ('GEP', 'TOP'): ax.annotate(f'{v[0]:.0f}', (FLOW_T[0], v[0]), textcoords='offset points', xytext=(-8, 4), ha='right', color=COLOR[k], fontsize=10)
ax.set_xticks(FLOW_T); ax.set_xticklabels(['20.1', '30', '50', '100']); ax.set_ylim(0, 270)
finish(ax, '기름 온도 (℃)', '유동 시간 (초)\n점: 평균, 막대: 표준편차', 'fig3_flow_time')

def rpm_plot(D, name, ylim):
    fig, ax = plt.subplots()
    for k, (t, T, lo, hi) in D.items():
        ax.fill_between(t, lo, hi, color=COLOR[k], alpha=0.18, lw=0)
        ax.plot(t, mid(lo, hi), marker=MK[k], color=COLOR[k], lw=2, ms=6, label=OILS[k])
    ax.set_xticks(range(0, 16, 3)); ax.set_ylim(*ylim)
    finish(ax, '구동 시간 (분)', '입력축 회전수 (RPM)\n선: 최소·최대의 중간값, 띠: 최소~최대', name, {'ncol': 3, 'loc': 'lower center', 'fontsize': 10})
rpm_plot(ROOM, 'fig4_room_rpm', (164, 184))
rpm_plot(HOT, 'fig6_hot_rpm', (164, 184))

# 그림 5: 50℃ 시작 온도 변화
fig, ax = plt.subplots()
for k, (t, T, lo, hi) in HOT.items(): ax.plot(t, T, marker=MK[k], color=COLOR[k], lw=2, ms=7, label=OILS[k])
for k, (t, T, lo, hi) in HOT.items():
    if k in ('GEP', 'JET'): ax.annotate(f'{T[-1]}℃', (t[-1], T[-1]), textcoords='offset points', xytext=(6, 4 if k == 'GEP' else -14), color=COLOR[k], fontsize=10)
ax.set_xticks(range(0, 16, 3)); ax.set_xlim(-0.5, 17); ax.set_ylim(20, 52)
finish(ax, '구동 시간 (분)', '오일 온도 (℃)', 'fig5_hot_temp')
# 그림 7: 효율(막대 + 전류 분해능에 따른 범위)과 40℃ 동점도-회전수
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.4))
ks = sorted(EFF, key=lambda k: -eff(k)); e = [eff(k) for k in ks]
a1.bar(range(len(ks)), e, color=[COLOR[k] for k in ks], width=0.62,
       yerr=[[eff(k) - eff(k, DI) for k in ks], [eff(k, -DI) - eff(k) for k in ks]], capsize=4, ecolor='#333333')
for i, k in enumerate(ks): a1.text(i, eff(k, -DI) + 0.08, f'{eff(k):.1f}', ha='center', va='bottom', fontsize=10)
a1.set_xticks(range(len(ks))); a1.set_xticklabels(['\n'.join(OILS[k].rsplit(' ', 1)) for k in ks], fontsize=9)
a1.set_ylim(0, 7); a1.set_ylabel('효율 (%)'); a1.grid(axis='x', visible=False)
for k, v in VISC40.items():
    t, T, lo, hi = ROOM[k]; mm = mid(lo, hi); avg = sum(mm) / len(mm)
    a2.errorbar(v, avg, yerr=[[avg - min(lo)], [max(hi) - avg]], fmt=MK[k], color=COLOR[k], ms=8, capsize=4, label=OILS[k])
a2.set_xlim(0, 130); a2.set_ylim(164, 184); a2.set_xlabel('40℃ 동점도 (mm²/s, 제조사 자료)'); a2.set_ylabel('상온 회전수 평균 (RPM)\n막대: 최소~최대')
a2.legend(frameon=False, fontsize=9, loc='lower left')
plt.tight_layout(); plt.savefig('figs/fig7_efficiency.png'); plt.close()
print('ok')
