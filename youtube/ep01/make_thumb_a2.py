"""시안 A 다듬기: 명령어 1번 → 재미까지 3시간 + 대본 제목 질문."""
import os
from PIL import Image, ImageDraw, ImageFont

S = os.path.dirname(os.path.abspath(__file__)) + "/thumb"
OUT = "C:/Users/user/Videos/1편_썸네일"
EB = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\NanumSquareEB.ttf")
YEL, WHITE, BLACK, PAPER = (255, 200, 61), (255, 255, 255), (15, 15, 15), (240, 239, 234)
font = lambda n: ImageFont.truetype(EB, n)

def fit(im, w, h):
    r = max(w / im.width, h / im.height); im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))

A = Image.new("RGB", (1280, 720), PAPER)
A.paste(fit(Image.open(f"{S}/f1680.png").crop((740, 200, 1790, 1440)), 740, 720), (540, 0))

# 오른쪽 위 글자 뒤를 어둡게 (보드 위 글씨 대비)
shade = Image.new("L", (740, 720), 0); sd = ImageDraw.Draw(shade)
for y in range(330): sd.line((0, y, 740, y), fill=int(170 * (1 - y / 330)))
A.paste(Image.new("RGB", (740, 720), BLACK), (540, 0), shade)

d = ImageDraw.Draw(A)
d.polygon([(540, 0), (620, 0), (560, 720), (480, 720)], fill=PAPER)   # 비스듬한 경계

# 왼쪽: 명령어 1번 + 실제 프롬프트
d.text((44, 46), "명령어 1번", font=font(92), fill=BLACK)
# 실제 첫 프롬프트 문장을 읽히는 크기로 입력창 모양에 다시 씀
d.rounded_rectangle((40, 172, 500, 330), 22, fill=WHITE, outline=(200, 200, 195), width=3)
for i, line in enumerate(["내가 첨부한 디자인빌리지 룰북을", "바탕으로 웹에서 플레이할 수", "있게 만들어줘."]):
    d.text((66, 190 + i * 40), line, font=font(30), fill=(40, 40, 40))
d.ellipse((430, 268, 482, 320), fill=(217, 119, 87)); d.text((456, 294), "↑", font=font(34), fill=WHITE, anchor="mm")
d.text((440, 340), "딸깍!", font=font(48), fill=BLACK, stroke_width=0)

# 왼쪽 아래: 대본 제목 질문
for i, line in enumerate(["AI 딸깍 게임에", "재미는 어떻게 입힐까?"]):
    y = 440 + i * 92
    l, t, r, b = d.textbbox((50, y), line, font=font(56))
    d.rectangle((l - 14, t - 12, r + 14, b + 12), fill=YEL if i else BLACK)
    d.text((50, y), line, font=font(56), fill=BLACK if i else WHITE)

# 오른쪽: 재미까지 3시간
d.text((1236, 40), "재미까지", font=font(84), fill=WHITE, anchor="ra", stroke_width=8, stroke_fill=BLACK)
d.text((1236, 128), "3시간", font=font(170), fill=YEL, anchor="ra", stroke_width=10, stroke_fill=BLACK)

A.save(f"{OUT}/시안A2_최종.png")
A.resize((246, 138), Image.LANCZOS).save(f"{S}/a2_small.png")
A.resize((640, 360), Image.LANCZOS).save(f"{S}/a2_mid.png")
print("ok")
