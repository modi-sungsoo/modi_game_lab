"""1편 유튜브 썸네일 시안 3개 (1280x720). 실제 녹화 화면과 건물 타일만 사용."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

S = os.path.dirname(os.path.abspath(__file__)) + "/thumb"
OUT = "C:/Users/user/Videos/1편_썸네일"; os.makedirs(OUT, exist_ok=True)
TILES = "C:/Users/user/Videos/1편_소스/타일"
EB = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\NanumSquareEB.ttf")
GREEN, YEL, WHITE, BLACK = (11, 58, 46), (255, 200, 61), (255, 255, 255), (15, 15, 15)
font = lambda n: ImageFont.truetype(EB, n)

def text(d, xy, s, size, fill=WHITE, stroke=10, anchor="la"):
    d.text(xy, s, font=font(size), fill=fill, stroke_width=stroke, stroke_fill=BLACK, anchor=anchor)

def chip(d, xy, s, size, bg=YEL, fg=BLACK, pad=16):   # 노란 띠 위 검은 글씨
    x, y = xy; l, t, r, b = d.textbbox((x, y), s, font=font(size))
    d.rounded_rectangle((l - pad, t - pad, r + pad, b + pad), 10, fill=bg); d.text((x, y), s, font=font(size), fill=fg)

def fit(im, w, h):   # 가운데 기준으로 비율 맞춰 자르고 크기 조정
    r = max(w / im.width, h / im.height); im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))

board82 = Image.open(f"{S}/f1680.png").crop((760, 200, 1840, 1440))     # 8.2 완성에 가까운 보드
board40 = Image.open(f"{S}/f370.png").crop((780, 230, 1620, 1400))      # 4.0 첫 구현 보드
prompt = Image.open(f"{S}/f26.5.png").crop((1000, 600, 1990, 970))      # 첫 프롬프트 입력창
tiles = [Image.open(f"{TILES}/{f}").convert("RGBA") for f in sorted(os.listdir(TILES)) if f.endswith(".png")]

# ---------- A: 명령어 1번 vs 재미 3시간 ----------
A = Image.new("RGB", (1280, 720), (236, 236, 232)); d = ImageDraw.Draw(A)
A.paste(fit(board82, 700, 720), (580, 0))
d.polygon([(560, 0), (640, 0), (580, 720), (500, 720)], fill=(236, 236, 232))   # 비스듬한 경계
p = prompt.resize((520, int(520 * prompt.height / prompt.width)), Image.LANCZOS)
A.paste(p, (40, 300)); d.rectangle((40, 300, 40 + p.width, 300 + p.height), outline=YEL, width=6)
text(d, (48, 70), "명령어", 96, fill=BLACK, stroke=0); text(d, (48, 175), "1번", 110, fill=BLACK, stroke=0)
text(d, (1240, 60), "재미는", 96, anchor="ra"); text(d, (1240, 170), "3시간", 150, fill=YEL, anchor="ra")
text(d, (48, 560), "AI가 만든 게임,", 52, fill=BLACK, stroke=0); text(d, (48, 625), "그다음은?", 52, fill=BLACK, stroke=0)
A.save(f"{OUT}/시안A_명령어1번_재미3시간.png")

# ---------- B: 타일 + 큰 질문 ----------
B = Image.new("RGB", (1280, 720), GREEN); d = ImageDraw.Draw(B)
glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((620, 40, 1300, 720), fill=(40, 120, 90, 160))
B.paste(glow.filter(ImageFilter.GaussianBlur(80)), (0, 0), glow.filter(ImageFilter.GaussianBlur(80)))
tw = 190; th = int(tw * tiles[0].height / tiles[0].width)
pos = [(0, 0), (1, 0), (2, 0), (-.5, 1), (.5, 1), (1.5, 1), (2.5, 1), (0, 2), (1, 2), (2, 2)]   # 벌집 배치
pick = [1, 3, 2, 9, 0, 10, 4, 11, 5, 8]
for (cx, cy), k in zip(pos, pick):
    t = tiles[k].resize((tw, th), Image.LANCZOS); B.paste(t, (int(700 + cx * tw * 1.0), int(60 + cy * th * 0.78)), t)
text(d, (60, 120), "AI 딸깍 게임에", 84); text(d, (60, 230), "재미는", 84)
chip(d, (70, 370), "어떻게 입힐까?", 92)
text(d, (60, 560), "보드게임 → 웹게임 → 언리얼", 40, fill=(210, 230, 220), stroke=6)
B.save(f"{OUT}/시안B_재미는어떻게.png")

# ---------- C: 비포 / 애프터 ----------
C = Image.new("RGB", (1280, 720), GREEN); d = ImageDraw.Draw(C)
before = ImageEnhance.Color(fit(board40, 560, 470)).enhance(0.35)
after = ImageEnhance.Color(fit(board82, 600, 500)).enhance(1.25)
C.paste(before, (30, 200)); C.paste(after, (650, 180))
d.rectangle((30, 200, 590, 670), outline=(200, 200, 200), width=5); d.rectangle((650, 180, 1250, 680), outline=YEL, width=8)
d.polygon([(600, 400), (640, 430), (600, 460)], fill=YEL)   # 화살표
chip(d, (50, 225), "명령어 1번", 40, bg=(60, 60, 60), fg=WHITE, pad=12)
chip(d, (672, 205), "+3시간", 48, pad=12)
text(d, (640, 70), "AI가 만든 게임, 재미는 사람이", 64, anchor="mm")
C.save(f"{OUT}/시안C_비포애프터.png")

# 작은 크기(검색 결과 크기) 미리보기
prev = Image.new("RGB", (3 * 246 + 40, 158), WHITE)
for i, im in enumerate((A, B, C)): prev.paste(im.resize((246, 138), Image.LANCZOS), (10 + i * 256, 10))
prev.save(f"{S}/thumbs_small.png")
big = Image.new("RGB", (1280, 3 * 720 + 40), WHITE)
for i, im in enumerate((A, B, C)): big.paste(im, (0, i * 740))
big.resize((640, big.height // 2)).save(f"{S}/thumbs_all.png")
print("ok")
