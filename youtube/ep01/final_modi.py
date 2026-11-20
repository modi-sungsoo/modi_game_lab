"""Vrew 편집 화면은 그대로 두고, 나레이션만 ModiSungSoo 목소리로 바꾼 최종본을 만든다.
클립마다 Modi 문장이 원래 문장보다 길면 그 클립 끝 화면을 멈춰 길이를 늘린다(다음 문장과 최소 GAP 간격).
사용: python final_modi.py 배경음악.wav
"""
import json, os, re, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
VID = "C:/Users/user/Videos"
SRC = f"{VID}/1편_합본_1080p_나레이션_자막없음.mp4"
VREW = f"{VID}/1편_나레이션/1편_합본_1080p_나레이션_자막없음.vrew1편_나레이션_최종.vrew"
MODI = "C:/Users/user/Desktop/유튜브/나레이션/1. AI에게 보드게임 룰북만 줬더니 명령어 하나로 게임이 됐습니다/ModiSungSoo 나레이션"
SFX = "C:/Users/user/Desktop/유튜브/효과음/1편"
OUT = f"{VID}/1편_최종본_Modi_1080p"
BGM = sys.argv[1]
TMP = f"{HERE}/modi_tmp"; os.makedirs(TMP, exist_ok=True)
FONT = "fontfile='C\\:/Windows/Fonts/malgunbd.ttf'"
GAP = 0.35

