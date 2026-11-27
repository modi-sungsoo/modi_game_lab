"""2편 썸네일(1280x720)과 30초 하이라이트(9:16 세로, 1배속·1.25배속)를 만든다. 1편 시안 A2·쇼츠 하이라이트와 같은 스타일.
사용: python make_thumb_hl.py
"""
import os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

SRC = "C:/Users/user/Desktop/유튜브/영상/2편_2D 보드게임 3D화/2편 소스"
OUT = "C:/Users/user/Desktop/유튜브/영상/2편_2D 보드게임 3D화"
TH = "C:/Users/user/Desktop/유튜브/썸네일/2편"
FINAL = f"{OUT}/2편_최종본_Modi_1080p_자막없음.mp4"     # 자막 없는 화면 + 최종 오디오
SRT = f"{OUT}/2편_편집.srt"
TD = "C:/Users/user/AppData/Local/Temp/dv_ep2_hl"; os.makedirs(TD, exist_ok=True); os.makedirs(TH, exist_ok=True)
FONT = "fontfile='C\\:/Windows/Fonts/malgunbd.ttf'"
TITLE = ("웹게임을 3D로 옮기고", "스팀 등록까지")
PICK = [(1, 3), (14, 14), (16, 16), (29, 30), (5, 6)]   # 기본도형→아트 → 가림 문제 → 해결 → 이상한 숫자 → 한 달 대기로 끝
ENC = ["-r", "30", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart"]

def run(args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode: sys.exit("\n".join(l for l in r.stderr.splitlines() if "Fontconfig" not in l))

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

# ---------------- 썸네일 ----------------
EB = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\NanumSquareEB.ttf")
YEL, WHITE, BLACK, PAPER = (255, 200, 61), (255, 255, 255), (15, 15, 15), (240, 239, 234)
font = lambda n: ImageFont.truetype(EB, n)

def frame(src, t, name):
    p = f"{TD}/{name}.png"; run(["-ss", str(t), "-i", src, "-frames:v", "1", p]); return Image.open(p).convert("RGB")

def fit(im, w, h):
    r = max(w / im.width, h / im.height); im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))

before = frame(f"{SRC}/언리얼_02_예고_기본도형.mp4", 1.0, "before").crop((380, 60, 1700, 940))   # 1920x1080 기본 도형
after = frame(f"{SRC}/디빌 언리얼 플레이 장면_2.mkv", 180, "after").crop((560, 230, 1960, 1260))  # 2560x1440 원목 판

A = Image.new("RGB", (1280, 720), PAPER)
A.paste(fit(after, 760, 720), (520, 0))
shade = Image.new("L", (760, 720), 0); sd = ImageDraw.Draw(shade)          # 오른쪽 위 글자 뒤를 어둡게
for y in range(300): sd.line((0, y, 760, y), fill=int(175 * (1 - y / 300)))
A.paste(Image.new("RGB", (760, 720), BLACK), (520, 0), shade)
d = ImageDraw.Draw(A)
d.polygon([(520, 0), (600, 0), (540, 720), (460, 720)], fill=PAPER)        # 비스듬한 경계

# 왼쪽 위: 지난 편 기본 도형 → 아래로 화살표
d.text((44, 34), "지난 편", font=font(46), fill=BLACK)
d.rounded_rectangle((40, 100, 470, 352), 18, fill=WHITE, outline=(200, 200, 195), width=3)
A.paste(fit(before, 414, 236), (48, 108))
d.polygon([(220, 372), (290, 372), (255, 418)], fill=BLACK)

# 왼쪽 아래: 3D 버전
for i, line in enumerate(["웹게임을", "3D로 옮겼다"]):
    y = 450 + i * 96
    l, t, r, b = d.textbbox((48, y), line, font=font(62))
    d.rectangle((l - 14, t - 12, r + 14, b + 12), fill=YEL if i else BLACK)
    d.text((48, y), line, font=font(62), fill=BLACK if i else WHITE)

# 오른쪽 위: 스팀 출시까지 한 달
d.text((1240, 36), "스팀 출시까지", font=font(80), fill=WHITE, anchor="ra", stroke_width=8, stroke_fill=BLACK)
d.text((1240, 128), "한 달", font=font(170), fill=YEL, anchor="ra", stroke_width=10, stroke_fill=BLACK)

