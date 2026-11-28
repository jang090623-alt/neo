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
<div style="width:105mm"><h1>RPM 5단 수동변속기</h1><div style="font-size:15pt;font-weight:700;margin-bottom:6mm">조립 그림 설명서<br>기어박스 + 클러치 + 페달 + GGM 모터 + 아두이노</div>
<p style="font-size:10.5pt;line-height:1.6">그림 한 장에 한 가지씩 순서대로 조립합니다.<br>부품 번호는 출력 파일 이름의 번호입니다.<br>수치는 모두 설계 코드(build/src/tx.py)에서 그대로 가져왔습니다.</p>
<div class="legend" style="font-size:9.5pt;margin-top:8mm;line-height:2.2">
<div><span style="background:#f39a2b;margin-left:0"></span>이번에 붙이는 출력 부품</div><div><span style="background:#4f86c6;margin-left:0"></span>이번에 붙이는 쇠 부품</div>
<div><span style="background:#d9dce1;margin-left:0"></span>이미 붙인 부품</div><div><span style="background:#d8342b;margin-left:0"></span>×6 = 같은 것을 6번 / 빨간 화살표 = 끼우는 방향</div></div>
<p class="small" style="margin-top:10mm">2026-11 · 기어박스 17판은 11/17 파일 · 클러치·페달·모터 받침·센서 부품은 18~23판</p></div>
<div style="flex:1;display:flex;align-items:center;justify-content:center"><img src="img/hero.png" style="max-width:100%;max-height:180mm"></div></div></div>"""

def rules():
    return """<div class="pg"><div class="pad"><h2>시작 전에 꼭</h2><div class="cols"><div><ol class="rules">
<li><b>핀·너트는 인두로 데워서</b> 넣습니다. 망치로 치면 구멍 바닥이 뚫려 핀이 짧아집니다. 바닥에 닿으면 멈추면 됩니다.</li>
<li><b>베어링은 바이스로</b> 바깥 링을 고르게 눌러 넣습니다.</li>
<li><b>에폭시는 정해진 곳만</b>: 입력 기어 6 · 허브 3 (축에) · 아이들러 축 · 고무 호스 (핀에) · 핑거·손잡이 (레버봉에) · 클러치 육각 슬리브 (축에) · 강철 와셔 (클러치 허브에). <b>클러치 허브 자체는 축에 붙이지 않습니다</b> (미끄러져야 클러치가 끊김). 베어링·출력 기어·슬리브에는 묻히지 않습니다.</li>
<li><b>그리스는 톱니·허브·레일만</b> 얇게 (PTFE). 베어링은 이미 그리스가 들어 있습니다.</li>
<li><b>클러치 조절나사는 M5×10</b>을 끝까지. M5×12를 와셔 없이 쓰지 않습니다 (기어가 버티는 힘을 넘음).</li>
<li><b>출력 덮개는 없지만, 학교 재료(아크릴·합판 등)로 클러치와 기어 위를 덮는 것을 권장합니다.</b> 다른 사람이 조작하므로 그 덮개에 덮개 스위치를 달고, 비상정지 버튼을 손 닿는 곳에 둡니다.</li>
<li>입력축은 <b>435mm 그대로</b> 씁니다. 끝판 A 바깥으로 102mm가 클러치·모터 연결 자리입니다.</li></ol></div>
<div><table><tr><th>공구·재료</th><th>쓰는 곳</th></tr>
<tr><td>인두 (200~220℃)</td><td>평행핀 30개, 끝판 A M4 너트 4개, 배선 납땜</td></tr>
<tr><td>멀티미터</td><td>가속 페달 신호 0~5V 확인, 배선 확인</td></tr>
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
<p class="small">M3×10은 레일 칼라 6 + 케이블 1 = 7개가 필요합니다. 구매목록(bom.py)에는 1개만 있습니다 (보유 개수 미확인). 모자라면 레일 칼라에 M3×12를 써도 됩니다 (32단계 참고).</p></div></div>"""

def end_page():
    return f"""<div class="pg"><div class="pad" style="display:flex;gap:6mm"><div style="width:110mm"><h2>완성 · 사용법</h2><ol class="rules">
