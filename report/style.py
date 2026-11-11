import sys, json, re
from gdoc import *
c, body = load(sys.argv[1]); part = sys.argv[2]
PT = lambda v: {"magnitude": v, "unit": "PT"}
R = lambda s, e: {"startIndex": s, "endIndex": e}
paras = [e for e in body if 'paragraph' in e]
i0 = next(i for i, e in enumerate(paras) if 'Ⅰ. 서 론' in ptext(e['paragraph']) and e['startIndex'] > 1200)
B0, END = paras[i0]['startIndex'], body[-1]['endIndex']
tb = tables(body)[2:]
reqs = []
def pstyle(s, e, st): reqs.append({"updateParagraphStyle": {"range": R(s, e), "paragraphStyle": st, "fields": ",".join(st.keys())}})
def tstyle(s, e, st): reqs.append({"updateTextStyle": {"range": R(s, e), "textStyle": st, "fields": ",".join(st.keys())}})
YEL = {"backgroundColor": {"color": {"rgbColor": {"red": 1, "green": 0.95, "blue": 0.4}}}}
if part == 'base':
    tstyle(B0, END - 1, {"fontSize": PT(12)})
    seg = B0
    for t in tb + [None]:                       # 표 사이 구간(본문 단락)에만 단락 간격 적용
        e = t['startIndex'] if t else END
        pstyle(seg, e, {"spaceAbove": PT(12), "spaceBelow": PT(12)})
        if t: seg = t['endIndex']
    for t in tb: tstyle(t['startIndex'], t['endIndex'], {"fontSize": PT(10)})
if part == 'head':
    for e in paras[i0:]:
        s, en, tx = e['startIndex'], e['endIndex'], ptext(e['paragraph']).lstrip('\x0c').rstrip('\n')
        if any(t['startIndex'] < s < t['endIndex'] for t in tb): continue
        off = len(ptext(e['paragraph'])) - len(ptext(e['paragraph']).lstrip('\x0c'))
        if re.match(r'[ⅠⅡⅢⅣⅤⅥⅦ]\. ', tx):
            pstyle(s, en, {"alignment": "CENTER", "keepWithNext": True}); tstyle(s + off, en - 1, {"bold": True, "fontSize": PT(17)})
        elif re.match(r'\d\. ', tx) and len(tx) < 40:
            pstyle(s, en, {"keepWithNext": True}); tstyle(s, en - 1, {"bold": True, "fontSize": PT(15)})
        elif re.match(r'([가-힣]\. |\d\) )', tx) and len(tx) < 40:
            tstyle(s, en - 1, {"bold": True})
if part == 'cap':
    refs = False; later = []
    _t = tstyle
    def tstyle(a, b, st): later.append((a, b, st))
    for e in paras[i0:]:
        s, en, tx = e['startIndex'], e['endIndex'], ptext(e['paragraph']).rstrip('\n')
        if any(t['startIndex'] < s < t['endIndex'] for t in tb): continue
        if tx.startswith('<표 '): pstyle(s, en, {"alignment": "CENTER", "keepWithNext": True}); tstyle(s, en - 1, {"fontSize": PT(11), "bold": True})
        elif tx.startswith('[그림 '): pstyle(s, en, {"alignment": "CENTER"}); tstyle(s, en - 1, {"fontSize": PT(11), "bold": True})
        elif tx.startswith('【그림 '): pstyle(s, en, {"alignment": "CENTER", "keepWithNext": True}); tstyle(s, en - 1, YEL)
        elif '【각자 작성】' in tx: k = tx.index('【'); tstyle(s + k, en - 1, YEL)
        if tx.startswith('Ⅵ. '): refs = True
        elif tx.startswith('Ⅶ. '): refs = False
        elif refs: pstyle(s, en, {"indentStart": PT(24), "indentFirstLine": PT(0), "spaceAbove": PT(4), "spaceBelow": PT(4)})
if part == 'cap':
    tstyle = _t
    for a, b, st in later: tstyle(a, b, st)
