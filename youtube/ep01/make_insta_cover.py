"""유튜브 썸네일 A2를 인스타 릴스 커버(1080x1920)로 세로 재배치. 글자는 프로필 격자에 보이는 가운데 3:4(y 240~1680) 안에만 둔다."""
import os
from PIL import Image, ImageDraw, ImageFont

S = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/") + "/thumb"
OUT = "C:/Users/user/Desktop/유튜브/썸네일/1. AI 딸깍 게임에 재미는 어떻게 입힐까요"
EB = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\NanumSquareEB.ttf")
YEL, WHITE, BLACK, PAPER = (255, 200, 61), (255, 255, 255), (15, 15, 15), (240, 239, 234)
font = lambda n: ImageFont.truetype(EB, n)

def fit(im, w, h):
    r = max(w / im.width, h / im.height); im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))

W, H, IMG_H = 1080, 1920, 1060
A = Image.new("RGB", (W, H), PAPER)
A.paste(fit(Image.open(f"{S}/f1680.png").crop((740, 200, 1790, 1440)), W, IMG_H), (0, 0))
shade = Image.new("L", (W, IMG_H), 0); sd = ImageDraw.Draw(shade)
for y in range(620): sd.line((0, y, W, y), fill=int(190 * (1 - y / 620)))
A.paste(Image.new("RGB", (W, IMG_H), BLACK), (0, 0), shade)
d = ImageDraw.Draw(A)
d.polygon([(0, IMG_H - 60), (W, IMG_H - 140), (W, IMG_H), (0, IMG_H)], fill=PAPER)   # 비스듬한 경계

# 위: 재미까지 3시간
d.text((W // 2, 280), "재미까지", font=font(120), fill=WHITE, anchor="ma", stroke_width=10, stroke_fill=BLACK)
d.text((W // 2, 410), "3시간", font=font(250), fill=YEL, anchor="ma", stroke_width=14, stroke_fill=BLACK)

# 가운데 아래: 명령어 1번 + 실제 프롬프트
d.text((70, 1000), "명령어 1번", font=font(110), fill=BLACK)
d.rounded_rectangle((60, 1150, 1020, 1390), 30, fill=WHITE, outline=(200, 200, 195), width=4)
for i, line in enumerate(["내가 첨부한 디자인빌리지 룰북을", "바탕으로 웹에서 플레이할 수 있게", "만들어줘."]):
    d.text((100, 1178 + i * 62), line, font=font(46), fill=(40, 40, 40))
d.ellipse((920, 1296, 990, 1366), fill=(217, 119, 87)); d.text((955, 1331), "↑", font=font(46), fill=WHITE, anchor="mm")
d.text((1010, 1030), "딸깍!", font=font(76), fill=BLACK, anchor="ra")

# 아래: 대본 제목 질문
for i, line in enumerate(["AI 딸깍 게임에", "재미는 어떻게 입힐까?"]):
    y = 1450 + i * 112
    l, t, r, b = d.textbbox((W // 2, y), line, font=font(74), anchor="ma")
    d.rectangle((l - 18, t - 14, r + 18, b + 14), fill=YEL if i else BLACK)
    d.text((W // 2, y), line, font=font(74), fill=BLACK if i else WHITE, anchor="ma")

A.save(f"{OUT}/인스타_릴스_커버_1080x1920.png")
A.crop((0, 240, W, 1680)).resize((360, 480), Image.LANCZOS).save("insta_grid_preview.png")   # 프로필 격자 미리보기
A.resize((540, 960), Image.LANCZOS).save("insta_cover_half.png")
print("ok")