<li>가속 페달을 뗀 채 전원을 켜고, 1단에서 클러치를 밟은 채 가속 페달을 살짝 → 클러치를 천천히 뗍니다.</li>
<li>변속: 페달을 끝까지 밟음 → 레버를 중립 → 원하는 단 → 페달을 천천히 뗌.</li>
<li>레버가 안 들어가면 클러치를 밟은 채 가속 페달을 아주 살짝 밟아 핀과 포켓을 맞춥니다.</li>
<li>후진(R)은 레버를 눌러야 들어갑니다 (잠금).</li>
<li>후진(R)은 멈춘 뒤에만 넣습니다.</li><li>클러치는 약 {0.58:.2f} N·m에서 미끄러지게 설정되어 기어를 보호합니다.</li></ol>
<p class="note" style="font-size:10pt">덮개가 없으니 모터가 도는 동안 클러치·스프로킷·기어에 손을 넣지 않습니다.</p></div>
<div style="flex:1;display:flex;gap:4mm;align-items:center;justify-content:center"><img src="img/heroB.png" style="max-width:65%;max-height:170mm"><img src="img/hero_pedal.png" style="max-width:32%;max-height:120mm"></div></div></div>"""


def fit_page():
    rows = [
      ('베어링 6001 자리', f'Ø{tx.BRG_SEAT}', '손으로는 안 들어가고 바이스로 눌러 들어가면 정상'),
      ('베어링 6003 자리 (캐리어)', f'Ø{tx.BRG3_SEAT}', '바이스로 눌러 넣기'),
      ('축 구멍 (기어·허브·스페이서)', f'Ø{tx.SHAFT_HOLE}', 'Ø12 축이 손으로 들어가야 함 (에폭시 틈). 빡빡하면 사포를 감은 봉으로'),
      ('레일 구멍', f'Ø{tx.RAIL_HOLE}', 'Ø6 레일이 걸림 없이 미끄러져야 함'),
      ('평행핀 구멍 (기어·앞판)', f'Ø{tx.PIN_HOLE}', '인두로 데워 넣기. 망치 금지'),
      ('클러치 허브 ↔ 육각 슬리브', f'맞변 {tx.HEX_AF + 2 * tx.HEX_CLR:.1f} / {tx.HEX_AF:.0f}', '손으로 앞뒤로 쉽게 미끄러져야 함. 빡빡하면 허브 육각 구멍을 줄로'),
      ('클러치 허브 목 ↔ 강철 와셔', f'Ø16.8 / 안지름 17', '와셔가 목에 끼워져 어깨에 닿아야 함'),
      ('슬리브 포켓 ↔ 고무 호스', f'{2 * (tx.CUSH_OD / 2 + tx.POCKET_CLR):.1f} / {tx.CUSH_OD:.0f}', '손가락으로 밀어 쑥 들어가야 함. 빡빡하면 포켓 둥근 벽만 사포'),
    ]
    t = ''.join(f'<tr><td>{E(a)}</td><td><b>{E(b)}</b></td><td>{E(d)}</td></tr>' for a, b, d in rows)
    return f"""<div class="pg"><div class="pad"><h2>출력 후 손질 · 맞춤 확인</h2>
