"""다운로드 폴더의 ElevenLabs mp3를 생성 시각 순으로 대본 줄 번호에 대응시켜, 대본 문장 이름으로 나레이션 폴더에 옮긴다.
사용: python place_nar.py 16 17 18   (새로 받은 파일 수와 인자 수가 같아야 함)"""
import json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DL = "C:/Users/user/Downloads"
DST = "C:/Users/user/Desktop/유튜브/나레이션/1. AI에게 보드게임 룰북만 줬더니 명령어 하나로 게임이 됐습니다"
lines = json.load(open(f"{HERE}/lines.json", encoding="utf-8"))
name = lambda n: re.sub(r'[\\/:*?"<>|]', "", lines[n - 1]).strip() + ".mp3"   # 윈도 파일명 금지 문자만 뺌
assert len({name(i) for i in range(1, len(lines) + 1)}) == len(lines), "파일명 중복"

nums = [int(a) for a in sys.argv[1:]]
files = sorted(f for f in os.listdir(DL) if f.startswith("ElevenLabs_") and f.endswith(".mp3"))
if len(files) != len(nums):
    sys.exit(f"새 파일 {len(files)}개, 줄 번호 {len(nums)}개 — 맞지 않아 아무것도 옮기지 않음: {files}")
for f, n in zip(files, nums):
    dst = f"{DST}/{name(n)}"
    assert not os.path.exists(dst), f"이미 있음: {dst}"
    shutil.move(f"{DL}/{f}", dst)
    print(n, name(n))
