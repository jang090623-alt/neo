import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from data import *
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family': fm.FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name(), 'font.size': 12,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#dddddd', 'grid.linewidth': 0.8,
    'axes.unicode_minus': False, 'savefig.dpi': 200, 'figure.figsize': (8, 4.8)})
MK = {'ATF': 'o', 'TOP': 's', 'RAC': '^', 'GEP': 'D', 'GRS': 'v'}
mid = lambda lo, hi: [(a + b) / 2 for a, b in zip(lo, hi)]

def finish(ax, xl, yl, name, legend_kw=None):
    ax.set_xlabel(xl); ax.set_ylabel(yl); ax.legend(frameon=False, **(legend_kw or {}))
    plt.tight_layout(); plt.savefig(f'figs/{name}.png'); plt.close()

# 그림 3: 온도-유동 시간
fig, ax = plt.subplots()
for k, v in FLOW.items(): ax.plot(FLOW_T, v, marker=MK[k], color=COLOR[k], lw=2, ms=7, label=OILS[k])
for k, v in FLOW.items(): ax.annotate(f'{v[0]}', (FLOW_T[0], v[0]), textcoords='offset points', xytext=(-8, 4), ha='right', color=COLOR[k], fontsize=10)
ax.set_xticks(FLOW_T); ax.set_xticklabels(['20.1', '30', '50', '100']); ax.set_ylim(0, 270)
finish(ax, '기름 온도 (℃)', '유동 시간 (초)', 'fig3_flow_time')

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
    if k in ('GEP', 'ATF'): ax.annotate(f'{T[-1]}℃', (t[-1], T[-1]), textcoords='offset points', xytext=(6, 4 if k == 'GEP' else -12), color=COLOR[k], fontsize=10)
ax.set_xticks(range(0, 16, 3)); ax.set_xlim(-0.5, 17); ax.set_ylim(20, 52)
finish(ax, '구동 시간 (분)', '오일 온도 (℃)', 'fig5_hot_temp')
print('ok')
