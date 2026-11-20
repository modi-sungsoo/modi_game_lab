import json, os, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
DST = "C:/Users/user/Desktop/유튜브/나레이션/1. AI에게 보드게임 룰북만 줬더니 명령어 하나로 게임이 됐습니다"
lines = json.load(open(f"{HERE}/lines.json", encoding="utf-8"))
bad = 0
for i, t in enumerate(lines, 1):
    f = f"{DST}/" + re.sub(r'[\/:*?"<>|]', "", t).strip() + ".mp3"
    if not os.path.exists(f): print("MISSING", i); bad += 1; continue
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
    rate = len(t.replace(" ", "")) / d
    flag = "" if 3.0 <= rate <= 9.5 else "  <-- 확인"
    if flag: bad += 1
    print(f"{i:2d} {d:5.2f}s {rate:4.1f}자/초{flag}")
print("문제", bad)
