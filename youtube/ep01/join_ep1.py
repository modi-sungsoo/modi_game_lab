"""1080p 클립을 대본 순서로 이어 붙여 합본 mp4 1개 + 합본 SRT를 만든다 (재인코딩 없이 스트림 복사)."""
import os, re, subprocess

VID = "C:/Users/user/Videos"; D = f"{VID}/1편_소스_1080p"; OUT = f"{VID}/1편_합본_1080p"
ORDER = ["웹_01_훅_명령어1번", "웹_02_훅_재미3시간", "웹_03_문제_첫구현직후", "웹_06_리뷰_페르소나회의",
         "웹_09_본론1_밸런스", "웹_04_본론2_8.1참조표", "웹_08_본론2_참조표변화", "웹_05_본론2_웹게임참조표",
         "웹_07_본론3_튜토리얼", "정산_01_결과_정산표", "언리얼_02_예고_기본도형"]

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def t2s(t):
    h, m, s = t.replace(",", ".").split(":"); return int(h) * 3600 + int(m) * 60 + float(s)

def s2t(x):
    ms = int(round(x * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"

def vparams(p):   # 스트림 복사로 이어 붙이려면 이 값이 모든 클립에서 같아야 한다
    return subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=codec_name,profile,pix_fmt,width,height,r_frame_rate,time_base", "-of", "csv=p=0", p], text=True).strip()

params = {n: vparams(f"{D}/{n}.mp4") for n in ORDER}
assert len(set(params.values())) == 1, "클립 형식이 다름: " + repr(params)

lst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "join_list.txt")
with open(lst, "w", encoding="utf-8") as f:
    for n in ORDER: f.write(f"file '{D}/{n}.mp4'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                "-movflags", "+faststart", f"{OUT}.mp4"], check=True)

off, k, out = 0.0, 0, []
for n in ORDER:
    for a, b, text in re.findall(r"\d+\n(\S+) --> (\S+)\n(.+?)\n\n", open(f"{D}/{n}.srt", encoding="utf-8").read(), re.S):
        k += 1; out.append(f"{k}\n{s2t(t2s(a) + off)} --> {s2t(t2s(b) + off)}\n{text}\n")
    off += dur(f"{D}/{n}.mp4")
open(f"{OUT}.srt", "w", encoding="utf-8").write("\n".join(out))
total = dur(f"{OUT}.mp4")
assert abs(total - off) < 0.5, (total, off)   # 이어 붙인 길이 = 클립 길이 합
print(f"합본 {total:.1f}s, 자막 {k}줄")
