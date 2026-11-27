"""2편 영상(소리 없음)을 대본 줄 길이에 맞춰 소스에서 잘라 붙인다. 자막 번인 미리보기본과 SRT도 만든다.

사용: python build_ep2.py [나레이션 폴더]
  나레이션 폴더에 '{대본 문장}.mp3'(narrate_api.py 결과)가 있으면 그 길이에 맞추고,
  없으면 글자 수로 길이를 어림한다 (줄당 0.125초×글자 + 0.3초).
장면 표 SCENES 의 (첫 줄, 끝 줄, 클립 목록)만 고치면 다시 만들 수 있다.
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
SRC = "C:/Users/user/Desktop/유튜브/영상/2편 소스"
OUT = "C:/Users/user/Desktop/유튜브/영상/2편_편집"
TMP = f"{OUT}/_clips"
NAR = sys.argv[1] if len(sys.argv) > 1 else None
W, H, FPS = 1920, 1080, 30
HL = "0xFFC83D"                                   # 요청 강조색 (1편과 같음)
ENC = ["-an", "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS)]
FONT = "fontfile='C\\:/Windows/Fonts/malgunbd.ttf'"
for d in (OUT, TMP): os.makedirs(d, exist_ok=True)

D = lambda n: f"{SRC}/디빌 언리얼 개발 과정_{n}.{'mp4' if n in (6, 9, 10) else 'mkv'}"
P1, P2, ST = f"{SRC}/디빌 언리얼 플레이 장면_1.mkv", f"{SRC}/디빌 언리얼 플레이 장면_2.mkv", f"{SRC}/스팀웍스 등록 과정.mkv"
K = 1.6                                           # 1600x900 캡처에서 잰 좌표 → 원본 2560x1440
k = lambda *v: tuple(int(x * K) for x in v)

# 스팀웍스 화면의 계정 이름(인사말, 오른쪽 위)은 가린다
ST_BLUR = [k(440, 185, 800, 245), k(1280, 38, 1410, 90)]
BOARD = (640, 330, 1600, 900)                     # 플레이 화면에서 판 부분 (x, y, w, h)
BOARD_NEAR = (1000, 450, 1120, 630)
D12_BOARD = (640, 300, 1600, 900)

# 클립: ("v", 소스, 시작초, 소스길이, 가중치, 옵션)  재생 속도는 장면 길이에 맞춰 자동
#       ("z", 소스, 시각, 강조박스(원본좌표), 가중치, 옵션)  정지 화면 확대 (+노란 테두리)
#       ("c", 카드이름, 가중치)
SCENES = [
    (1, 1, [("v", P1, 60, 50, 1, {})]),
    (2, 2, [("v", P2, 3, 6, 1, {}), ("v", P2, 216, 24, 1.5, {})]),
    (3, 3, [("z", ST, 62, None, 1, {"blur": ST_BLUR})]),
    (4, 5, [("z", ST, 62, k(360, 335, 1240, 470), 1, {"blur": ST_BLUR})]),
    (6, 7, [("v", P2, 48, 82, 1, {})]),
    (8, 8, [("z", D(2), 862, k(573, 662, 1145, 705), 1, {})]),
    (9, 9, [("v", D(2), 1290, 70, 1, {})]),
    (10, 10, [("z", D(3), 30, k(569, 493, 1145, 627), 1, {}), ("v", D(3), 750, 28, 1, {"crop": (90, 101, 2380, 1338)})]),
    (11, 11, [("z", D(11), 117, k(567, 605, 1145, 671), 1, {})]),
    (12, 12, [("v", D(11), 130, 170, 1, {})]),
    (13, 14, [("v", P2, 132, 18, 1, {"crop": BOARD})]),
    (15, 15, [("v", D(12), 990, 20, 1, {"crop": D12_BOARD})]),
    (16, 16, [("v", D(12), 900, 60, 1, {"crop": D12_BOARD})]),
    (17, 19, [("v", D(11), 1920, 12, 1, {"crop": (280, 0, 2000, 1125)})]),
    (20, 21, [("v", P2, 150, 12, 1, {"crop": BOARD})]),
    (22, 22, [("z", D(6), 870, k(614, 68, 1049, 315), 1, {"hl": False})]),
    (23, 23, [("v", P2, 165, 8, 1, {"crop": BOARD})]),
    (24, 24, [("v", P2, 160, 10, 1, {"crop": BOARD_NEAR})]),
    (25, 25, [("v", P2, 216, 10, 1, {})]),
    (26, 26, [("v", P2, 200, 8, 1, {"crop": BOARD_NEAR})]),
    (27, 27, [("v", P2, 72, 18, 1, {})]),
    (28, 30, [("c", "seat", 1)]),
    (31, 31, [("v", P2, 78, 6, 1, {})]),
    (32, 34, [("c", "opener", 1)]),
    (35, 36, [("v", P2, 105, 15, 1, {})]),
    (37, 38, [("c", "meeple", 1)]),
    (39, 39, [("z", P2, 18, (960, 415, 1630, 1120), 1, {"hl": False})]),
    (40, 41, [("c", "hard", 1)]),
    (42, 43, [("v", P2, 3, 8, 1, {})]),
    (44, 44, [("v", P2, 33, 3, 1, {})]),
    (45, 45, [("v", P2, 39, 7, 1, {})]),
    (46, 46, [("v", P2, 12, 14, 1, {})]),
    (47, 47, [("v", P2, 180, 20, 1, {})]),
    (48, 48, [("z", ST, 62, None, 1, {"blur": ST_BLUR})]),
    (49, 51, [("z", ST, 62, k(360, 335, 1240, 470), 1, {"blur": ST_BLUR})]),
    (52, 52, [("z", ST, 18, k(490, 318, 1092, 382), 1, {})]),
    (53, 54, [("z", ST, 18, k(490, 608, 1092, 698), 1, {})]),
    (55, 57, [("z", ST, 18, k(526, 388, 1088, 430), 1, {})]),
    (58, 60, [("v", P2, 226, 20, 2, {}), ("v", P2, 246, 4, 1, {})]),
]

# ---------------- 줄 길이 ----------------
LINES = json.load(open(f"{HERE}/lines.json", encoding="utf-8"))
fname = lambda l: re.sub(r'[\\/:*?"<>|]', "", l).strip()

def probe(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def line_len(i):
    if NAR:
        for suf in ("", "_Modi"):
            p = f"{NAR}/{fname(LINES[i])}{suf}.mp3"
            if os.path.exists(p): return probe(p) + 0.25
    return 0.125 * len(LINES[i]) + 0.3          # shortcut: 어림치. 나레이션이 나오면 폴더를 줘서 다시 맞춘다

DUR = [line_len(i) for i in range(len(LINES))]
covered = [n for a, b, _ in SCENES for n in range(a, b + 1)]
assert covered == list(range(1, len(LINES) + 1)), "장면 표가 대본 줄을 빠짐없이 차례로 덮어야 합니다"

# ---------------- 카드 ----------------
BG, CARD, INK, SUB, ACC, LINE = (11, 58, 46), (247, 244, 233), (28, 32, 30), (110, 116, 110), (232, 120, 40), (222, 216, 200)
NS = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\NanumSquare")
F = lambda s, b=True: ImageFont.truetype(NS + ("EB.ttf" if b else "R.ttf"), s)

def bars(name, title, sub, labels, vals, ref=None, ref_label="", hi=None, unit="%"):
    im = Image.new("RGB", (W, H), BG); g = ImageDraw.Draw(im)
    g.rounded_rectangle((160, 90, W - 160, H - 90), 36, fill=CARD)
    g.text((240, 150), title, font=F(64), fill=INK); g.text((240, 240), sub, font=F(36, False), fill=SUB)
    x0, base, top = 300, 900, 360; bw, gap = 220, (W - 600 - 220 * len(vals)) // max(1, len(vals) - 1)
    vmax = max(vals + ([ref] if ref else [])) * 1.15
    y = lambda v: base - (base - top) * v / vmax
    for i, (lab, v) in enumerate(zip(labels, vals)):
        x = x0 + i * (bw + gap); c = ACC if i == hi else (150, 160, 150)
        g.rectangle((x, y(v), x + bw, base), fill=c)
        t = f"{v:g}{unit}"; g.text((x + bw / 2, y(v) - 14), t, font=F(48), fill=INK, anchor="md")
        g.text((x + bw / 2, base + 20), lab, font=F(38), fill=INK, anchor="ma")
    g.line((260, base, W - 260, base), fill=LINE, width=4)
    if ref:
        for xx in range(260, W - 260, 40): g.line((xx, y(ref), xx + 22, y(ref)), fill=INK, width=4)
        g.text((W - 260, y(ref) - 12), ref_label, font=F(32), fill=INK, anchor="rd")
    p = f"{TMP}/card_{name}.png"; im.save(p); return p

def text_card(name, title, rows):
    im = Image.new("RGB", (W, H), BG); g = ImageDraw.Draw(im)
    g.rounded_rectangle((160, 90, W - 160, H - 90), 36, fill=CARD)
    g.text((W / 2, 300), title, font=F(64), fill=INK, anchor="mm")
    for i, (lab, val, c) in enumerate(rows):
        yy = 520 + i * 170
        g.text((W / 2 - 40, yy), lab, font=F(56, False), fill=SUB, anchor="rm")
        g.text((W / 2 + 40, yy), val, font=F(72), fill=c, anchor="lm")
    p = f"{TMP}/card_{name}.png"; im.save(p); return p

CARDS = {   # 수치 출처: 언리얼 저장소 Docs/TurnOrderBalance.md, AIDesign.md
    "seat": lambda: bars("seat", "4인전 차례별 우승률", "설정마다 5,000판 시뮬레이션 (보통 AI)",
                         ["1번", "2번", "3번", "4번"], [21.2, 22.7, 30.5, 25.6], 25, "공정 25%", hi=2),
    "opener": lambda: bars("opener", "시민 경매, 누가 가져갔나", "경매를 연 사람 기준 (4인 기본)",
                           ["연 사람", "다음", "그다음", "마지막"], [7, 12, 35, 46], hi=3),
    "meeple": lambda: text_card("meeple", "시민 미플 개수", [("룰북", "4개", INK), ("게임", "5개 → 4개", ACC)]),
    "hard": lambda: bars("hard", "어려움 AI 1 vs 보통 AI 3", "4인전 우승률",
                         ["어려움 AI", "보통 AI (평균)"], [36, 21.3], 25, "공정 25%", hi=0),
}

# ---------------- 렌더 ----------------
def ff(args, out):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args, *ENC, out], capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode: sys.exit(f"FAIL {out}\n{r.stderr}")
    return out

def pre(opt):
    """블러 → 크롭 → 1920x1080. 좌표는 원본 2560x1440 기준."""
    f, n = "[0:v]", 0
    chain = []
    for (x0, y0, x1, y1) in opt.get("blur", []):
        chain.append(f"{f}split[m{n}][b{n}];[b{n}]crop={x1-x0}:{y1-y0}:{x0}:{y0},boxblur=10:5[bb{n}];[m{n}][bb{n}]overlay={x0}:{y0}[o{n}]")
        f = f"[o{n}]"; n += 1
    c = opt.get("crop")
    tail = (f"crop={c[2]}:{c[3]}:{c[0]}:{c[1]}," if c else "") + f"scale={W}:{H}:flags=lanczos,setsar=1"
    return chain, f, tail

def vclip(src, ss, sdur, out_t, opt, out):
    chain, f, tail = pre(opt)
    fc = ";".join(chain + [f"{f}{tail},setpts=PTS*{out_t / sdur:.5f},fps={FPS},trim=0:{out_t:.3f},setpts=PTS-STARTPTS[v]"])
    return ff(["-ss", str(ss), "-t", str(sdur), "-i", src, "-filter_complex", fc, "-map", "[v]", "-t", f"{out_t:.3f}"], out)

def zclip(src, t, box, out_t, opt, out):
    """정지 화면. box가 있으면 그 둘레를 16:9로 확대하고 (hl이면) 노란 테두리, 천천히 살짝 다가간다."""
    chain, f, _ = pre({"blur": opt.get("blur", [])})
    if box:
        x0, y0, x1, y1 = box
        w = max(int((x1 - x0) * 1.3), 900); w -= w % 2; h = int(w * 9 / 16); h -= h % 2
        if h < (y1 - y0) * 1.3: h = int((y1 - y0) * 1.3) // 2 * 2; w = int(h * 16 / 9) // 2 * 2
        cx = int(min(max((x0 + x1) / 2 - w / 2, 0), 2560 - w)); cy = int(min(max((y0 + y1) / 2 - h / 2, 0), 1440 - h))
        s = W / w; pad = 14
        crop = f"crop={w}:{h}:{cx}:{cy},scale={W}:{H}:flags=lanczos,setsar=1"
        if opt.get("hl", True):
            crop += (f",drawbox=x={int((x0 - pad - cx) * s)}:y={int((y0 - pad - cy) * s)}:"
                     f"w={int((x1 - x0 + 2 * pad) * s)}:h={int((y1 - y0 + 2 * pad) * s)}:color={HL}:t=9")
    else:
        crop = f"scale={W}:{H}:flags=lanczos,setsar=1"
    n = int(out_t * FPS) + 1
    zoom = f"scale={W*2}:{H*2},zoompan=z='1+0.04*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={n}:s={W}x{H}:fps={FPS}"
    fc = ";".join(chain + [f"{f}{crop},trim=end_frame=1,{zoom}[v]"])
    return ff(["-ss", str(t), "-i", src, "-filter_complex", fc, "-map", "[v]", "-t", f"{out_t:.3f}"], out)

def cclip(png, out_t, out):
    n = int(out_t * FPS) + 1
    return ff(["-loop", "1", "-t", f"{out_t:.3f}", "-i", png, "-vf",
               f"scale={W*2}:{H*2},zoompan=z='1+0.03*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={n}:s={W}x{H}:fps={FPS}",
               "-t", f"{out_t:.3f}"], out)

parts, cues, t = [], [], 0.0
for si, (a, b, clips) in enumerate(SCENES):
    T = sum(DUR[a - 1:b])
    for n in range(a, b + 1):
        cues.append((t, t + DUR[n - 1] - 0.1, LINES[n - 1])); t += DUR[n - 1]
    wsum = sum(c[-2] if c[0] != "c" else c[-1] for c in clips)
    for ci, c in enumerate(clips):
        out = f"{TMP}/s{si:02d}_{ci}.mp4"
        if c[0] == "v": _, src, ss, sd, w, opt = c; vclip(src, ss, sd, T * w / wsum, opt, out)
        elif c[0] == "z": _, src, tt, box, w, opt = c; zclip(src, tt, box, T * w / wsum, opt, out)
        else: _, name, w = c; cclip(CARDS[name](), T * w / wsum, out)
        parts.append(out)
    print(f"장면 {a}-{b}: {T:.1f}s", flush=True)

with open(f"{TMP}/list.txt", "w", encoding="utf-8") as f:
    f.writelines(f"file '{p}'\n" for p in parts)
CLEAN = f"{OUT}/2편_편집_자막없음.mp4"
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{TMP}/list.txt", "-c", "copy", CLEAN])
assert r.returncode == 0

# ---------------- 자막 (SRT + 번인 미리보기) ----------------
st = lambda x: f"{int(x//3600):02d}:{int(x//60%60):02d}:{int(x%60):02d},{int(round(x%1*1000))%1000:03d}"
with open(f"{OUT}/2편_편집.srt", "w", encoding="utf-8") as f:
    for i, (a, b, l) in enumerate(cues): f.write(f"{i+1}\n{st(a)} --> {st(b)}\n{l}\n\n")
SUBDIR = "C:/Users/user/AppData/Local/Temp/dv_ep2_subs"; os.makedirs(SUBDIR, exist_ok=True)   # drawtext는 한글 경로를 못 읽음
vf = []
for i, (a, b, l) in enumerate(cues):
    p = f"{SUBDIR}/{i}.txt"; open(p, "w", encoding="utf-8").write(l)
    vf.append(f"drawtext={FONT}:expansion=none:textfile='{p.replace(':', chr(92) + ':')}':fontsize=54:fontcolor=white:borderw=4:bordercolor=black@0.9:"
              f"box=1:boxcolor=black@0.5:boxborderw=20:x=(w-text_w)/2:y=h-text_h-66:enable='between(t,{a:.2f},{b:.2f})'")
ff(["-i", CLEAN, "-vf", ",".join(vf)], f"{OUT}/2편_편집_자막미리보기.mp4")
print(f"총 {t:.1f}s, 클린 {probe(CLEAN):.1f}s")