A.save(f"{TH}/썸네일_최종.png")
A.resize((246, 138), Image.LANCZOS).save(f"{TD}/thumb_small.png")      # 유튜브 목록 크기에서 읽히는지 확인용

# ---------------- 30초 하이라이트 (세로) ----------------
t2s = lambda t: (lambda h, m, s: int(h) * 3600 + int(m) * 60 + float(s.replace(",", ".")))(*t.split(":"))
cues = [(t2s(a), t2s(b), x) for a, b, x in re.findall(r"\d+\n(\S+) --> (\S+)\n(.+?)\n", open(SRT, encoding="utf-8").read())]
END = dur(FINAL)
nxt = lambda n: cues[n][0] if n < len(cues) else END                 # n번째 줄 다음 줄이 시작하는 시각

def wrap(t, n=16):
    if len(t) <= n: return [t]
    sp = [i for i, ch in enumerate(t) if ch == " "]
    k = min(sp, key=lambda i: abs(i - len(t) / 2)); return [t[:k], t[k + 1:]]

def txt(name, s):
    p = f"{TD}/{name}.txt"; open(p, "w", encoding="utf-8").write(s); return p.replace(":", "\\:")

segs, subs, o = [], [], 0.0
for s, e in PICK:
    a, b = cues[s - 1][0], nxt(e)
    segs.append((a, b))
    for n in range(s, e + 1):
        ca, cb, x = cues[n - 1]; subs.append((o + ca - a, o + cb - a, x))
    o += b - a

fc = []
for i, (a, b) in enumerate(segs):
    fc.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.06,afade=t=out:st={b - a - 0.08:.3f}:d=0.08[a{i}]")
n = len(segs)
fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]")
fc.append("[cv]split[bgs][fgs]")
fc.append("[bgs]scale=-2:1920,crop=1080:1920,boxblur=24:2,eq=brightness=-0.18[bg]")
fc.append("[fgs]scale=1458:820:flags=lanczos,crop=1080:820[fg]")   # 1편 하이라이트처럼 1.35배 확대
d = ["[bg][fg]overlay=0:430",
     f"drawtext={FONT}:textfile='{txt('t1', TITLE[0])}':fontsize=76:fontcolor=white:box=1:boxcolor=black@0.85:boxborderw=22:x=(w-text_w)/2:y=180",
     f"drawtext={FONT}:textfile='{txt('t2', TITLE[1])}':fontsize=76:fontcolor=black:box=1:boxcolor=0xFFC83D:boxborderw=22:x=(w-text_w)/2:y=310"]
for i, (a, b, x) in enumerate(subs):
    for j, ln in enumerate(wrap(x)):
        d.append(f"drawtext={FONT}:expansion=none:textfile='{txt(f's{i}_{j}', ln)}':fontsize=64:fontcolor=white:borderw=5:bordercolor=black:"
                 f"box=1:boxcolor=black@0.55:boxborderw=16:x=(w-text_w)/2:y={1290 + j * 96}:enable='between(t,{a:.3f},{b - 0.02:.3f})'")
fc.append(",".join(d) + "[vout]")
open(f"{TD}/fc.txt", "w", encoding="utf-8").write(";\n".join(fc))
HL = f"{OUT}/2편_쇼츠_릴스_하이라이트_Modi_1080x1920"
run(["-i", FINAL, "-/filter_complex", f"{TD}/fc.txt", "-map", "[vout]", "-map", "[ca]", *ENC, f"{HL}.mp4"])

def s2t(x):
    ms = int(round(x * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
def write_srt(p, sp=1.0):
    open(p, "w", encoding="utf-8").write("\n".join(f"{i+1}\n{s2t(a/sp)} --> {s2t(b/sp)}\n{x}\n" for i, (a, b, x) in enumerate(subs)))
write_srt(f"{HL}.srt")
run(["-i", f"{HL}.mp4", "-filter_complex", "[0:v]setpts=PTS/1.25[v];[0:a]atempo=1.25[a]", "-map", "[v]", "-map", "[a]", *ENC, f"{HL}_1.25배속.mp4"])
write_srt(f"{HL}_1.25배속.srt", 1.25)
print(f"하이라이트 계획 {o:.2f}s, 결과 {dur(HL + '.mp4'):.2f}s / 1.25배속 {dur(HL + '_1.25배속.mp4'):.2f}s")
assert abs(dur(HL + ".mp4") - o) < 0.2
