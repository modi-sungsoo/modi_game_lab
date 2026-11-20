"""Vrew 프로젝트의 편집(남긴 구간·자막·2번 클립 교체 음성)대로 원본에서 다시 렌더링하고, 효과음과 (선택) 배경음악을 얹는다.
사용: python final_ep1.py [배경음악.mp3]
Vrew 워터마크 없이 ffmpeg로 직접 만든다.
"""
import json, os, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
VID = "C:/Users/user/Videos"
SRC = f"{VID}/1편_합본_1080p_나레이션_자막없음.mp4"          # Vrew가 불러온 원본 (04:08 버전)
VREW = f"{VID}/1편_나레이션/1편_합본_1080p_나레이션_자막없음.vrew1편_나레이션_최종.vrew"
CLIP2 = "C:/Users/user/Desktop/유튜브/나레이션/1. AI에게 보드게임 룰북만 줬더니 명령어 하나로 게임이 됐습니다/테스트삼아 우선 제가 기획했던 보드게임 룰북으로.mp3"
CLIP2_SPEECH = 3.86   # 원본 속도 녹음에서 말이 끝나는 시각 (뒤는 무음)
GAP_AFTER = 0.35     # 2번 문장 끝과 3번 문장 시작 사이 최소 간격
SFX = "C:/Users/user/Desktop/유튜브/효과음/1편"
OUT = f"{VID}/1편_최종본_1080p"
BGM = sys.argv[1] if len(sys.argv) > 1 else None
FONT = "fontfile='C\\:/Windows/Fonts/malgunbd.ttf'"

# ---- 1. Vrew 타임라인 읽기 ----
p = json.loads(zipfile.ZipFile(VREW).read("project.json"))
A, T = p["props"]["assets"], p["props"]["tracks"]
src_id = next(f["mediaId"] for f in p["files"] if f["name"].endswith("_자막없음.mp4"))
segs, clips, extra_audio, first_speech, out_t = [], [], [], [], 0.0
for c in p["transcript"]["clips"]:
    c_start = out_t; fs = None
    for w in c["words"]:
        if fs is None and w["type"] == 0: fs = out_t
        w_start = out_t
        for a in w["assetIds"]:
            for tid in A[a]["trackIds"]:
                t = T[tid]
                if A[a].get("role") == "main" and t["type"] == "video":
                    assert t["mediaId"] == src_id
                    vol = next((T[x].get("volume", 1) for x in A[a]["trackIds"] if T[x]["type"] == "videoAudio"), 1)
                    segs.append([t["sourceIn"], t["sourceOut"], vol]); out_t += t["sourceOut"] - t["sourceIn"]
                elif A[a].get("role") == "sub" and t["type"] == "soundEffect":
                    extra_audio.append(w_start)        # 이 단어가 시작하는 시점에 얹힌 소리
    cap = "".join(x.get("insert", "") for x in c["captions"][0]["text"]).strip()
    if not cap:   # TRANSCRIPT 모드 클립은 자막이 단어에서 나옴
        cap = " ".join(w["text"] for w in c["words"] if w["text"]).strip()
    clips.append((c_start, out_t, cap)); first_speech.append(fs)
total = out_t
assert len(extra_audio) == 1, extra_audio                # 2번 클립 교체 음성 하나뿐

merged = []
for a, b, v in segs:                                     # 이어지는 구간은 하나로 합침
    if merged and abs(a - merged[-1][1]) < 0.02 and merged[-1][2] == v: merged[-1][1] = b
    else: merged.append([a, b, v])
out_starts, acc = [], 0.0
for a, b, v in merged: out_starts.append(acc); acc += b - a

# 2번 클립 교체 음성이 3번 클립 첫 말과 겹치지 않게, 2번 클립 끝에서 화면을 멈춰 길이를 늘린다.
T2 = clips[1][1]
HOLD = max(0.0, extra_audio[0] + CLIP2_SPEECH + GAP_AFTER - first_speech[2])
shift = lambda t: t + (HOLD if t >= T2 - 1e-6 else 0.0)
clips = [(shift(a) if i > 1 else a, shift(b) if i >= 1 else b, cap) for i, (a, b, cap) in enumerate(clips)]
clips[1] = (clips[1][0], T2 + HOLD, clips[1][2])
total += HOLD

