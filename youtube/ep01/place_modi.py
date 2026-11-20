"""다운로드 폴더의 ElevenLabs mp3를 생성 순서대로 줄 번호에 맞춰 'ModiSungSoo 나레이션' 폴더에 '{대본}_Modi.mp3'로 옮긴다.
사용: python place_modi.py 1 2 3"""
import json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DL = "C:/Users/user/Downloads"
DST = "C:/Users/user/Desktop/유튜브/나레이션/1. AI에게 보드게임 룰북만 줬더니 명령어 하나로 게임이 됐습니다/ModiSungSoo 나레이션"
os.makedirs(DST, exist_ok=True)
lines = json.load(open(f"{HERE}/lines.json", encoding="utf-8"))
name = lambda n: re.sub(r'[\\/:*?"<>|]', "", lines[n - 1]).strip() + "_Modi.mp3"
nums = [int(a) for a in sys.argv[1:]]
files = sorted(f for f in os.listdir(DL) if f.startswith("ElevenLabs_") and f.endswith(".mp3"))
if len(files) != len(nums):
    sys.exit(f"새 파일 {len(files)}개, 줄 번호 {len(nums)}개 — 옮기지 않음")
for f, n in zip(files, nums):
    dst = f"{DST}/{name(n)}"
    assert not os.path.exists(dst), dst
    shutil.move(f"{DL}/{f}", dst); print(n)
