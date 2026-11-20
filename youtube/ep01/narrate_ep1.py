"""1080p 자막없음 클립에 나레이션 mp3를 줄별로 얹고, 자막을 실제 음성 길이에 맞춰 다시 새긴 뒤 합본을 만든다.
- 각 줄은 원래 자막 시작 시각에 놓되, 앞 줄 음성과 겹치면 0.15초 뒤로 민다.
- 음성이 클립보다 길어지면 클립 마지막 장면을 정지 화면으로 늘린다.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
VID = "C:/Users/user/Videos"
SRC = f"{VID}/1편_소스_1080p"
NOSUB = "--nosub" in sys.argv   # Vrew용: 화면 자막 없이 (Vrew가 자막을 새로 만듦)
OUTD = f"{VID}/1편_나레이션" + ("/자막없음" if NOSUB else "")
NAR = "C:/Users/user/Desktop/유튜브/나레이션/1. AI에게 보드게임 룰북만 줬더니 명령어 하나로 게임이 됐습니다"
ORDER = ["웹_01_훅_명령어1번", "웹_02_훅_재미3시간", "웹_03_문제_첫구현직후", "웹_06_리뷰_페르소나회의",
         "웹_09_본론1_밸런스", "웹_04_본론2_8.1참조표", "웹_08_본론2_참조표변화", "웹_05_본론2_웹게임참조표",
         "웹_07_본론3_튜토리얼", "정산_01_결과_정산표", "언리얼_02_예고_기본도형"]
LABELS = {"웹_01_훅_명령어1번": "명령어 1번", "웹_02_훅_재미3시간": "재미 3시간"}
FONT = "fontfile='C\\:/Windows/Fonts/malgunbd.ttf'"
HL = "0xFFC83D"
GAP, TAIL = 0.15, 0.4
os.makedirs(OUTD, exist_ok=True); os.makedirs(f"{HERE}/subs", exist_ok=True)

def run(args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, encoding="utf-8", errors="replace")
    err = "\n".join(l for l in r.stderr.splitlines() if "Fontconfig" not in l)
    if r.returncode: sys.exit(err)

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def t2s(t):
    h, m, s = t.replace(",", ".").split(":"); return int(h) * 3600 + int(m) * 60 + float(s)

def s2t(x):
    ms = int(round(x * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"

lines = json.load(open(f"{HERE}/lines.json", encoding="utf-8"))
narfile = lambda t: f"{NAR}/" + re.sub(r'[\\/:*?"<>|]', "", t).strip() + ".mp3"

all_srt, offset, k, li = [], 0.0, 0, 0
for name in ORDER:
    cues = re.findall(r"\d+\n(\S+) --> (\S+)\n(.+?)\n\n", open(f"{SRC}/{name}.srt", encoding="utf-8").read(), re.S)
    clean = f"{SRC}/자막없음/{name}.mp4"; vlen = dur(clean)
    placed, prev_end = [], 0.0
    for a, b, text in cues:
        assert text == lines[li], (name, text, lines[li]); li += 1
        f = narfile(text); d = dur(f)
        st = max(t2s(a), prev_end + GAP if placed else t2s(a))
        placed.append((st, st + d, text, f)); prev_end = st + d
    total = max(vlen, prev_end + TAIL)
    # 영상: 필요하면 마지막 장면을 늘리고, 라벨·자막을 새로 새김
    vf = [f"tpad=stop_mode=clone:stop_duration={total - vlen + 0.05:.2f}", f"trim=0:{total:.3f}"]
    if name in LABELS:
        vf.append(f"drawtext={FONT}:text='{LABELS[name]}':fontsize=66:fontcolor=black:box=1:boxcolor={HL}:boxborderw=24:x=72:y=60")
    for i, (st, en, text, _) in enumerate(placed):
        if NOSUB:
            k += 1; all_srt.append(f"{k}\n{s2t(st + offset)} --> {s2t(en + offset)}\n{text}\n"); continue
        tf = f"{HERE}/subs/n{li}_{i}.txt"; open(tf, "w", encoding="utf-8").write(text)
        vf.append(f"drawtext={FONT}:textfile='{tf.replace(':', chr(92) + ':')}':fontsize=54:fontcolor=white:borderw=4:bordercolor=black@0.9:"
                  f"box=1:boxcolor=black@0.5:boxborderw=21:x=(w-text_w)/2:y=h-text_h-66:enable='between(t,{st:.3f},{en:.3f})'")
        k += 1; all_srt.append(f"{k}\n{s2t(st + offset)} --> {s2t(en + offset)}\n{text}\n")
    # 오디오: 줄마다 지연시켜 섞기 (amix가 볼륨을 줄이지 않게 normalize=0)
    ins = ["-i", clean] + sum([["-i", f] for *_, f in placed], [])
    af = [f"[{i+1}:a]aresample=48000,adelay={int(st*1000)}|{int(st*1000)}[a{i}]" for i, (st, *_ ) in enumerate(placed)]
    af.append("".join(f"[a{i}]" for i in range(len(placed))) + f"amix=inputs={len(placed)}:normalize=0,apad,atrim=0:{total:.3f}[aout]")
    run([*ins, "-filter_complex", f"[0:v]{','.join(vf)}[vout];" + ";".join(af), "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "30",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", f"{OUTD}/{name}.mp4"])
    offset += dur(f"{OUTD}/{name}.mp4")
    print(f"{name}: {vlen:.1f}s -> {total:.1f}s, {len(placed)}줄")

assert li == len(lines), (li, len(lines))
lst = f"{HERE}/nar_list.txt"
open(lst, "w", encoding="utf-8").write("".join(f"file '{OUTD}/{n}.mp4'\n" for n in ORDER))
final = f"{VID}/1편_합본_1080p_나레이션" + ("_자막없음" if NOSUB else "")
run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", f"{final}.mp4"])
open(f"{final}.srt", "w", encoding="utf-8").write("\n".join(all_srt))
print(f"합본 {dur(final + '.mp4'):.1f}s, 자막 {k}줄")