def src2out(t):
    for (a, b, v), o in zip(merged, out_starts):
        if a - 1e-3 <= t <= b: return shift(o + (t - a))
    return None

# ---- 2. 효과음 배치 (원본 시각 기준 → Vrew 편집 후 시각) ----
ORDER = [("웹_01", 16.82), ("웹_02", 12.2), ("웹_03", 38.4), ("웹_06", 18.233), ("웹_09", 35.067), ("웹_04", 16.267),
         ("웹_08", 11.1), ("웹_05", 16.467), ("웹_07", 14.0), ("정산", 15.8), ("언리얼_02", 31.5)]
off, o = {}, 0.0
for n, d in ORDER: off[n] = o; o += d
cues = [  # (클립, 클립 안 시각, 효과음, 볼륨)
    ("웹_01", 0.3, "02_타이핑.wav", 0.25), ("웹_01", 4.5, "03_팝_클릭.wav", 0.5), ("웹_01", 7.9, "01_엔터키_A.wav", 0.7),
    ("웹_01", 8.1, "05_휙_빨리감기.wav", 0.35),
    ("웹_02", 0.05, "05_휙_빨리감기.wav", 0.35), ("웹_02", 2.5, "03_팝_클릭.wav", 0.5), ("웹_02", 5.3, "03_팝_클릭.wav", 0.5), ("웹_02", 9.1, "03_팝_클릭.wav", 0.5),
    ("웹_03", 0.0, "04_휙_부드럽게.wav", 0.35),
    ("웹_06", 0.0, "03_팝_클릭.wav", 0.5), ("웹_06", 2.4, "03_팝_클릭.wav", 0.5), ("웹_06", 4.8, "08_카드_등장.wav", 0.4), ("웹_06", 10.8, "03_팝_클릭.wav", 0.5),
    ("웹_09", 0.0, "03_팝_클릭.wav", 0.5), ("웹_09", 2.4, "08_카드_등장.wav", 0.4), ("웹_09", 13.0, "03_팝_클릭.wav", 0.5),
    ("웹_09", 15.4, "08_카드_등장.wav", 0.4), ("웹_09", 20.4, "03_팝_클릭.wav", 0.5), ("웹_09", 25.9, "05_휙_빨리감기.wav", 0.3),
    ("웹_04", 0.0, "08_카드_등장.wav", 0.4),
    ("웹_08", 0.0, "03_팝_클릭.wav", 0.5), ("웹_08", 2.6, "05_휙_빨리감기.wav", 0.3), ("웹_08", 7.6, "08_카드_등장.wav", 0.4),
    ("웹_05", 0.0, "04_휙_부드럽게.wav", 0.35),
    ("웹_07", 2.0, "08_카드_등장.wav", 0.4),
    ("정산", 0.0, "08_카드_등장.wav", 0.4), ("정산", 4.4, "06_성공_알림.wav", 0.45), ("정산", 9.0, "06_성공_알림.wav", 0.45),
    ("언리얼_02", 0.0, "04_휙_부드럽게.wav", 0.35), ("언리얼_02", 6.0, "05_휙_빨리감기.wav", 0.3),
] + [("언리얼_02", 12.8 + 0.25 * i, "07_타일_팝.wav", 0.35) for i in range(12)]
placed = []
for clip, t, f, v in cues:
    ot = src2out(off[clip] + t)
    if ot is not None: placed.append((ot, f, v))

# ---- 3. 필터 그래프 ----
sel = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b, _ in merged)
mute = "+".join(f"between(t,{o:.3f},{o + b - a:.3f})" for (a, b, v), o in zip(merged, out_starts) if v == 0) or "0"
fc = [f"[0:v]select='{sel}',setpts=N/30/TB,format=yuv420p,split[v1][v2]",
      f"[v1]trim=0:{T2:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={HOLD:.3f}[va]",
      f"[v2]trim={T2:.3f},setpts=PTS-STARTPTS[vb]", "[va][vb]concat=n=2:v=1:a=0[vs]",
      f"[0:a]aselect='{sel}',asetpts=N/SR/TB,volume=0:enable='{mute}',asplit[a1][a2]",
      f"[a1]atrim=0:{T2:.3f},asetpts=PTS-STARTPTS,apad=pad_dur={HOLD:.3f}[aa]",
      f"[a2]atrim={T2:.3f},asetpts=PTS-STARTPTS[ab]", "[aa][ab]concat=n=2:v=0:a=1[nar0]"]
