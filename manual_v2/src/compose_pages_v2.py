# 2차 설명서 쪽 합성 (1400x1000). 사용: python3 compose_pages_v2.py 그림폴더 썸네일폴더 출력폴더
import sys
from PIL import Image, ImageDraw, ImageFont, ImageChops
FIG, TH, OUT = sys.argv[1:4]
F = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
font = lambda s: ImageFont.truetype(F, s, index=1)   # index 1 = Noto Sans CJK KR
W, H, BG = 1400, 1000, (248, 248, 248)
NAVY, ORANGE_T = (20, 60, 110), (120, 70, 0)

def crop(im):
    im = im.convert('RGB'); bg = Image.new('RGB', im.size, im.getpixel((0, 0)))
    b = ImageChops.difference(im, bg).getbbox(); return im.crop(b) if b else im

def fit(im, w, h):
    # 배경색(왼쪽 위 픽셀)을 투명하게 만들어 어떤 상자 위에 붙여도 배경 사각형이 안 보이게 함
    bgc = im.convert('RGB').getpixel((0, 0))          # 자르기 전 모서리 = 배경색
    im = crop(im); s = min(w / im.width, h / im.height)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    bg = Image.new('RGB', im.size, bgc)
    a = ImageChops.difference(im, bg).convert('L').point(lambda v: 255 if v > 6 else 0)
    im = im.convert('RGBA'); im.putalpha(a); return im

def text_fit(d, xy, s, size, fill, maxw, anchor='mm'):
    while d.textlength(s, font=font(size)) > maxw: size -= 1
    d.text(xy, s, font=font(size), fill=fill, anchor=anchor); return size

NAME = {'plate_out': 'plate_out', 'plate_in': 'plate_in', 'sun': 'sun', 'planet': 'planet', 'carrier': 'carrier',
        'hub': 'hub', 'ring': 'ring', 'tray': 'tray', 'cradle': 'cradle', 'encoder': 'encoder',
        'bracket_in': 'bracket_in', 'bracket': 'bracket', 'bearing': '베어링', 'shaft50': '막대 50 mm',
        'shaft75': '막대 75 mm', 'bolt': '볼트', 'nut': '너트', 'screw': 'M3 나사', 'motor': '모터',
        'tie': '케이블타이', 'coupling': '커플링', 'magnet': '자석', 'hall': '홀센서', 'tsens': '온도센서',
        'oil': '오일 39 mL', 'sub7': '4~5단계 덩어리', 'sub8': '3단계 덩어리', 'sub9': '2단계 판', 'sub13': '기어 상자'}