<p style="font-size:10.5pt">조립 전에 부품마다 한 번씩 끼워 봅니다. 구멍 치수는 설계 값입니다 (mm).</p>
<table><tr><th>자리</th><th>설계 치수</th><th>확인</th></tr>{t}</table>
<p class="small" style="margin-top:4mm">브림은 칼로 떼고, 첫 층이 퍼진 턱(코끼리발)은 구멍 입구만 칼로 살짝 다듬습니다. 11번 판 러그 홈의 서포트는 끝까지 깨끗이 (핑거가 지나가는 길).</p></div></div>"""

def trouble_page():
    rows = [
      ('레버가 단에 안 들어감', '핀과 슬리브 포켓 위치가 안 맞음', '클러치 페달을 밟은 채 가속 페달을 아주 살짝'),
      ('달리다 변속이 저절로 빠짐', '핀이 짧음 (걸리는 길이 = 나온 길이 − 1)', '그 기어 핀을 인두로 데워 6mm까지 빼거나, 그 기어만 다시 출력'),
      ('중립인데 기어가 긁히거나 같이 돎', '핀이 7mm보다 김 → 슬리브에 닿음', '핀 나온 길이를 재서 7mm 넘는 핀을 줄로 갈기'),
      ('모터는 도는데 입력축이 안 돎', '클러치 페달을 안 밟았는데 케이블이 당겨져 있음 / 육각 슬리브 에폭시가 안 붙음', '페달을 뗀 상태로 케이블을 다시 맞춤 (팽팽하되 포크를 당기지 않게)'),
      ('페달을 밟아도 클러치가 안 끊김', '케이블이 느슨함', '페달을 뗀 채 속선을 당겨 M3×10 다시 조임'),
      ('페달을 밟아도 클러치가 덜 끊김', '허브가 슬리브 위에서 안 미끄러짐 (에폭시가 묻음)', '허브를 빼서 확인, 슬리브 바깥의 에폭시를 칼로'),
      ('클러치가 너무 쉽게 미끄러짐', f'설정 미끄럼 토크 약 {0.58:.2f} N·m', '시운전 3번으로 재기. 0.40 N·m보다 작으면 M5×12 + M5 와셔(0.5) 1장 (설계서 8장 시험 3)'),
      ('모터가 5초마다 멈춤', '출력축 rpm 펄스가 안 들어옴', '바퀴 자석·센서 틈(2.5mm)과 D7 배선 확인'),
      ('전원을 켜도 모터 허가가 안 됨', '가속 페달을 밟은 채 켬 / 비상정지 눌림 / A4 배선', '페달을 떼고 0.5초 기다림, 비상정지 풀기'),
      ('기어가 뻑뻑함', '축 끝 칼라가 끝판을 꽉 누름 / 그리스 없음', '칼라를 풀고 0.2mm쯤 틈을 둔 채 다시 조임, 톱니에 PTFE 그리스'),
      ('레일 칼라가 밀림', 'M3 덜 조임', '슬릿이 닫힐 때까지 조임'),
    ]
    t = ''.join(f'<tr><td><b>{E(a)}</b></td><td>{E(b)}</td><td>{E(d)}</td></tr>' for a, b, d in rows)
    return f"""<div class="pg"><div class="pad"><h2>문제 해결</h2><table><tr><th>증상</th><th>원인</th><th>해결</th></tr>{t}</table></div></div>"""

def wiring_page():
    svg = """<svg viewBox="0 0 1000 520" style="width:100%;height:150mm" font-family="Noto Sans CJK KR" font-size="17">
<defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#333"/></marker></defs>
<text x="10" y="28" font-weight="700" font-size="20">① 모터 전원 (굵은 선 1.5mm² 이상)</text>
<g stroke="#c0392b" stroke-width="5" fill="none"><path d="M120,90 H230 M330,90 H430 M560,90 H660 M800,90 H860"/></g>
<g font-size="16"><rect x="20" y="60" width="100" height="60" rx="8" fill="#fff" stroke="#333"/><text x="70" y="88" text-anchor="middle">12V 배터리</text><text x="70" y="108" text-anchor="middle">(+)</text>
<rect x="230" y="60" width="100" height="60" rx="8" fill="#fff4e5" stroke="#333"/><text x="280" y="88" text-anchor="middle">퓨즈 15A</text><text x="280" y="108" text-anchor="middle" font-size="13">배터리 바로 옆</text>
<rect x="430" y="60" width="130" height="60" rx="8" fill="#e8f1ff" stroke="#333"/><text x="495" y="88" text-anchor="middle">40A 릴레이</text><text x="495" y="108" text-anchor="middle" font-size="13">접점 30 → 87</text>
<rect x="660" y="60" width="140" height="60" rx="8" fill="#fff" stroke="#333"/><text x="730" y="88" text-anchor="middle">키트 모터</text><text x="730" y="108" text-anchor="middle">드라이버</text>
<rect x="860" y="60" width="110" height="60" rx="8" fill="#fff" stroke="#333"/><text x="915" y="95" text-anchor="middle">GGM 모터</text></g>
<text x="20" y="150" font-size="14" fill="#555">배터리 (−) → 드라이버 (−). 가속 페달은 키트 설명서대로 드라이버에 연결.</text>
<text x="10" y="200" font-weight="700" font-size="20">② 릴레이 코일 (가는 선) — 모두 닫혀야 모터가 돎</text>
<g stroke="#1d4ed8" stroke-width="3" fill="none"><path d="M120,260 H170 M290,260 H340 M460,260 H520 M650,260 H700 M840,260 H880"/></g><g font-size="15"><rect x="880" y="236" width="80" height="48" rx="8" fill="#fff" stroke="#333"/><text x="920" y="266" text-anchor="middle">GND</text></g>
<g font-size="15"><rect x="20" y="230" width="100" height="60" rx="8" fill="#fff" stroke="#333"/><text x="70" y="256" text-anchor="middle">12V</text><text x="70" y="276" text-anchor="middle" font-size="12">(퓨즈 뒤)</text>
<rect x="170" y="230" width="120" height="60" rx="8" fill="#ffe4e1" stroke="#333"/><text x="230" y="256" text-anchor="middle">비상정지</text><text x="230" y="276" text-anchor="middle" font-size="12">b접점(NC)</text>
<rect x="340" y="230" width="120" height="60" rx="8" fill="#f3f4f6" stroke="#333" stroke-dasharray="6 4"/><text x="400" y="256" text-anchor="middle">덮개 스위치</text><text x="400" y="276" text-anchor="middle" font-size="12">→ 전선으로 이음</text>
<rect x="520" y="230" width="130" height="60" rx="8" fill="#e8f1ff" stroke="#333"/><text x="585" y="256" text-anchor="middle">5V 릴레이 모듈</text><text x="585" y="276" text-anchor="middle" font-size="12">COM → NO</text>
<rect x="700" y="230" width="140" height="60" rx="8" fill="#e8f1ff" stroke="#333"/><text x="770" y="256" text-anchor="middle">40A 릴레이 코일</text><text x="770" y="276" text-anchor="middle" font-size="12">85 → 86 → GND</text></g>
<g font-size="14"><circle cx="490" cy="260" r="6" fill="#1d4ed8"/><path d="M490,260 V400" stroke="#1d4ed8" stroke-width="2"/>
<rect x="430" y="400" width="120" height="44" rx="6" fill="#fff" stroke="#333"/><text x="490" y="427" text-anchor="middle">감지점</text>
<text x="565" y="415">10kΩ → 아두이노 A4, A4 → 4.7kΩ → GND (약 3.8V)</text>
<text x="640" y="320" fill="#1d4ed8">1N4007 을 코일 양 끝에 역방향 병렬 (띠가 85 = + 쪽)</text>
<text x="20" y="480">5V 릴레이 모듈: VCC → 5V, GND → GND, IN → D12 (IN=LOW 일 때 켜지는 모듈 기준)</text>
<text x="20" y="505" fill="#9a3412">⚠ 학교 재료로 만든 덮개에 스위치를 답니다. 덮개를 안 만들 때만 이 자리를 전선으로 잇습니다. 비상정지는 꼭 답니다.</text></g></svg>"""
    return f"""<div class="pg"><div class="pad"><h2>배선 1 · 모터 전원과 안전 회로</h2>{svg}
<p class="small">회로는 설계서 9장 그대로. 40A 릴레이 단자 번호(30·87·85·86)는 흔한 자동차 릴레이 기준이고, 산 소켓의 선 색은 제품마다 달라 미확인입니다 → 멀티미터로 확인.</p></div></div>"""

def arduino_page():
    rows = [('D4', '1단 홀센서 (레일 1-2, 끝판 B에서 먼 쪽)'), ('D5', '2단 홀센서 (레일 1-2, 가까운 쪽)'), ('D6', '3단 (레일 3-4, 먼 쪽)'), ('D8', '4단 (레일 3-4, 가까운 쪽)'),
            ('D9', '5단 (레일 5-R, 먼 쪽)'), ('D10', '후진 R (레일 5-R, 가까운 쪽)'), ('D7', '출력축 rpm 홀센서 (바퀴 덮개)'), ('D11', '코스 복귀 버튼 → GND (없으면 비워 둠)'),
            ('D12', '5V 릴레이 모듈 IN'), ('A0', '가속 페달 신호 (먼저 멀티미터로 0~5V인지 확인, GND 공통)'), ('A1', '클러치 페달 가변저항 가운데 다리 (양 끝 = 5V, GND)'),
            ('A2', '핸들 (안 씀 → GND에 이음)'), ('A3', '브레이크 (안 씀 → GND에 이음)'), ('A4', '안전 회로 감지점 (10k/4.7k 분압)')]
    t = ''.join(f'<tr><td><b>{a}</b></td><td>{E(b)}</td></tr>' for a, b in rows)
    return f"""<div class="pg"><div class="pad"><h2>배선 2 · 아두이노 레오나르도 핀</h2><div class="cols"><div><table><tr><th>핀</th><th>연결</th></tr>{t}</table></div>
