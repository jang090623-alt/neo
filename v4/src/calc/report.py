"""calc_result.json → 계산서 마크다운 (calc_report.md)"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # src/
R = json.load(open(os.path.join(ROOT, 'calc', 'calc_result.json')))

def table(rows, cols=None):
    cols = cols or list(rows[0].keys())
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for r in rows:
        out.append('| ' + ' | '.join(str(r.get(c, '')) for c in cols) + ' |')
    return '\n'.join(out)

def kv(d):
    return table([{'항목': k, '값': v} for k, v in d.items() if not isinstance(v, (list, dict))])

L = []
L.append('# 계산서 v4 (자동 생성: calc/calc.py → calc/report.py)\n')
L.append('단위: N, mm, MPa, N·m. **SF** = 안전율(허용 ÷ 실제). 정적 SF 는 출력 PLA 인장강도(XY 45.5 MPa, Z 33.1 MPa), '
         '피로 SF 는 Ezeh & Susmel 설계 곡선(생존확률 95%: 200만 회 = 인장강도의 10%, k=5.5)과 비교했습니다.\n')
L.append('## 0. 가정 (측정해서 바꿔야 할 값)\n')
L.append('\n'.join(f'- {v}' for v in R['assume'].values()) + '\n')
L.append('## 1. 속도 (12V, 감속기 1:9, 무부하 가정)\n')
L.append(table([{'단': k, '출력 rpm': v} for k, v in R['speeds_rpm'].items()]) + '\n')
L.append('## 2. 회전관성 (CAD 부피 x PLA 밀도 1.24, 속 100% = 위쪽 한계)\n')
L.append(kv(R['inertia_kgm2']) + '\n')
L.append('## 3. 필요한 토크와 클러치\n')
L.append(kv(R['torque_need_Nm']) + '\n')
L.append('### 3-1. 조절나사 길이별 미끄럼 토크 (끝까지 조임. 설정 = M5x10, M5x12 이상 금지)\n')
L.append(table(R['clutch']['설정표']) + '\n')
L.append(kv({k: v for k, v in R['clutch'].items() if k != '설정표'}) + '\n')
L.append('### 3-2. 발열\n')
L.append(kv(R['clutch_heat']) + '\n')
L.append('## 4. 축 (양면 D, 단순지지, 클러치 최대 토크)\n')
L.append(kv(R['shaft_section']) + '\n')
L.append(table(R['shafts']) + '\n')
L.append('클러치 쪽 내민 축 (커플링 핀 1개가 다 받는 최악):\n\n' + kv(R['shaft_overhang']) + '\n')
L.append('## 5. 기어 이뿌리 (FEM 응력계수 x 이 폭당 하중 x K_V x K_Fβ)\n')
gf = R['gear_factors']
k41 = 'FEM 응력계수 MPa/(N/mm) v4.1 랙 창성(17T +0.3, 49T -0.3 전위)'
L.append(table([{'잇수': z, 'v4.1 랙 창성(설계)': gf[k41][z], 'v4 필렛 R1.0': gf['v4 직선 뿌리 + 필렛 R1.0 (참고)'][z],
                 'v3 각진 뿌리': gf['v3 각진 뿌리 (참고)'][z],
                 'v3 대비': f"{(1 - gf[k41][z] / gf['v3 각진 뿌리 (참고)'][z]) * 100:.0f}% 낮음"}
                for z in gf[k41]]) + '\n')
L.append(f"FEM 응력계수 = 이끝(인벌류트 끝)에 법선 하중 1 N/mm 일 때 이뿌리 최대 인장응력 → 응력 = 계수 x (Ft/cos20°)/이폭 x K_V x K_Fβ. "
         f"K_V {gf['K_V(Barth, 1단~5단)']} (단마다 피치원 속도), K_Fβ = ISO 6336-1 방법 C (상한 없음), N_F {gf['N_F']}, c_γ {gf['c_γ N/(mm·μm)']} N/(mm·μm)\n")
rows = []
for r in R['gears']:
    ks = [k for k in r if '응력' in k]
    rows.append({'단': r['단'], '경우': r['경우'], 'Ft N': r['Ft N'], 'K_V': r['K_V'], 'KFβ': r['KFβ'],
                 '작은 기어 MPa / 정적SF / 피로SF': ' / '.join(map(str, r[ks[0]])),
                 '큰 기어 MPa / 정적SF / 피로SF': ' / '.join(map(str, r[ks[1]])), '면압 MPa': r['면압 MPa']})
L.append(table(rows) + '\n')
L.append('## 6. 변속 충격 (강철 핀 + 고무 쿠션)\n')
L.append(kv({k: v for k, v in R['impacts'].items() if k != 'rows'}) + '\n')
L.append(table(R['impacts']['rows']) + '\n')
L.append('## 7. 허브·키·D면 (클러치 최대 토크)\n')
L.append(table(R['hubs']) + '\n')
L.append('## 8. 베어링\n')
L.append(kv(R['bearings']) + '\n')
L.append('## 9. 포크·카트리지\n')
L.append(kv(R['fork']) + '\n')
L.append('## 10. 레버·게이트 (손잡이 400N)\n')
L.append(kv(R['lever']) + '\n')
L.append('## 11. 클러치 부품\n')
L.append(kv(R['clutch_parts']) + '\n')
L.append('## 12. 전기·모터 받침·디텐트\n')
L.append(kv(R['electric']) + '\n\n' + kv(R['motor_mount']) + '\n\n' + kv(R['detent']) + '\n')
L.append('## 13. 압축 스프링 (기성품): 가장 짧을 때 길이와 전단응력\n')
L.append(f"길이는 밀착 + 1 = {R['C252_min_len']['밀착 + 1 (이보다 길어야 함)']} mm 보다 길어야 합니다. 전단응력(Wahl 보정, 하중 +10%)은 "
         "인장강도의 35% 이하여야 합니다 (오스테나이트 스텐, 셋 제거 안 한 정적 허용: Shigley 표 10-6). 밀착 줄은 참고값입니다.\n")
L.append(table(R['springs']) + '\n')
L.append('## 출처\n')
L.append('\n'.join(f'- {v}' for v in R['src'].values()) + '\n')
open(os.path.join(ROOT, 'calc', 'calc_report.md'), 'w').write('\n'.join(L))
print('written', sum(len(x) for x in L))
