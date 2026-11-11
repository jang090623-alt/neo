# Google 문서 read_doc JSON 을 읽어 단락·표 위치를 구하는 도구
import json, re
def load(path):
    c = json.load(open(path))['content']; return c, c['tabs'][0]['documentTab']['body']['content']
def ptext(p): return ''.join(r.get('textRun', {}).get('content', '') for r in p['elements'])
def paragraphs(body):
    return [(e['startIndex'], e['endIndex'], ptext(e['paragraph'])) for e in body if 'paragraph' in e]
def tables(body):
    return [e for e in body if 'table' in e]
def cells(tbl):
    out = []
    for row in tbl['table']['tableRows']:
        out.append([(c['content'][0]['startIndex'], c['content'][-1]['endIndex'], ''.join(ptext(x['paragraph']) for x in c['content'] if 'paragraph' in x)) for c in row['tableCells']])
    return out