def run(args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode: sys.exit("\n".join(l for l in r.stderr.splitlines() if "Fontconfig" not in l))
def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
def speech_len(p):   # 끝 무음을 뺀 실제 말 길이
    d = dur(p)
    err = subprocess.run(["ffmpeg", "-i", p, "-af", "silencedetect=n=-40dB:d=0.1", "-f", "null", "-"], capture_output=True, encoding="utf-8", errors="replace").stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    lead = en[0] if st and st[0] < 0.02 and en else 0.0            # 앞 무음
    # 끝 무음: 마지막 무음이 파일 끝까지 이어질 때만 (문장 중간 쉼을 끝으로 보지 않게)
    end = st[-1] if st and (len(en) < len(st) or en[-1] > d - 0.03) and st[-1] > lead else d
    return lead, end

# ---- Vrew 타임라인 ----
p = json.loads(zipfile.ZipFile(VREW).read("project.json"))
A, T = p["props"]["assets"], p["props"]["tracks"]
segs, clips, out_t = [], [], 0.0
for c in p["transcript"]["clips"]:
    c_start, fs = out_t, None
    for w in c["words"]:
        if fs is None and w["type"] == 0: fs = out_t
        for a in w["assetIds"]:
            if A[a].get("role") != "main": continue
            for tid in A[a]["trackIds"]:
                t = T[tid]
                if t["type"] == "video":
                    segs.append([t["sourceIn"], t["sourceOut"]]); out_t += t["sourceOut"] - t["sourceIn"]
    cap = "".join(x.get("insert", "") for x in c["captions"][0]["text"]).strip() or " ".join(w["text"] for w in c["words"] if w["text"]).strip()
    clips.append(dict(a=c_start, b=out_t, fs=(fs if fs is not None else c_start) - c_start, cap=cap))
merged = []
for a, b in segs:
    if merged and abs(a - merged[-1][1]) < 0.02: merged[-1][1] = b
    else: merged.append([a, b])
outs, acc = [], 0.0
for a, b in merged: outs.append(acc); acc += b - a
def src2vrew(t):
    for (a, b), o in zip(merged, outs):
        if a - 1e-3 <= t <= b: return o + (t - a)
    return None

# ---- 클립별 새 길이 ----
for c in clips:
    c["mp3"] = f"{MODI}/" + re.sub(r'[\\/:*?"<>|]', "", c["cap"]).strip() + "_Modi.mp3"
    assert os.path.exists(c["mp3"]), c["mp3"]
    c["lead"], c["end"] = speech_len(c["mp3"]); c["sp"] = c["end"] - c["lead"]
# 문장이 다음 클립으로 이어지면(마침표·물음표·느낌표로 끝나지 않으면) 사이를 촘촘히 붙인다.
cont = lambda c: not re.search(r"[.?!]$", c["cap"])
TIGHT, MAX_CUT = 0.12, 1.2
for i, c in enumerate(clips):
    if i > 0 and cont(clips[i - 1]): c["fs"] = 0.03
new_t = 0.0
for i, c in enumerate(clips):
    L = c["b"] - c["a"]
    nxt = clips[i + 1]["fs"] if i + 1 < len(clips) else 0.0
    if i + 1 < len(clips) and cont(c):     # 화면 끝을 잘라서라도 붙임 (최대 MAX_CUT초)
        c["L"] = max(L - MAX_CUT, c["fs"] + c["sp"] + TIGHT - nxt, c["fs"] + c["sp"] + 0.05)
    else:
        c["L"] = max(L, c["fs"] + c["sp"] + GAP - nxt, c["fs"] + c["sp"] + 0.2)
    c["na"] = new_t; new_t += c["L"]
total = new_t
def vrew2new(t):
    for c in clips:
        if c["a"] - 1e-6 <= t < c["b"]: return c["na"] + min(t - c["a"], c["L"] - 0.05)
    return None

# ---- 1) Vrew대로 자른 화면 ----
cut = f"{TMP}/cut.mp4"
sel = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in merged)
run(["-i", SRC, "-vf", f"select='{sel}',setpts=N/30/TB,format=yuv420p", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", cut])
# ---- 2) 클립마다 잘라서 필요한 만큼 끝 화면 정지 ----
lst = []
for i, c in enumerate(clips):
    f = f"{TMP}/c{i:02d}.mp4"; L0 = c["b"] - c["a"]
    run(["-ss", f"{c['a']:.3f}", "-t", f"{L0:.3f}", "-i", cut, "-vf", f"tpad=stop_mode=clone:stop_duration={max(0.0, c['L'] - L0) + 0.1:.3f},trim=0:{c['L']:.3f},setpts=PTS-STARTPTS,fps=30",
         "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", f])
    lst.append(f"file '{f}'\n")
open(f"{TMP}/list.txt", "w", encoding="utf-8").write("".join(lst))
body = f"{TMP}/body.mp4"
run(["-f", "concat", "-safe", "0", "-i", f"{TMP}/list.txt", "-c", "copy", body])
# 프레임 단위로 반올림된 실제 클립 길이로 시각을 다시 계산 (자막·소리가 뒤로 갈수록 밀리지 않게)
new_t = 0.0
for i, c in enumerate(clips):
    c["L"] = dur(f"{TMP}/c{i:02d}.mp4"); c["na"] = new_t; new_t += c["L"]
total = new_t

# ---- 3) 효과음 (원본 → Vrew → 새 타임라인) ----
ORDER = [("웹_01", 16.82), ("웹_02", 12.2), ("웹_03", 38.4), ("웹_06", 18.233), ("웹_09", 35.067), ("웹_04", 16.267),
         ("웹_08", 11.1), ("웹_05", 16.467), ("웹_07", 14.0), ("정산", 15.8), ("언리얼_02", 31.5)]
off, o = {}, 0.0
for n, d in ORDER: off[n] = o; o += d
sys.argv = [sys.argv[0]]
cues = [("웹_01", 0.3, "02_타이핑.wav", 0.25), ("웹_01", 4.5, "03_팝_클릭.wav", 0.5), ("웹_01", 7.9, "01_엔터키_A.wav", 0.7),
    ("웹_01", 8.1, "05_휙_빨리감기.wav", 0.35), ("웹_02", 0.05, "05_휙_빨리감기.wav", 0.35), ("웹_02", 2.5, "03_팝_클릭.wav", 0.5),
    ("웹_02", 5.3, "03_팝_클릭.wav", 0.5), ("웹_02", 9.1, "03_팝_클릭.wav", 0.5), ("웹_03", 0.0, "04_휙_부드럽게.wav", 0.35),
    ("웹_06", 0.0, "03_팝_클릭.wav", 0.5), ("웹_06", 2.4, "03_팝_클릭.wav", 0.5), ("웹_06", 4.8, "08_카드_등장.wav", 0.4), ("웹_06", 10.8, "03_팝_클릭.wav", 0.5),
    ("웹_09", 0.0, "03_팝_클릭.wav", 0.5), ("웹_09", 2.4, "08_카드_등장.wav", 0.4), ("웹_09", 13.0, "03_팝_클릭.wav", 0.5),
    ("웹_09", 15.4, "08_카드_등장.wav", 0.4), ("웹_09", 20.4, "03_팝_클릭.wav", 0.5), ("웹_09", 25.9, "05_휙_빨리감기.wav", 0.3),
    ("웹_04", 0.0, "08_카드_등장.wav", 0.4), ("웹_08", 0.0, "03_팝_클릭.wav", 0.5), ("웹_08", 2.6, "05_휙_빨리감기.wav", 0.3),
    ("웹_08", 7.6, "08_카드_등장.wav", 0.4), ("웹_05", 0.0, "04_휙_부드럽게.wav", 0.35), ("웹_07", 2.0, "08_카드_등장.wav", 0.4),
    ("정산", 0.0, "08_카드_등장.wav", 0.4), ("정산", 4.4, "06_성공_알림.wav", 0.45), ("정산", 9.0, "06_성공_알림.wav", 0.45),
    ("언리얼_02", 0.0, "04_휙_부드럽게.wav", 0.35), ("언리얼_02", 6.0, "05_휙_빨리감기.wav", 0.3)] + \
    [("언리얼_02", 12.8 + 0.25 * i, "07_타일_팝.wav", 0.35) for i in range(12)]
placed = []
for clip, t, f, v in cues:
    vt = src2vrew(off[clip] + t)
    nt = vrew2new(vt) if vt is not None else None
    if nt is not None: placed.append((nt, f, v))

# ---- 4) 자막 + 소리 합치기 ----
os.makedirs(f"{TMP}/subs", exist_ok=True)
def s2t(x):
    ms = int(round(x * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
draws, srt = [], []
for i, c in enumerate(clips):
    tf = f"{TMP}/subs/c{i}.txt"; open(tf, "w", encoding="utf-8").write(c["cap"])
    a, b = c["na"], c["na"] + c["L"]
    draws.append(f"drawtext={FONT}:textfile='{tf.replace(':', chr(92) + ':')}':fontsize=54:fontcolor=white:borderw=4:bordercolor=black@0.9:"
                 f"box=1:boxcolor=black@0.5:boxborderw=21:x=(w-text_w)/2:y=h-text_h-66:enable='between(t,{a:.3f},{b - 0.02:.3f})'")
    srt.append(f"{i+1}\n{s2t(a)} --> {s2t(b)}\n{c['cap']}\n")
ins = ["-i", body]; fc = [f"[0:v]{','.join(draws)}[vout]"]; nar, sfx = [], []
for c in clips:
    ins += ["-i", c["mp3"]]; k = len(ins) // 2 - 1; d = int((c["na"] + c["fs"]) * 1000)
    fc.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim={c['lead']:.3f}:{c['end'] + 0.08:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={c['sp'] - 0.02:.3f}:d=0.1,adelay={d}|{d}[n{k}]"); nar.append(f"[n{k}]")
for nt, f, v in placed:
    ins += ["-i", f"{SFX}/{f}"]; k = len(ins) // 2 - 1; d = int(nt * 1000)
    fc.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,volume={v},adelay={d}|{d}[s{k}]"); sfx.append(f"[s{k}]")
b0 = len(ins) // 2; ins += ["-i", BGM] * 1 + ["-i", BGM, "-i", BGM, "-i", BGM]
fc.append("".join(nar) + f"amix=inputs={len(nar)}:normalize=0,asplit[narA][narK]")
fc.append("".join(sfx) + f"amix=inputs={len(sfx)}:normalize=0[sfx]")
fc.append("".join(f"[{b0+k}:a]aresample=48000,aformat=channel_layouts=stereo[b{k}];" for k in range(4)) +
          f"[b0][b1]acrossfade=d=3[x1];[x1][b2]acrossfade=d=3[x2];[x2][b3]acrossfade=d=3,volume=0.22,atrim=0:{total:.3f},"
          f"afade=t=in:d=1.5,afade=t=out:st={total-3:.3f}:d=3[bgm0]")
fc.append("[bgm0][narK]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[bgm]")
fc.append("[narA][sfx][bgm]amix=inputs=3:normalize=0,alimiter=limit=0.95[aout]")
open(f"{TMP}/fc.txt", "w", encoding="utf-8").write(";\n".join(fc))
run([*ins, "-/filter_complex", f"{TMP}/fc.txt", "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.3f}",
     "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", f"{OUT}.mp4"])
open(f"{OUT}.srt", "w", encoding="utf-8").write("\n".join(srt))
ext = [(i + 1, round(c["L"] - (c["b"] - c["a"]), 2)) for i, c in enumerate(clips) if abs(c["L"] - (c["b"] - c["a"])) > 0.01]
print(f"원래 {out_t:.2f}s -> {total:.2f}s ({dur(OUT + '.mp4'):.2f}s), 늘린 클립 {len(ext)}개: {ext}, 효과음 {len(placed)}")