<div><p style="font-size:11pt;line-height:1.7"><b>홀센서 A3144 7개</b> (글자가 보이는 면에서 왼쪽부터)<br>① VCC → 5V &nbsp; ② GND → GND &nbsp; ③ OUT → 위 표의 핀<br>저항은 필요 없습니다 (펌웨어가 내부 풀업을 켬).</p>
<p style="font-size:11pt;line-height:1.7"><b>자석</b>: 러그 3개(밑면), 표시 바퀴 4개(테). 센서 평면과 자석 사이 약 2.5mm.</p>
<p style="font-size:11pt;line-height:1.7"><b>전선</b>: 센서·가변저항은 점퍼 케이블, 5V·GND는 만능기판에서 모아 나눔.</p>
<p class="small">핀 번호는 펌웨어 build/src/fw/shifter_controller/shifter_controller.ino 그대로입니다 (GEAR_PIN = 4, 5, 6, 8, 9, 10).</p></div></div></div></div>"""

def fw_page():
    tests = [('1', '켜기', '가속 페달을 뗀 채 전원 → 0.5초 뒤 릴레이 딸깍 (모터 허가)'),
             ('2', '센서', '레버를 각 단에 넣고 시리얼 모니터/게임 컨트롤러 화면에서 그 단 버튼 1개만 켜지는지'),
             ('3', '클러치 미끄럼', '모터 달기 전: 입력축 B 끝 칼라를 플라이어로 잡고, 앞판 둘레(반지름 50)에 끈 → 2L 생수병에 물. 0.82~1.53kg에서 미끄러지면 정상 (0.40~0.75 N·m)'),
             ('4', '비상정지', '주행 중 3번 누름 → 바로 멈춤, 풀어도 가속 페달을 뗄 때까지 안 돎'),
             ('5', '막힘 차단', '바퀴 덮개 센서 선을 뽑고 1단·클러치 뗌·페달 50% → 5초 안에 모터 차단, 페달 1초 떼면 다시 허가'),
             ('6', '변속', '클러치 밟고 1→5단, 다운시프트, 건너뛰기 100번 → 핀·포켓 파손 없음')]
    t = ''.join(f'<tr><td>{a}</td><td><b>{E(b)}</b></td><td>{E(d)}</td></tr>' for a, b, d in tests)
    return f"""<div class="pg"><div class="pad"><h2>펌웨어 올리기 · 시운전</h2><div class="cols"><div><ol class="rules">
<li>컴퓨터에 Arduino IDE를 설치합니다.</li>
<li>라이브러리 "Joystick" (Matthew Heironimus)를 설치합니다. 라이브러리 관리에 없으면 GitHub ArduinoJoystickLibrary ZIP으로 설치합니다 (검색 결과는 미확인).</li>
<li>압축 파일의 shifter_controller.ino를 열고, 보드 = Arduino Leonardo, 포트를 고른 뒤 업로드합니다.</li>
<li>릴레이 모듈이 IN=HIGH일 때 켜지는 제품이면 파일 위쪽 RELAY_ACTIVE_LOW 를 false 로 바꿔 다시 올립니다.</li></ol></div>
<div><table><tr><th></th><th>시험</th><th>합격</th></tr>{t}</table>
<p class="small" style="margin-top:3mm">도는 부품을 손으로 막는 시험은 하지 않습니다. 시험 내용은 설계서 8장에서 덮개 관련만 뺀 것입니다.</p></div></div></div></div>"""

pages = [cover(), rules(), plates_page(), parts_page(), fit_page()] + [step_page(s, len(S)) for s in S if s['sec'] != '완성'] + [wiring_page(), arduino_page(), fw_page(), trouble_page(), end_page()]
open(os.path.join(HERE, 'manual.html'), 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(pages)}</body></html>')
print(len(pages), 'pages')