if part == 'table':
    GRY = {"backgroundColor": {"color": {"rgbColor": {"red": 0.87, "green": 0.92, "blue": 0.97}}}}
    W = {1: {0: 150, 1: 75, 2: 45}, 2: {0: 80, 1: 135}, 3: {0: 70, 2: 150}, 4: {0: 65}, 6: {0: 150}, 7: {0: 105}, 8: {0: 70}, 9: {0: 105}, 10: {0: 130}, 12: {0: 80, 1: 145}}
    for n, t in enumerate(tb, 1):
        s = t['startIndex']; cs = cells(t); ncol = len(cs[0])
        if n == 5:
            tstyle(cs[0][0][0], cs[0][0][1] - 1, {"fontSize": PT(9), "weightedFontFamily": {"fontFamily": "Courier New"}}); continue
        if n == 11:
            pstyle(cs[0][0][0], cs[-1][-1][1], {"alignment": "CENTER"}); tstyle(cs[0][0][0], cs[0][-1][1] - 1, YEL); continue
        reqs.append({"updateTableCellStyle": {"tableRange": {"tableCellLocation": {"tableStartLocation": {"index": s}, "rowIndex": 0, "columnIndex": 0}, "rowSpan": 1, "columnSpan": ncol}, "tableCellStyle": GRY, "fields": "backgroundColor"}})
        tstyle(cs[0][0][0], cs[0][-1][1] - 1, {"bold": True}); pstyle(cs[0][0][0], cs[0][-1][1], {"alignment": "CENTER"})
        if n in (6, 7, 8, 9, 10): pstyle(cs[1][0][0], cs[-1][-1][1], {"alignment": "CENTER"})
        if n in (7, 9): tstyle(s, t['endIndex'], {"fontSize": PT(9)})
        for col, w in W.get(n, {}).items():
            reqs.append({"updateTableColumnProperties": {"tableStartLocation": {"index": s}, "columnIndices": [col], "tableColumnProperties": {"widthType": "FIXED_WIDTH", "width": PT(w)}, "fields": "widthType,width"}})
if part == 'mark':                                   # 추정값(사용자 확인 필요)에 노란 배경
    KEYS = ['오일 50 mL를 넣는다', '12 V로 맞추고', '기어는 같은 기어 세트를 계속 사용했다', '조건마다 1회씩 했으므로', '오일 50 mL를 비커에 담아', '같은 모터를 축에만 연결하고 전선은 연결하지 않았다',
            '고성능 엔진오일은 네 온도를 모두 측정하지 못해 결과에서 제외했다', '온도센서로 윤활제 온도를 잴 수 없었으므로', '같은 시험기와 기어 세트, 오일 50 mL, 전원 전압 12 V', 'ZIC TOP LS 5W-30', '모든 측정을 조건마다 1회씩만 했다', '같은 기어 세트를 계속 사용해']
    allp = []
    def walk(els):
        for e in els:
            if 'paragraph' in e: allp.append((e['startIndex'], ptext(e['paragraph'])))
            elif 'table' in e:
                for row in e['table']['tableRows']:
                    for cell in row['tableCells']: walk(cell['content'])
    walk(body)
    for k in KEYS:
        hit = [(s + t.index(k)) for s, t in allp if k in t and s >= B0]
        assert hit, k
        s = hit[0]; tstyle(s, s + len(k), YEL)       # 첫 등장만 (BMP 문자뿐이라 len = UTF-16 길이)
merged = []
for q in reqs:
    k = next(iter(q)); v = q[k]
    if merged and k == 'updateParagraphStyle' and next(iter(merged[-1])) == k:
        pv = merged[-1][k]
        if pv['paragraphStyle'] == v['paragraphStyle'] and pv['range']['endIndex'] == v['range']['startIndex']:
            pv['range']['endIndex'] = v['range']['endIndex']; continue
    merged.append(q)
reqs = merged
print(len(reqs), file=sys.stderr)
print(json.dumps(reqs, ensure_ascii=False, separators=(',', ':')))
