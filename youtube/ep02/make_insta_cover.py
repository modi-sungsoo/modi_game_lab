"""2편 유튜브 썸네일을 인스타 릴스 커버(1080x1920)로 세로 재배치 (1편 커버와 같은 틀).
글자는 프로필 격자에 보이는 가운데 3:4(y 240~1680) 안에만 둔다.
사용: python make_insta_cover.py
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

SRC = "C:/Users/user/Desktop/유튜브/영상/2편_2D 보드게임 3D화/2편 소스"
OUT = "C:/Users/user/Desktop/유튜브/썸네일/2편"
TD = "C:/Users/user/AppData/Local/Temp/dv_ep2_cover"; os.makedirs(TD, exist_ok=True)
EB = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\NanumSquareEB.ttf")
YEL, WHITE, BLACK, PAPER = (255, 200, 61), (255, 255, 255), (15, 15, 15), (240, 239, 234)
font = lambda n: ImageFont.truetype(EB, n)

def frame(src, t, name):
    p = f"{TD}/{name}.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", p], check=True)
    return Image.open(p).convert("RGB")

def fit(im, w, h):
    r = max(w / im.width, h / im.height); im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))

before = frame(f"{SRC}/언리얼_02_예고_기본도형.mp4", 1.0, "before").crop((380, 60, 1700, 940))   # 썸네일과 같은 장면
after = frame(f"{SRC}/디빌 언리얼 플레이 장면_2.mkv", 180, "after").crop((900, 200, 1700, 1250))  # 원목 판 가운데를 세로로

W, H, IMG_H = 1080, 1920, 1060
A = Image.new("RGB", (W, H), PAPER)
A.paste(fit(after, W, IMG_H), (0, 0))
shade = Image.new("L", (W, IMG_H), 0); sd = ImageDraw.Draw(shade)
for y in range(660): sd.line((0, y, W, y), fill=int(190 * (1 - y / 660)))
A.paste(Image.new("RGB", (W, IMG_H), BLACK), (0, 0), shade)
d = ImageDraw.Draw(A)
d.polygon([(0, IMG_H - 60), (W, IMG_H - 140), (W, IMG_H), (0, IMG_H)], fill=PAPER)   # 비스듬한 경계

# 위: 스팀 출시까지 한 달
d.text((W // 2, 280), "스팀 출시까지", font=font(116), fill=WHITE, anchor="ma", stroke_width=10, stroke_fill=BLACK)
d.text((W // 2, 410), "한 달", font=font(250), fill=YEL, anchor="ma", stroke_width=14, stroke_fill=BLACK)

# 가운데 아래: 지난 편 기본 도형 ↔ 이번 편 3D(위 사진)
d.text((70, 1010), "지난 편", font=font(96), fill=BLACK)
d.text((1010, 1030), "이번 편 ▲", font=font(70), fill=BLACK, anchor="ra")
d.rounded_rectangle((60, 1140, 1020, 1400), 30, fill=WHITE, outline=(200, 200, 195), width=4)
A.paste(fit(before, 940, 240), (70, 1150))

# 아래: 제목 (세로 영상 위 제목과 같은 문구)
for i, line in enumerate(["웹게임을 3D로 옮기고", "스팀 등록까지"]):
    y = 1450 + i * 112
    l, t, r, b = d.textbbox((W // 2, y), line, font=font(74), anchor="ma")
    d.rectangle((l - 18, t - 14, r + 18, b + 14), fill=YEL if i else BLACK)
    d.text((W // 2, y), line, font=font(74), fill=BLACK if i else WHITE, anchor="ma")

A.save(f"{OUT}/인스타_릴스_커버_1080x1920.png")
A.crop((0, 240, W, 1680)).resize((360, 480), Image.LANCZOS).save(f"{TD}/grid_preview.png")   # 프로필 격자 미리보기
print("ok")
