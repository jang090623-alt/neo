"""설명서 HTML 조립 → manual.html (그림은 img/). PDF 는 make_pdf.js"""
import os, sys, json, collections, html
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import tx
S = json.load(open(os.path.join(HERE, 'steps.json')))
PL = json.load(open(os.path.join(HERE, 'plates.json')))
E = html.escape

def icon(k): return 'img/icon_' + k.replace(':', '_').replace('/', '_') + '.png'

CSS = """
@page { size: A4 landscape; margin: 0 }
* { box-sizing: border-box }
body { margin: 0; font-family: 'Noto Sans CJK KR', 'Noto Sans KR', sans-serif; color: #1f2328; }
.pg { width: 297mm; height: 210mm; position: relative; overflow: hidden; background: #f7f5f0; page-break-after: always; }
.num { position: absolute; left: 12mm; top: 7mm; font-size: 30pt; font-weight: 800; letter-spacing: -1px }
.rep { position: absolute; left: 31mm; top: 10mm; background: #d8342b; color: #fff; font-weight: 800; font-size: 15pt; padding: 1mm 3mm; border-radius: 2mm }
.sec { position: absolute; right: 12mm; top: 9mm; font-size: 9pt; color: #6b7280 }
.bar { position: absolute; right: 12mm; top: 15mm; width: 60mm; height: 1.2mm; background: #e5e1d8; border-radius: 1mm }
.bar i { display: block; height: 100%; background: #f39a2b; border-radius: 1mm }
.call { position: absolute; left: 12mm; top: 24mm; background: #fff; border: 0.6mm solid #2f6fb7; border-radius: 2.5mm; padding: 2mm; display: grid; grid-template-columns: repeat(2, 27mm); gap: 1.5mm; z-index: 3 }
.call.c1 { grid-template-columns: 27mm }
.it { text-align: center; font-size: 6.5pt; line-height: 1.15 }
.it img { width: 21mm; height: 21mm; object-fit: contain; display: block; margin: 0 auto }
.it b { display: block; font-size: 10pt }
.main { position: absolute; left: 70mm; right: 8mm; top: 18mm; bottom: 30mm; display: flex; align-items: center; justify-content: center }
.main img { max-width: 100%; max-height: 100%; -webkit-mask-image: linear-gradient(to right, transparent 0, #000 5%, #000 95%, transparent 100%), linear-gradient(to bottom, transparent 0, #000 5%, #000 95%, transparent 100%); -webkit-mask-composite: source-in; mask-composite: intersect; }
.inset { position: absolute; right: 12mm; bottom: 32mm; width: 62mm; height: 62mm; border-radius: 50%; border: 0.8mm solid #2f6fb7; overflow: hidden; background: #fff; z-index: 3 }
.inset img { width: 100%; height: 100% }
.inset span { position: absolute; left: 0; right: 0; bottom: 3mm; text-align: center; font-size: 7pt; color: #2f6fb7; font-weight: 700 }
.txt { position: absolute; left: 12mm; right: 12mm; bottom: 8mm; background: #fff; border-left: 2mm solid #f39a2b; border-radius: 1.5mm; padding: 2.5mm 4mm; font-size: 12pt; font-weight: 700 }
.note { font-size: 9.5pt; font-weight: 500; color: #9a3412; margin-top: 1mm }
.tip { font-size: 9.5pt; font-weight: 500; color: #1d4ed8; margin-top: 1mm }
.note:before { content: '⚠ '; } .tip:before { content: '💡 '; }
h1 { font-size: 30pt; margin: 0 0 3mm } h2 { font-size: 17pt; margin: 0 0 3mm; border-bottom: 0.6mm solid #f39a2b; padding-bottom: 1.5mm }
.pad { position: absolute; inset: 12mm 14mm }
table { border-collapse: collapse; font-size: 9pt; width: 100% } td, th { border-bottom: 0.3mm solid #ddd8cc; padding: 1.1mm 2mm; text-align: left; vertical-align: top } th { background: #ede9df }
.legend span { display: inline-block; width: 4mm; height: 4mm; border-radius: 1mm; vertical-align: -0.6mm; margin: 0 1.5mm 0 4mm }
.rules li { margin-bottom: 2.2mm; font-size: 11pt } .rules b { color: #b42318 }
.cols { display: flex; gap: 8mm } .cols > div { flex: 1 }
.small { font-size: 8.5pt; color: #555 }
"""

