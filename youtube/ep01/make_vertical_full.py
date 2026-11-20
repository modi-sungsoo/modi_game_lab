"""Modi 최종본에서 핵심 구간만 골라 9:16(1080x1920) 쇼츠·릴스용 세로 영상을 만든다.
화면: 흐린 배경 + 가운데 16:9 본편 + 위 제목 + 아래 큰 자막(긴 문장은 두 줄)."""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
VID = "C:/Users/user/Desktop/유튜브/영상/1. AI 딸깍 게임에 재미는 어떻게 입힐까요"
BODY = f"{HERE}/modi_tmp/body.mp4"                    # 자막 없는 Modi 본편 화면
FULL = f"{VID}/1편_최종본_Modi_1080p_썸네일포함.mp4"
OFF = 1 / 30              # 소리(나레이션+BGM+효과음)
SRT = f"{VID}/1편_최종본_Modi_1080p_썸네일포함.srt"
OUT = f"{VID}/1편_전체_세로_Modi_1080x1920"
PICK = [(1, 6), (15, 16), (28, 32), (46, 48), (54, 54)]   # 쓸 자막 번호 구간
FONT = "fontfile='C\\:/Windows/Fonts/malgunbd.ttf'"
TD = f"{HERE}/vfull_txt"; os.makedirs(TD, exist_ok=True)

def t2s(t):
    h, m, s = t.replace(",", ".").split(":"); return int(h) * 3600 + int(m) * 60 + float(s)
cues = [(int(n), t2s(a), t2s(b), x) for n, a, b, x in re.findall(r"(\d+)\n(\S+) --> (\S+)\n(.+?)\n", open(SRT, encoding="utf-8").read())]
by = {n: (a, b, x) for n, a, b, x in cues}

def wrap(t, n=17):   # 두 줄로 고르게 나뉘면 그대로, 안 되면 n자씩 채워 세 줄
    if len(t) <= n: return [t]
    sp = [i for i, ch in enumerate(t) if ch == " "]
    k = min(sp, key=lambda i: abs(i - len(t) / 2))
    if max(k, len(t) - k - 1) <= n: return [t[:k], t[k + 1:]]
    out = []
    for x in t.split(" "):
        if out and len(out[-1]) + 1 + len(x) <= n: out[-1] += " " + x
        else: out.append(x)
    return out

END = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", BODY])) + OFF
segs = [(OFF, END)]
subs = [(ca - OFF, cb - OFF, x) for n, ca, cb, x in cues]
o = END - OFF
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
fc.append("[fgs]scale=1080:608:flags=lanczos[fg]")
d = ["[bg][fg]overlay=0:640"]
# 위 제목 두 줄
d.append(f"drawtext={FONT}:textfile='{txt('t1','AI 딸깍 게임에')}':fontsize=76:fontcolor=white:box=1:boxcolor=black@0.85:boxborderw=22:x=(w-text_w)/2:y=380")
d.append(f"drawtext={FONT}:textfile='{txt('t2','재미는 어떻게 입힐까?')}':fontsize=76:fontcolor=black:box=1:boxcolor=0xFFC83D:boxborderw=22:x=(w-text_w)/2:y=510")
# 아래 자막 (줄마다 가운데 정렬)
for i, (a, b, x) in enumerate(subs):
    lines = wrap(x)
    for j, ln in enumerate(lines):
        y = 1300 + j * 90
        d.append(f"drawtext={FONT}:textfile='{txt(f's{i}_{j}', ln)}':fontsize=60:fontcolor=white:borderw=5:bordercolor=black:"
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
