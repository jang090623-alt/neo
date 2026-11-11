import sys, json
from gdoc import *; from tables import TABLES
c, body = load(sys.argv[1]); tb = tables(body)[2:]            # 앞의 2개는 표지·요약 표
assert len(tb) == 12, len(tb)
want = [int(x) for x in sys.argv[2].split(',')]
reqs = []
for n in sorted(want, reverse=True):
    cs = cells(tb[n - 1]); data = TABLES[n]
    assert len(cs) == len(data) and len(cs[0]) == len(data[0]), (n, len(cs), len(cs[0]))
    for r in range(len(data) - 1, -1, -1):
        for k in range(len(data[0]) - 1, -1, -1):
            assert cs[r][k][2] == '\n', (n, r, k, cs[r][k])
            if data[r][k]: reqs.append({"insertText": {"location": {"index": cs[r][k][0]}, "text": data[r][k]}})
idx = [q['insertText']['location']['index'] for q in reqs]; assert idx == sorted(idx, reverse=True)
print(json.dumps(reqs, ensure_ascii=False, separators=(',', ':')))