def step_page(s, total):
    rep = f'<div class="rep">{E(s["rep"])}</div>' if s['rep'] else ''
    items = ''.join(f'<div class="it"><img src="{icon(ic)}"><b>{"×" + str(q) if q else ""}</b>{E(lab)}</div>' for lab, q, ic in s['call'])
    cls = 'call c1' if len(s['call']) <= 2 else 'call'
    call = f'<div class="{cls}">{items}</div>' if s['call'] else ''
    inset = f'<div class="inset"><img src="img/inset{s["n"]:02d}.png"><span>확대</span></div>' if s['inset'] else ''
    note = f'<div class="note">{E(s["note"])}</div>' if s['note'] else ''
    tip = f'<div class="tip">{E(s["tip"])}</div>' if s.get('tip') else ''
    pct = round(100 * s['n'] / total)
    return f"""<div class="pg"><div class="num">{s['n']}</div>{rep}<div class="sec">{E(s['sec'])}</div><div class="bar"><i style="width:{pct}%"></i></div>
{call}<div class="main"><img src="img/step{s['n']:02d}.png"></div>{inset}<div class="txt">{E(s['text'])}{note}{tip}</div></div>"""

def cover():
    return f"""<div class="pg"><div class="pad" style="display:flex;gap:6mm">
<div style="width:105mm"><h1>RPM 5단 수동변속기</h1><div style="font-size:15pt;font-weight:700;margin-bottom:6mm">조립 그림 설명서<br>기어박스 + 클러치 + 손 크랭크 + 페달</div>
<p style="font-size:10.5pt;line-height:1.6">그림 한 장에 한 가지씩 순서대로 조립합니다.<br>부품 번호는 출력 파일 이름의 번호입니다.<br>수치는 모두 설계 코드(build/src/tx.py)에서 그대로 가져왔습니다.</p>
<div class="legend" style="font-size:9.5pt;margin-top:8mm;line-height:2.2">
<div><span style="background:#f39a2b;margin-left:0"></span>이번에 붙이는 출력 부품</div><div><span style="background:#4f86c6;margin-left:0"></span>이번에 붙이는 쇠 부품</div>
<div><span style="background:#d9dce1;margin-left:0"></span>이미 붙인 부품</div><div><span style="background:#d8342b;margin-left:0"></span>×6 = 같은 것을 6번 / 빨간 화살표 = 끼우는 방향</div></div>
<p class="small" style="margin-top:10mm">2026-11 · 기어박스 17판은 출력 완료 (11/17 파일) · 클러치·크랭크·페달은 18~21판</p></div>
<div style="flex:1;display:flex;align-items:center"><img src="img/hero.png" style="width:100%"></div></div></div>"""

def rules():
    return """<div class="pg"><div class="pad"><h2>시작 전에 꼭</h2><div class="cols"><div><ol class="rules">
<li><b>핀·너트는 인두로 데워서</b> 넣습니다. 망치로 치면 구멍 바닥이 뚫려 핀이 짧아집니다. 바닥에 닿으면 멈추면 됩니다.</li>
<li><b>베어링은 바이스로</b> 바깥 링을 고르게 눌러 넣습니다.</li>
<li><b>에폭시는 정해진 곳만</b>: 입력 기어 6 · 허브 3 (축에) · 아이들러 축 · 고무 호스 (핀에) · 핑거·손잡이 (레버봉에) · 클러치 허브 (축에) · 강철 와셔 (허브에) · 크랭크 손잡이 축. 베어링·출력 기어·슬리브에는 묻히지 않습니다.</li>
<li><b>그리스는 톱니·허브·레일만</b> 얇게 (PTFE). 베어링은 이미 그리스가 들어 있습니다.</li>
<li><b>클러치 조절나사는 M5×10</b>을 끝까지. M5×12 이상은 쓰지 않습니다 (기어가 버티는 힘을 넘음).</li>
<li>입력축은 <b>435mm 그대로</b> 씁니다. 끝판 A 바깥으로 102mm가 클러치·크랭크 자리입니다.</li></ol></div>
<div><table><tr><th>공구·재료</th><th>쓰는 곳</th></tr>
<tr><td>인두 (200~220℃)</td><td>평행핀 30개, 끝판 A M4 너트 4개</td></tr>
<tr><td>바이스 또는 C클램프 + 평평한 판</td><td>베어링 20개 압입</td></tr>
<tr><td>육각렌치 2.5 · 3 · 4 mm</td><td>M3 · M4 · M5 볼트</td></tr>
<tr><td>자 또는 버니어캘리퍼스</td><td>핀 나온 길이, 축 돌출, 스프링 길이</td></tr>
<tr><td>칼 · 줄 · 사포 240</td><td>서포트 자국, 슬리브 포켓 다듬기</td></tr>
<tr><td>2액형 에폭시 · 순간접착제</td><td>위 3번 자리 / 코르크 링</td></tr>
<tr><td>PTFE 그리스</td><td>마지막 시운전 전</td></tr>
<tr><td>11cm 받침 (책 등)</td><td>4장: 끝판 A를 세워 쌓을 때</td></tr></table>
<p class="small" style="margin-top:4mm">핀 나온 길이는 5~7mm면 됩니다. 걸리는 깊이 = 나온 길이 − 1mm. 짧은 핀 단은 시운전 때 세게 돌려 변속이 빠지지 않는지 확인합니다.</p></div></div></div></div>"""

