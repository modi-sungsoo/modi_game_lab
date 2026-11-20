"""Modi 최종본에서 핵심 구간만 골라 9:16(1080x1920) 쇼츠·릴스용 세로 영상을 만든다.
화면: 흐린 배경 + 가운데 16:9 본편 + 위 제목 + 아래 큰 자막(긴 문장은 두 줄)."""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
VID = "C:/Users/user/Videos"
BODY = f"{HERE}/modi_tmp/body.mp4"                    # 자막 없는 Modi 본편 화면
FULL = f"{VID}/1편_최종본_Modi_1080p_썸네일포함.mp4"
OFF = 1 / 30   # 썸네일포함 버전은 맨 앞 1프레임만큼 밀려 있음 (BODY는 안 밀림)              # 소리(나레이션+BGM+효과음)
SRT = f"{VID}/1편_최종본_Modi_1080p_썸네일포함.srt"
OUT = f"{VID}/1편_쇼츠_릴스_하이라이트_Modi_1080x1920"
PICK = [(1, 1), (4, 4), (5, 6), (16, 16), (31, 31), (55, 56)]   # 맨앞 훅 → 결과 → 3시간 → 메시지 2개 → 맨뒤   # 쓸 자막 번호 구간
FONT = "fontfile='C\\:/Windows/Fonts/malgunbd.ttf'"
TD = f"{HERE}/shorts_hl_txt"; os.makedirs(TD, exist_ok=True)

def t2s(t):
    h, m, s = t.replace(",", ".").split(":"); return int(h) * 3600 + int(m) * 60 + float(s)
cues = [(int(n), t2s(a), t2s(b), x) for n, a, b, x in re.findall(r"(\d+)\n(\S+) --> (\S+)\n(.+?)\n", open(SRT, encoding="utf-8").read())]
by = {n: (a, b, x) for n, a, b, x in cues}

def wrap(t, n=16):   # 긴 자막은 가운데 가까운 띄어쓰기에서 두 줄로
    if len(t) <= n: return [t]
    sp = [i for i, ch in enumerate(t) if ch == " "]
    k = min(sp, key=lambda i: abs(i - len(t) / 2))
    return [t[:k], t[k + 1:]]

segs, subs, o = [], [], 0.0
for s, e in PICK:
    a, b = by[s][0], by[e][1]
    segs.append((a, b))
    for n in range(s, e + 1):
        ca, cb, x = by[n]; subs.append((o + ca - a, o + cb - a, x))
    o += b - a
total = o

def txt(name, s):
    p = f"{TD}/{name}.txt"; open(p, "w", encoding="utf-8").write(s); return p.replace(":", "\\:")
fc = []
for i, (a, b) in enumerate(segs):
    fc.append(f"[0:v]trim={a - OFF:.3f}:{b - OFF:.3f},setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[1:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.06,afade=t=out:st={b - a - 0.08:.3f}:d=0.08[a{i}]")
n = len(segs)
fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]")
fc.append("[cv]split[bgs][fgs]")
fc.append("[bgs]scale=-2:1920,crop=1080:1920,boxblur=24:2,eq=brightness=-0.18[bg]")
fc.append("[fgs]scale=1458:820:flags=lanczos,crop=1080:820[fg]")   # 1.35배 확대해 세로 화면을 더 채움 (좌우 13%씩 잘림)
d = ["[bg][fg]overlay=0:430"]
# 위 제목 두 줄
d.append(f"drawtext={FONT}:textfile='{txt('t1','AI 딸깍 게임에')}':fontsize=76:fontcolor=white:box=1:boxcolor=black@0.85:boxborderw=22:x=(w-text_w)/2:y=180")
d.append(f"drawtext={FONT}:textfile='{txt('t2','재미는 어떻게 입힐까?')}':fontsize=76:fontcolor=black:box=1:boxcolor=0xFFC83D:boxborderw=22:x=(w-text_w)/2:y=310")
# 확대로 잘린 원래 라벨을 덮어 새로 그림 (세그먼트 시작 시각 기준)
seg_t, acc2 = [], 0.0
for (sa, sb) in segs: seg_t.append(acc2); acc2 += sb - sa
for text, t0, t1 in [("명령어 1번", seg_t[0], seg_t[2]), ("재미 3시간", seg_t[2], seg_t[3])]:
    d.append(f"drawtext={FONT}:textfile='{txt('lab' + str(int(t0)), text)}':fontsize=56:fontcolor=black:box=1:boxcolor=0xFFC83D:boxborderw=30:"
             f"x=28:y=464:enable='between(t,{t0:.3f},{t1 - 0.02:.3f})'")
# 아래 자막 (줄마다 가운데 정렬)
for i, (a, b, x) in enumerate(subs):
    lines = wrap(x)
    for j, ln in enumerate(lines):
        y = 1290 + j * 96
        d.append(f"drawtext={FONT}:textfile='{txt(f's{i}_{j}', ln)}':fontsize=64:fontcolor=white:borderw=5:bordercolor=black:"
                 f"box=1:boxcolor=black@0.55:boxborderw=16:x=(w-text_w)/2:y={y}:enable='between(t,{a:.3f},{b - 0.02:.3f})'")
fc.append(",".join(d) + ",format=yuv420p[vout]")
open(f"{TD}/fc.txt", "w", encoding="utf-8").write(";\n".join(fc))
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", BODY, "-i", FULL, "-/filter_complex", f"{TD}/fc.txt",
                    "-map", "[vout]", "-map", "[ca]", "-r", "30", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", f"{OUT}.mp4"],
                   capture_output=True, encoding="utf-8", errors="replace")
if r.returncode: sys.exit("\n".join(l for l in r.stderr.splitlines() if "Fontconfig" not in l))
def s2t(x):
    ms = int(round(x * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
open(f"{OUT}.srt", "w", encoding="utf-8").write("\n".join(f"{i+1}\n{s2t(a)} --> {s2t(b)}\n{x}\n" for i, (a, b, x) in enumerate(subs)))
d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{OUT}.mp4"]))
print(f"{len(subs)}줄, 계획 {total:.2f}s, 결과 {d:.2f}s")
