"""건물 타일 12장을 육각형 투명 PNG로 잘라내고, 정산 표 카드 PNG(단계별 공개)를 만든다."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

SRC, TILE_DIR, CARD_DIR = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(TILE_DIR, exist_ok=True); os.makedirs(CARD_DIR, exist_ok=True)

# ---------- 타일 ----------
NAMES = ["역세권", "회사", "공장", "상점", "묘지", "학교",
         "복지관", "도서관", "쓰레기매립지", "하수처리장", "공원", "집"]
img = Image.open(SRC).convert("RGB")
a = np.asarray(img).astype(int)
bg = a[2, 2]                                   # 배경(짙은 초록)
diff = np.abs(a - bg).sum(axis=2) > 40
W, H = img.size
cw, rh = W / 6, H / 2
for i, name in enumerate(NAMES):
    r, c = divmod(i, 6)
    x0, y0, x1, y1 = int(c * cw), int(r * rh), int((c + 1) * cw), int((r + 1) * rh)
    ys, xs = np.nonzero(diff[y0:y1, x0:x1])
    bx0, bx1, by0, by1 = xs.min() + x0, xs.max() + x0 + 1, ys.min() + y0, ys.max() + y0 + 1
    tile = img.crop((bx0, by0, bx1, by1)).convert("RGBA")
    w, h = tile.size
    S = 4                                          # 안티앨리어싱용 초과 샘플링
    m = Image.new("L", (w * S, h * S), 0)
    ImageDraw.Draw(m).polygon([(w*S/2, 0), (w*S, h*S/4), (w*S, h*S*3/4), (w*S/2, h*S),
                               (0, h*S*3/4), (0, h*S/4)], fill=255)
    tile.putalpha(m.resize((w, h), Image.LANCZOS))
    tile.save(os.path.join(TILE_DIR, f"{i+1:02d}_{name}.png"))
    assert 150 < w < 260 and 180 < h < 280, (name, w, h)   # 셀 하나에 타일 하나만 잡혔는지

# ---------- 정산 표 카드 ----------
BG, CARD, INK, SUB, ACC, LINE = (11, 58, 46), (247, 244, 233), (28, 32, 30), (110, 116, 110), (232, 120, 40), (222, 216, 200)
# 맑은 고딕 Regular는 작은 크기에서 '같' 받침이 깨져 나와서 나눔스퀘어를 쓴다 (썸네일과 같은 서체)
NS = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\NanumSquare")
F = lambda s, b=True: ImageFont.truetype(NS + ("EB.ttf" if b else "R.ttf"), s)

def card(draw, box, title, sub, rows, total, shown):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, 22, fill=CARD)
    draw.text((x0 + 40, y0 + 34), title, font=F(40), fill=INK)
    draw.text((x0 + 40, y0 + 92), sub, font=F(22, False), fill=SUB)
    y = y0 + 150
    for k, (label, val) in enumerate(rows):
        if k >= shown: return
        draw.line((x0 + 40, y, x1 - 40, y), fill=LINE, width=2)
        draw.text((x0 + 40, y + 20), label, font=F(30, False), fill=INK)
        draw.text((x1 - 40, y + 20), val, font=F(32), fill=INK, anchor="ra")
        y += 76
    if shown > len(rows):
        draw.line((x0 + 40, y, x1 - 40, y), fill=INK, width=3)
        draw.text((x0 + 40, y + 22), total[0], font=F(32), fill=INK)
        draw.text((x1 - 40, y + 14), total[1], font=F(44), fill=ACC, anchor="ra")

LEFT = ("1편 정산", "Claude Pro 구독 안에서 작업",
        [("기획", "10분"), ("아트", "10분"), ("다듬기 · QA", "180분")], ("추가 비용", "$0"))
RIGHT = ("API로 썼다면?", "언리얼 1차 구현, 같은 양을 API 단가로 환산",
         [("Opus 5.5", "약 $20"), ("Fable 5.2", "약 $51")], ("합계", "약 $71"))
# 단계: 왼쪽 행을 하나씩(0~4), 그다음 오른쪽 행을 하나씩(0~3)
steps = [(n, -1) for n in range(1, 5)] + [(4, n) for n in range(0, 4)]
for k, (ls, rs) in enumerate(steps):
    im = Image.new("RGB", (1920, 1080), BG)
    d = ImageDraw.Draw(im)
    card(d, (110, 290, 930, 790), *LEFT, ls)
    if rs >= 0:
        card(d, (990, 290, 1810, 790), *RIGHT, rs)
    im.save(os.path.join(CARD_DIR, f"cost_{k}.png"))
print("tiles", len(os.listdir(TILE_DIR)), "cards", len(steps))