def plates_page():
    rows = ''.join(f"<tr><td>{p['no']}</td><td>{E(p['file'])}</td><td>{E(p['parts'])}</td><td>{E(p['set'])}</td><td>{E(p['time'])}</td><td>{E(p['state'])}</td></tr>" for p in PL)
    return f"""<div class="pg"><div class="pad"><h2>출력 판 목록</h2>
<p class="small">Cura 프로파일 Normal #5 (층 0.28, 벽 1.6, 위·아래 1.0, 채움 Lines) · 베드 75℃ · 노즐 210℃ · 브림 8mm · 팬 3mm부터 50%. 18~21판 시간·무게는 PrusaSlicer 같은 설정 추정 (기존 판으로 Cura와 5% 안에서 일치 확인).</p>
<table><tr><th>번호</th><th>파일</th><th>부품</th><th>설정</th><th>시간 · 무게</th><th>상태</th></tr>{rows}</table></div></div>"""

def parts_page():
    c = collections.OrderedDict()
    for s in S:
        rep = int(s['rep'][1:]) if s['rep'] else 1
        for lab, q, ic in s['call']:
            if ic.startswith('stl:') or q == 0: continue
            key = ic
            if key not in c: c[key] = [lab, 0, []]
            c[key][1] += q * rep
            c[key][2].append(s['n'])
    items = sorted(c.items(), key=lambda kv: kv[1][0])
    half = (len(items) + 1) // 2
    def tbl(part):
        return '<table><tr><th></th><th>구매 부품</th><th>개수</th><th>단계</th></tr>' + ''.join(
            f'<tr><td><img src="{icon(k)}" style="width:9mm;height:9mm;object-fit:contain"></td><td>{E(v[0])}</td><td><b>{v[1]}</b></td><td class="small">{", ".join(map(str, sorted(set(v[2]))))}</td></tr>' for k, v in part) + '</table>'
    return f"""<div class="pg"><div class="pad"><h2>구매 부품 (설명서 단계에서 자동으로 센 개수)</h2>
<div class="cols"><div>{tbl(items[:half])}</div><div>{tbl(items[half:])}</div></div>
<p class="small">M3×10은 레일 칼라 6 + 케이블 1 = 7개가 필요합니다. 구매목록(bom.py)에는 1개만 있어서, 모자라면 더 사야 합니다 (보유 개수 미확인).</p></div></div>"""

def end_page():
    return f"""<div class="pg"><div class="pad" style="display:flex;gap:6mm"><div style="width:110mm"><h2>완성 · 사용법</h2><ol class="rules">
<li>페달을 뗀 채 크랭크를 천천히 돌리면 기어가 돕니다.</li>
<li>변속: 페달을 끝까지 밟음 → 레버를 중립 → 원하는 단 → 페달을 천천히 뗌.</li>
<li>레버가 안 들어가면 크랭크를 아주 살짝 돌려 핀과 포켓을 맞춥니다.</li>
<li>후진(R)은 레버를 눌러야 들어갑니다 (잠금).</li>
<li>클러치가 손으로 쉽게 미끄러지면 정상입니다 (약 {0.58:.2f} N·m에서 미끄러지게 설정 = 기어 보호).</li></ol>
<p class="note" style="font-size:10pt">돌리는 중에는 클러치와 기어 사이에 손가락을 넣지 않습니다.</p></div>
<div style="flex:1;display:flex;flex-direction:column;gap:3mm;justify-content:center"><img src="img/heroB.png" style="width:100%"><img src="img/hero_pedal.png" style="width:55%;align-self:center"></div></div></div>"""

pages = [cover(), rules(), plates_page(), parts_page()] + [step_page(s, len(S)) for s in S if s['sec'] != '완성'] + [end_page()]
open(os.path.join(HERE, 'manual.html'), 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(pages)}</body></html>')
print(len(pages), 'pages')
