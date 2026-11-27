"""인스타용: 2편 최종본을 1.25배속(목소리 높이 유지)으로 만들고, 같은 속도의 9:16(1080x1920) 세로 전체본도 만든다.
세로 화면은 1편과 같다: 흐린 배경 + 가운데 16:9 본편(y640) + 위 제목 두 줄(y380/510) + 아래 큰 자막(y1300~).
사용: python make_insta.py
"""
import os, re, subprocess, sys

OUT = "C:/Users/user/Desktop/유튜브/영상/2편_2D 보드게임 3D화"
CLEAN = f"{OUT}/2편_최종본_Modi_1080p_자막없음.mp4"     # 자막 없는 화면 + 최종 오디오
SUBBED = f"{OUT}/2편_최종본_Modi_1080p.mp4"
SRT = f"{OUT}/2편_편집.srt"
TITLE = ("웹게임을 3D로 옮기고", "스팀 등록까지")
SP = 1.25
FONT = "fontfile='C\\:/Windows/Fonts/malgunbd.ttf'"
TD = "C:/Users/user/AppData/Local/Temp/dv_ep2_insta"; os.makedirs(TD, exist_ok=True)   # drawtext는 한글 경로를 못 읽음
ENC = ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "30",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart"]

def run(args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode: sys.exit("\n".join(l for l in r.stderr.splitlines() if "Fontconfig" not in l))

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

t2s = lambda t: (lambda h, m, s: int(h) * 3600 + int(m) * 60 + float(s.replace(",", ".")))(*t.split(":"))
def s2t(x):
    ms = int(round(x * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
cues = [(t2s(a) / SP, t2s(b) / SP, x) for a, b, x in re.findall(r"\d+\n(\S+) --> (\S+)\n(.+?)\n", open(SRT, encoding="utf-8").read())]

def write_srt(p):
    open(p, "w", encoding="utf-8").write("\n".join(f"{i+1}\n{s2t(a)} --> {s2t(b)}\n{x}\n" for i, (a, b, x) in enumerate(cues)))

def wrap(t, n=17):   # 두 줄로 고르게 나뉘면 그대로, 안 되면 n자씩 채운다 (1편과 같음)
    if len(t) <= n: return [t]
    sp = [i for i, ch in enumerate(t) if ch == " "]
    k = min(sp, key=lambda i: abs(i - len(t) / 2))
    if max(k, len(t) - k - 1) <= n: return [t[:k], t[k + 1:]]
    out = []
    for x in t.split(" "):
        if out and len(out[-1]) + 1 + len(x) <= n: out[-1] += " " + x
        else: out.append(x)
    return out

def txt(name, s):
    p = f"{TD}/{name}.txt"; open(p, "w", encoding="utf-8").write(s); return p.replace(":", "\\:")

# 1) 가로 1.25배속
H = f"{OUT}/2편_최종본_Modi_1080p_1.25배속"
run(["-i", SUBBED, "-filter_complex", f"[0:v]setpts=PTS/{SP}[v];[0:a]atempo={SP}[a]", "-map", "[v]", "-map", "[a]", *ENC, f"{H}.mp4"])
write_srt(f"{H}.srt")

# 2) 세로 전체본 1.25배속
V = f"{OUT}/2편_전체_세로_Modi_1080x1920_1.25배속"
d = ["[bg][fg]overlay=0:640",
     f"drawtext={FONT}:textfile='{txt('t1', TITLE[0])}':fontsize=76:fontcolor=white:box=1:boxcolor=black@0.85:boxborderw=22:x=(w-text_w)/2:y=380",
     f"drawtext={FONT}:textfile='{txt('t2', TITLE[1])}':fontsize=76:fontcolor=black:box=1:boxcolor=0xFFC83D:boxborderw=22:x=(w-text_w)/2:y=510"]
for i, (a, b, x) in enumerate(cues):
    for j, ln in enumerate(wrap(x)):
        d.append(f"drawtext={FONT}:expansion=none:textfile='{txt(f's{i}_{j}', ln)}':fontsize=60:fontcolor=white:borderw=5:bordercolor=black:"
                 f"box=1:boxcolor=black@0.55:boxborderw=16:x=(w-text_w)/2:y={1300 + j * 90}:enable='between(t,{a:.3f},{b - 0.02:.3f})'")
fc = [f"[0:v]setpts=PTS/{SP},split[bgs][fgs]",
      "[bgs]scale=-2:1920,crop=1080:1920,boxblur=24:2,eq=brightness=-0.18[bg]",
      "[fgs]scale=1080:608:flags=lanczos[fg]",
      ",".join(d) + "[v]", f"[0:a]atempo={SP}[a]"]
open(f"{TD}/fc.txt", "w", encoding="utf-8").write(";\n".join(fc))
run(["-i", CLEAN, "-/filter_complex", f"{TD}/fc.txt", "-map", "[v]", "-map", "[a]", *ENC, f"{V}.mp4"])
write_srt(f"{V}.srt")

for p in (SUBBED, f"{H}.mp4", f"{V}.mp4"): print(f"{dur(p):.2f}s  {p}")
assert abs(dur(f"{H}.mp4") - dur(SUBBED) / SP) < 0.2 and abs(dur(f"{V}.mp4") - dur(SUBBED) / SP) < 0.2