vf, srt = "[vs]", []
os.makedirs(f"{HERE}/fsubs", exist_ok=True)
def s2t(x):
    ms = int(round(x * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
draws = []
for i, (a, b, cap) in enumerate(clips):
    if not cap: continue
    tf = f"{HERE}/fsubs/c{i}.txt"; open(tf, "w", encoding="utf-8").write(cap)
    draws.append(f"drawtext={FONT}:textfile='{tf.replace(':', chr(92) + ':')}':fontsize=54:fontcolor=white:borderw=4:bordercolor=black@0.9:"
                 f"box=1:boxcolor=black@0.5:boxborderw=21:x=(w-text_w)/2:y=h-text_h-66:enable='between(t,{a:.3f},{b - 0.02:.3f})'")
    srt.append(f"{len(srt)+1}\n{s2t(a)} --> {s2t(b)}\n{cap}\n")
fc.append(f"[vs]{','.join(draws)}[vout]")
ins = ["-i", SRC, "-i", CLIP2]
fc.append(f"[1:a]aresample=48000,atrim=0:{CLIP2_SPEECH + 0.1},afade=t=out:st={CLIP2_SPEECH - 0.05}:d=0.15,adelay={int(extra_audio[0]*1000)}|{int(extra_audio[0]*1000)}[c2]")
mix = ["[nar0]", "[c2]"]
for k, (ot, f, v) in enumerate(placed):
    ins += ["-i", f"{SFX}/{f}"]; idx = len(ins) // 2 - 1
    fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume={v},adelay={int(ot*1000)}|{int(ot*1000)}[s{k}]"); mix.append(f"[s{k}]")
fc.append("".join(mix[:2]) + "amix=inputs=2:normalize=0[nar]")
fc.append("".join(mix[2:]) + f"amix=inputs={len(mix)-2}:normalize=0[sfx]")
if BGM:
    ins += ["-i", BGM, "-i", BGM, "-i", BGM, "-i", BGM]; bi = len([x for x in ins if x == "-i"]) - 4
    xf = "".join(f"[{bi+k}:a]aresample=48000,aformat=channel_layouts=stereo[b{k}];" for k in range(4))
    fc.append(xf + f"[b0][b1]acrossfade=d=3[bx1];[bx1][b2]acrossfade=d=3[bx2];[bx2][b3]acrossfade=d=3,"   # 1분 곡을 3초씩 겹쳐 이어 붙임
              f"volume=0.22,atrim=0:{total:.3f},afade=t=in:d=1.5,afade=t=out:st={total-3:.3f}:d=3[bgm0]")
    fc.append("[nar]asplit=2[narA][narK]")
    fc.append("[bgm0][narK]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[bgm]")   # 말할 때 배경음악을 낮춤
    fc.append("[narA][sfx][bgm]amix=inputs=3:normalize=0,alimiter=limit=0.95[aout]")
else:
    fc.append("[nar][sfx]amix=inputs=2:normalize=0,alimiter=limit=0.95[aout]")
open(f"{HERE}/final_fc.txt", "w", encoding="utf-8").write(";\n".join(fc))
cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-/filter_complex", f"{HERE}/final_fc.txt", "-map", "[vout]", "-map", "[aout]",
       "-t", f"{total:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-r", "30", "-c:a", "aac", "-b:a", "192k",
       "-ar", "48000", "-movflags", "+faststart", f"{OUT}.mp4"]
r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
err = "\n".join(l for l in r.stderr.splitlines() if "Fontconfig" not in l)
if r.returncode: sys.exit(err)
open(f"{OUT}.srt", "w", encoding="utf-8").write("\n".join(srt))
d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{OUT}.mp4"]))
print(f"2번 뒤 정지 {HOLD:.2f}s, 타임라인 {total:.2f}s, 구간 {len(merged)}개, 자막 {len(srt)}줄, 효과음 {len(placed)}/{len(cues)}개, 결과 {d:.2f}s, BGM={'있음' if BGM else '없음'}")