def inset(P, img, box, shape, label):
    """확대/보조 그림: shape='circle' 이면 원형, 아니면 사각 상자"""
    d = ImageDraw.Draw(P); x0, y0, x1, y1 = box
    if shape == 'circle':
        d.ellipse(box, fill='white', outline=(200, 40, 40), width=6)
        m = fit(Image.open(img), int((x1 - x0) * 0.66), int((y1 - y0) * 0.66))
        P.paste(m, ((x0 + x1 - m.width) // 2, (y0 + y1 - m.height) // 2), m)
        d.ellipse(box, outline=(200, 40, 40), width=6)
    else:
        d.rounded_rectangle(box, 14, fill='white', outline=NAVY, width=5)
        m = fit(Image.open(img), x1 - x0 - 30, y1 - y0 - 60)
        P.paste(m, ((x0 + x1 - m.width) // 2, y0 + 45 + (y1 - y0 - 55 - m.height) // 2), m)
    tw = d.textlength(label, font=font(24)) + 24
    lx = (x0 + x1) / 2
    d.rounded_rectangle([lx - tw / 2, y0 - 18, lx + tw / 2, y0 + 18], 10, fill=(200, 40, 40) if shape == 'circle' else NAVY)
    d.text((lx, y0), label, font=font(24), fill='white', anchor='mm')

# (단계, 본 그림, 부품[(썸네일, 개수)], 설명, 팁, 보조 그림[(파일, 모양, 이름표)])
S = [
 (1, 's1', [('plate_out', 1), ('bearing', 1)], '베어링을 plate_out 안쪽 가운데 구멍에 꾹 눌러 넣어요', '돌기 2개 있는 면이 안쪽 · 좁은 쪽부터 넣기',
  [('c1', 'circle', '턱에 걸릴 때까지'), ('b1', 'rect', '뒤집으면 육각 홈 4개')]),
 (2, 's2', [('plate_in', 1), ('bearing', 1)], 'plate_in에도 베어링을 똑같이 넣어요', 'plate_in = 바깥면에 육각 홈이 없는 판',
  [('c2', 'circle', '턱에 걸릴 때까지')]),
 (3, 's3', [('sun', 1), ('shaft50', 1)], '짧은 막대(50 mm)를 sun 가운데 구멍에 끼워요', '막대 끝 = 기어 이 쪽 면 (딱 같은 높이)',
  [('c3', 'circle', '끝이 같은 높이')]),
 (4, 's4', [('hub', 1), ('shaft75', 1), ('carrier', 1)], '긴 막대(75 mm)를 hub에 끼우고, carrier 아래에서 육각을 꽂아요',
  '막대 끝 = 육각 끝면 · 둥근 쪽은 구멍보다 커서 안 들어가요', [('c4', 'circle', '끝이 같은 높이')]),
 (5, 's5', [('planet', 3)], 'planet 3개를 carrier 기둥에 끼워요', '점 있는 면이 아래(carrier 쪽) · 3개 모두 같게',
  [('c5', 'circle', '이 면이 아래로')]),
 (6, 's6', [('ring', 1)], 'ring을 plate_out 위에 올려요', '판의 돌기 2개를 ring 구멍에 맞추기',
  [('c6', 'circle', '돌기가 구멍에 쏙')]),
 (7, 's7', [('sub7', 1)], '긴 막대를 베어링에 꽂으며 carrier 덩어리를 ring 안에 넣어요', '안 들어가면 planet을 살살 돌려 3개를 함께 맞물리기', []),
 (8, 's8', [('sub8', 1)], 'sun 덩어리를 가운데에 밀어 넣어요', '짧은 막대가 위로 · sun을 살살 돌리며 넣기', []),
 (9, 's9', [('sub9', 1)], 'plate_in을 덮어요', '베어링 넣은 안쪽 면이 아래 · 돌기 2개를 ring 구멍에', []),
 (10, 's10', [('bolt', 4)], '볼트 4개를 plate_in 쪽에서 끝까지 꽂아요', '볼트 머리는 plate_in 쪽', []),
 (11, 's11', [('nut', 4)], '뒤집어서 plate_out 육각 홈에 너트를 넣고 조여요', '너트가 홈 안으로 쏙 · 4곳을 번갈아 조금씩',
  [('c11', 'circle', '너트가 홈 안에')]),
 (12, 's12', [], '짧은 막대를 손으로 돌려 봐요', '짧은 막대 4바퀴 = 긴 막대 1바퀴 (걸림 없이 돌면 성공)', []),
 (13, 's13', [('sub13', 1), ('tray', 1)], '기어 상자를 트레이에 세워요', '부채꼴 창이 아래 · 긴 막대 쪽이 빈 칸 쪽', []),
 (14, 's14', [('cradle', 2), ('screw', 2)], '모터 받침을 레일 양쪽에 나사로 고정해요', '받침 위치는 그림처럼 (커플링 길이에 맞추기)', []),
 (15, 's15', [('encoder', 2), ('magnet', 2)], '자석을 원판 홈에 넣고, 원판을 막대 끝에서 끼워 끝벽 위까지 밀어요',
  '자석 홈이 바깥(센서 쪽) · 커플링보다 먼저!', [('c15', 'circle', '자석은 홈에'), ('L15', 'rect', '반대쪽에서 보면')]),
 (16, 's16', [('motor', 2), ('tie', 4)], '모터를 받침에 올리고 케이블타이로 느슨하게 감아요', '타이는 받침 아래 통로로 지나가요',
  [('c16', 'circle', '타이 지나가는 길')]),
 (17, 's17', [('coupling', 2)], '커플링을 모터 축에 끼운 뒤, 모터를 밀어 막대에 끼워요', '커플링 나사를 조이고 케이블타이를 꽉',
  [('L17', 'rect', '반대쪽에서 보면')]),
 (18, 's18', [('bracket_in', 1), ('bracket', 1), ('hall', 2), ('screw', 2)], '센서 받침을 끝벽 위에 나사로 세우고, 홀센서를 원판 옆에 둬요',
  '센서~원판 2~3 mm · 입력쪽(왼쪽)은 bracket_in', [('c18', 'circle', '빨간 막대 = 2~3 mm'), ('L18', 'rect', '반대쪽에서 보면')]),
 (19, 's19', [('tsens', 1)], '온도센서를 빈 칸의 고리에 꽂아요', '센서 끝이 오일에 잠기게', []),
 (20, 's20', [('oil', 1)], '주사기로 오일 39 mL를 빈 칸에 넣어요', '안쪽 벽 가운데 긴 눈금(15 mm)까지',
  [('c20', 'circle', '가운데 긴 줄 = 15 mm')]),
]

def page(n, img, parts, cap, tip, extras):
    P = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(P)
    d.text((40, 5), str(n), font=font(120), fill=(30, 30, 30))
    top = 40
    if parts:
        cw = 150; bx, by = 200, 30; bw = cw * len(parts) + 20; bh = 200
        d.rounded_rectangle([bx, by, bx + bw, by + bh], 18, fill=(214, 234, 248), outline=(120, 170, 210), width=4)
        for i, (t, q) in enumerate(parts):
            th = fit(Image.open(f'{TH}/t_{t}.png'), 115, 105)
            cx = bx + 10 + i * cw + cw // 2
            P.paste(th, (cx - th.width // 2, by + 12 + (105 - th.height) // 2), th)
            d.text((cx, by + 140), f'×{q}', font=font(30), fill=NAVY, anchor='mm')
            text_fit(d, (cx, by + 178), NAME[t], 20, (60, 60, 60), cw - 10)
        top = by + bh
    # 그림 영역: top+20 ~ H-130, 보조 그림이 있으면 오른쪽 400px 를 씀
    y0, y1 = top + 20, H - 135
    side = 420 if extras else 0
    m = fit(Image.open(f'{FIG}/{img}.png'), W - 80 - side, y1 - y0)
    P.paste(m, (40 + (W - 80 - side - m.width) // 2, y0 + (y1 - y0 - m.height) // 2), m)
    if extras:
        k = len(extras); x0 = W - side + 10; x1 = W - 30
        hgt = (H - 150 - 60) // k if k > 1 else min(390, x1 - x0)
        ys = 60 if k > 1 else max(y0 + 20, (y0 + y1 - hgt) // 2)
        for i, (f, shape, label) in enumerate(extras):
            yy = ys + i * (hgt + 15)
            if shape == 'circle':
                r = min(x1 - x0, hgt) // 2; cx, cy = (x0 + x1) // 2, yy + hgt // 2
                inset(P, f'{FIG}/{f}.png', (cx - r, cy - r, cx + r, cy + r), shape, label)
            else:
                inset(P, f'{FIG}/{f}.png', (x0, yy, x1, yy + hgt), shape, label)
    text_fit(d, (W // 2, H - 102), cap, 34, (20, 20, 20), W - 60)
    if tip:
        sz = 28
        while d.textlength('!  ' + tip, font=font(sz)) + 40 > W - 60: sz -= 1
        tw = d.textlength('!  ' + tip, font=font(sz)) + 40
        d.rounded_rectangle([W // 2 - tw / 2, H - 72, W // 2 + tw / 2, H - 20], 14, fill=(255, 236, 179), outline=(230, 160, 0), width=3)
        d.text((W // 2, H - 46), '!  ' + tip, font=font(sz), fill=ORANGE_T, anchor='mm')
    return P

pages = []
# 0쪽: 부품 전체
P = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(P)
d.text((W // 2, 50), '부품을 모두 꺼내 개수를 세요', font=font(50), fill=(30, 30, 30), anchor='mm')
printed = [('plate_out', 1), ('plate_in', 1), ('sun', 1), ('planet', 3), ('carrier', 1), ('hub', 1), ('ring', 1),
           ('tray', 1), ('cradle', 2), ('encoder', 2), ('bracket_in', 1), ('bracket', 1)]
bought = [('bearing', 2), ('shaft50', 1), ('shaft75', 1), ('bolt', 4), ('nut', 4), ('screw', 4), ('motor', 2),
          ('tie', 4), ('coupling', 2), ('magnet', 2), ('hall', 2), ('tsens', 1), ('oil', 1)]
d.text((40, 100), '3D 프린터로 뽑은 부품 (주황)', font=font(28), fill=ORANGE_T)
d.text((40, 535), '산 물건', font=font(28), fill=(60, 60, 60))
cols, cw, ch = 7, W // 7, 205
for grp, ytop in ((printed, 140), (bought, 575)):
    for i, (t, q) in enumerate(grp):
        r, c = divmod(i, cols); x0, yy = c * cw, ytop + r * ch
        th = fit(Image.open(f'{TH}/t_{t}.png'), 135, 115)
        P.paste(th, (x0 + (cw - th.width) // 2, yy + (115 - th.height) // 2), th)
        text_fit(d, (x0 + cw // 2, yy + 140), f'{NAME[t]} ×{q}', 24, NAVY, cw - 8)
d.line([30, 525, W - 30, 525], fill=(180, 180, 180), width=2)
text_fit(d, (W // 2, H - 22), 'bracket_in = 입력쪽(왼쪽)용으로 새로 뽑은 받침 · 홀센서와 온도센서는 README 구매 목록에는 없지만 필요해요', 22, (90, 90, 90), W - 40)
pages.append(P)
for s in S: pages.append(page(*s))
# 21쪽: 완성
P = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(P)
d.text((40, 5), '21', font=font(120), fill=(30, 30, 30))
d.text((W // 2, 80), '완성!', font=font(80), fill=(30, 30, 30), anchor='mm')
m = fit(Image.open(f'{FIG}/s21.png'), W - 500, H - 330); P.paste(m, (40 + (W - 500 - m.width) // 2, 160 + (H - 330 - m.height) // 2), m)
inset(P, f'{FIG}/L21.png', (W - 440, 260, W - 30, 650), 'rect', '반대쪽에서 보면')
text_fit(d, (W // 2, H - 102), '모터가 짧은 막대(sun)를 돌리면 → 긴 막대가 4배 느리게 같은 방향으로 돌아요', 34, (20, 20, 20), W - 60)
tip = '!  실험 전후 사진은 같은 이(▲ 표시)를 앞에 두고 찍기'
tw = d.textlength(tip, font=font(28)) + 40
d.rounded_rectangle([W // 2 - tw / 2, H - 72, W // 2 + tw / 2, H - 20], 14, fill=(255, 236, 179), outline=(230, 160, 0), width=3)
d.text((W // 2, H - 46), tip, font=font(28), fill=ORANGE_T, anchor='mm')
pages.append(P)
# 22쪽: 그림에 대한 안내
P = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(P)
d.text((W // 2, 60), '그림에 대해 알아 두기', font=font(50), fill=(30, 30, 30), anchor='mm')
L = ['● 주황 = 이번에 끼우는 출력 부품 · 회색 = 이미 끼운 부품 · 산 물건 = 실제 색에 가깝게',
     '● 출력 부품(판·기어·트레이·받침·원판)은 설계 파일(planetary_testrig.scad)의 모양과 치수 그대로예요.',
     '● 아래 산 물건은 설계 파일에 없어서 모양을 단순하게 그렸어요:',
     '    – 모터 JGA25-370: 기어부 Ø25×21 + 몸통 Ø24.4×31 = 총길이 52 mm(실측), 축 Ø4×10',
     '    – 커플링 4-6 mm: Ø12×25 원통 (실제 모양·나사 위치는 제품마다 달라요)',
     '    – 홀센서 3144, 온도센서 DS18B20(Ø6), 케이블타이, 주사기',
     '    – 볼트·너트·나사·자석·베어링은 규격 치수로 그린 단순한 모양',
     '● 입력쪽(왼쪽) 센서 받침은 판과 겹치지 않게 몸체를 바깥으로 4 mm 옮긴 bracket_in이에요.',
     '● 자석 원판은 커플링보다 먼저 끼워요 (커플링을 끼우면 막대 끝이 막혀요).',
     '● 홀센서를 받침에 붙이는 방법은 설계에 없어요. 테이프 등으로 2~3 mm 간격에 맞춰 주세요.',
     '● 그림의 화살표: 빨간 곧은 화살표 = 끼우는 방향, 빨간 둥근 화살표 = 돌리는 방향']
y = 150
for s in L:
    text_fit(d, (60, y), s, 28, (30, 30, 30), W - 100, anchor='lm'); y += 70
pages.append(P)
for i, P in enumerate(pages): P.save(f'{OUT}/page{i:02d}.png')
pages[0].save(f'{OUT}/manual.pdf', save_all=True, append_images=pages[1:], resolution=150)
print(len(pages), '쪽')
