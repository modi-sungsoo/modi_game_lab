"""1편 소스 클립 전체 재빌드: 자막없음 원본 + 대본 자막 번인본 + SRT.

자막 타이밍은 나레이션 녹음 전이라 글자 수 비례 추정치다(구간 안에서 배분).
shortcut: 녹음본이 나오면 SRT 타이밍을 실제 음성에 맞춰 다시 배분해야 한다.
"""
import os, subprocess, sys

# --1080 이면 1080p로 별도 폴더에 렌더링 (기본 720p). 화면 좌표는 1280x720 기준에 SC를 곱한다.
HD = "--1080" in sys.argv
if HD: sys.argv.remove("--1080")
SC = 1.5 if HD else 1.0
W, H = int(1280 * SC), int(720 * SC)
px = lambda v: int(round(v * SC))

S = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
VID = "C:/Users/user/Videos"
WEB = f"{VID}/디자인빌리지 웹게임 구현 과정 플레이 영상_2026-11-17 15-58-48.mkv"
TOK = f"{VID}/토큰 수 정산 과정_2026-11-17 16-30-20.mkv"
UNR = f"{VID}/언리얼 1차 구현 과정_2026-11-17 16-40-59.mkv"
D = f"{VID}/1편_소스" + ("_1080p" if HD else ""); CLEAN = f"{D}/자막없음"; TILES = f"{VID}/1편_소스/타일"
SUBDIR = f"{S}/subs"
for p in (CLEAN, SUBDIR): os.makedirs(p, exist_ok=True)

FONT = "fontfile='C\\:/Windows/Fonts/malgunbd.ttf'"
OUT = f"scale={W}:{H}:flags=lanczos,setsar=1,fps=30,format=yuv420p"
ENC = ["-an", "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-movflags", "+faststart"]
NOSIDE = "crop=2140:1204:420:118"       # Claude 왼쪽 프로젝트 목록 제외
NOBAR = "crop=2320:1305:120:135"        # 브라우저 주소창 제외
VIEW = "crop=2050:1153:10:215"          # 언리얼 뷰포트
HL = "0xFFC83D"                         # 요청 강조색

def ff(args, out):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args, *ENC, out], capture_output=True, encoding="utf-8", errors="replace")
    err = "\n".join(l for l in r.stderr.splitlines() if "Fontconfig" not in l)
    if r.returncode: sys.exit(f"FAIL {out}\n{err}")
    return out

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def seg(i, speed, length, pre=""):
    return f"[{i}:v]{pre + ',' if pre else ''}setpts=PTS/{speed},{OUT},trim=0:{length},setpts=PTS-STARTPTS"

def zoom(i, box, hold):
    """정지 화면에서 요청 말풍선을 확대 + 노란 테두리 강조. box = 원본(2560x1440) 좌표."""
    x0, y0, x1, y1 = box
    w = max(int((x1 - x0) * 1.3), 900); w -= w % 2; h = int(w * 9 / 16); h -= h % 2
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cxo = int(min(max(cx - w / 2, 0), 2560 - w)); cyo = int(min(max(cy - h / 2, 0), 1440 - h))
    k = W / w; pad = 14
    bx, by = int((x0 - pad - cxo) * k), int((y0 - pad - cyo) * k)
    bw, bh = int((x1 - x0 + 2 * pad) * k), int((y1 - y0 + 2 * pad) * k)
    return (f"[{i}:v]crop={w}:{h}:{cxo}:{cyo},{OUT},trim=0:0.04,setpts=PTS-STARTPTS,"
            f"tpad=stop_mode=clone:stop_duration={hold},"
            f"drawbox=x={bx}:y={by}:w={bw}:h={bh}:color={HL}:t={px(6)}")

def inp(src, ss, t):
    return ["-ss", str(ss), "-t", str(t), "-i", src]

def label(text, t0=0, t1=999):   # 대본이 지정한 화면 자막: 왼쪽 위 노란 라벨
    return (f"drawtext={FONT}:text='{text}':fontsize={px(44)}:fontcolor=black:box=1:boxcolor={HL}:boxborderw={px(16)}:"
            f"x={px(48)}:y={px(40)}:enable='between(t,{t0},{t1})'")

# ---------------- 대본 자막 ----------------
def cues_in(lines, s, e):
    """[s,e] 구간에 줄들을 글자 수 비례로 배분."""
    n = [len(l.replace(" ", "")) for l in lines]; tot = sum(n); t = s; out = []
    for l, c in zip(lines, n):
        d = (e - s) * c / tot; out.append((round(t, 2), round(t + d - 0.08, 2), l)); t += d
    return out

def srt_time(x):
    ms = int(round(x * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"

def burn(name, cues, extra=""):
    src = f"{CLEAN}/{name}.mp4"; vf = []
    with open(f"{D}/{name}.srt", "w", encoding="utf-8") as f:
        for k, (a, b, text) in enumerate(cues):
            tf = f"{SUBDIR}/c{abs(hash(name)) % 10**8}_{k}.txt"   # drawtext는 한글 경로를 못 읽음
            with open(tf, "w", encoding="utf-8") as g: g.write(text)
            tfe = tf.replace(":", "\\:")
            vf.append(f"drawtext={FONT}:textfile='{tfe}':fontsize={px(36)}:fontcolor=white:borderw={px(3)}:bordercolor=black@0.9:"
                      f"box=1:boxcolor=black@0.5:boxborderw={px(14)}:x=(w-text_w)/2:y=h-text_h-{px(44)}:enable='between(t,{a},{b})'")
            f.write(f"{k+1}\n{srt_time(a)} --> {srt_time(b)}\n{text}\n\n")
    if extra: vf.insert(0, extra)
    ff(["-i", src, "-vf", ",".join(vf)], f"{D}/{name}.mp4")
    print(f"{name}: {dur(f'{D}/{name}.mp4'):.1f}s, 자막 {len(cues)}줄")

# ---------------- 클립 ----------------
def web01():
    fc = ";".join([seg(0, 2, 4.5, NOSIDE) + "[a]",
                   zoom(1, (1020, 826, 1830, 866), 3.6) + "[b]",
                   seg(2, 28, 1, NOSIDE) + "[c]",
                   seg(3, 1, 5.4, NOSIDE) + "[d]",
                   "[a][b][c][d]concat=n=4:v=1:a=0[o]"])
    ff([*inp(WEB, 17, 9), *inp(WEB, 26.5, 0.5), *inp(WEB, 29, 28), *inp(WEB, 58, 5.4),
        "-filter_complex", fc, "-map", "[o]"], f"{CLEAN}/웹_01_훅_명령어1번.mp4")
    burn("웹_01_훅_명령어1번",
         [(0.3, 4.4, "AI 딸깍으로 게임 만들기가 그렇게 쉽다는데 사실일까요?"),
          (4.5, 6.9, "테스트삼아 우선 제가 기획했던 보드게임 룰북으로"),
          (7.0, 9.4, "웹게임을 만들어달라고 딱 한 줄 요청했습니다."),
          (9.5, 14.3, "그랬더니 진짜 바로 웹게임이 구현됐습니다.")],
         label("명령어 1번"))

def web02():
    # 빨리감기 사이사이에 '다듬기' 요청 3개를 확대해서 멈춰 보여 줌.
    # 07:56–09:24(476–564초)는 노션 메모에 실명이 보여서 뺀다.
    fc = ";".join([seg(0, 87, 0.53, NOBAR) + "[a1]", seg(1, 87, 1.97, NOBAR) + "[a2]",
                   zoom(2, (915, 538, 1817, 641), 1.8) + "[z1]",
                   seg(3, 34, 1, NOBAR) + "[b]", zoom(4, (890, 584, 1824, 710), 1.8) + "[z2]",
                   seg(5, 72, 2, NOBAR) + "[c]", zoom(6, (1236, 614, 1824, 672), 1.8) + "[z3]",
                   seg(7, 14, 1.2, NOBAR) + "[d]",
                   "[a1][a2][z1][b][z2][c][z3][d]concat=n=8:v=1:a=0[o]"])
    ff([*inp(WEB, 430, 46), *inp(WEB, 564, 171), *inp(WEB, 735, 0.5), *inp(WEB, 736, 34), *inp(WEB, 770, 0.5),
        *inp(WEB, 771, 144), *inp(WEB, 915, 0.5), *inp(WEB, 916, 17),
        "-filter_complex", fc, "-map", "[o]"], f"{CLEAN}/웹_02_훅_재미3시간.mp4")
    burn("웹_02_훅_재미3시간", cues_in(["그런데 이 게임을 재밌게 만드는 데는", "3시간이 걸렸습니다.",
                                       "오늘은 그 3시간 동안 제가 무엇을 했는지", "보여 드리겠습니다."], 0.3, 12.0),
         label("재미 3시간"))

def web03():
    fc = ";".join([seg(0, 1, 2, NOSIDE) + "[a]", seg(1, 1.5, 8) + "[b]", seg(2, 1.5, 16) + "[c]",
                   seg(3, 20, 7) + "[d]", "[a][b][c][d]concat=n=4:v=1:a=0[o]"])
    ff([*inp(WEB, 62, 2), *inp(WEB, 188, 12), *inp(WEB, 212, 24), *inp(WEB, 240, 140),
        "-filter_complex", fc, "-map", "[o]"], f"{CLEAN}/웹_03_문제_첫구현직후.mp4")
    burn("웹_03_문제_첫구현직후", cues_in([
        "제 보드게임 <디자인 빌리지>는 건물 타일을 이어 붙여", "마을을 만드는 패밀리 전략 타일놓기 게임입니다.",
        "내 사유지를 어떤 건물 옆에 두느냐에 따라", "점수가 달라집니다.", "핵심 재미는 공유지와 사유지 사이에서", "발생하는 님비핌피 현상입니다.",
        "AI는 순식간에 규칙대로 돌아가는 게임을 만들어 줬습니다.", "하지만 게임의 재미는 기획자가 만들어야 합니다.",
        "규칙에 맞게 돌아가도, 어떤 건물은 고를 이유가 없고", "어떤 타일은 아무도 놓지 않는다면", "그 게임은 재미가 없습니다."],
        0.3, 32.8))

def web04():
    tbl = f"{S}/tbl.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "00:07:42.5", "-i", WEB, "-frames:v", "1", "-vf",
                    "crop=2347:1240:122:200,pad=2720:1530:186:30:white,scale=2560:1440", tbl], check=True)
    ff(["-i", tbl, "-filter_complex",
        f"[0:v]zoompan=z='min(zoom+0.00013,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=450:s={W}x{H}:fps=30,format=yuv420p[o]",
        "-map", "[o]"], f"{CLEAN}/웹_04_본론2_8.1참조표.mp4")
    burn("웹_04_본론2_8.1참조표", cues_in([
        "밸런스를 맞춰도 플레이어가 그 숫자를 읽지 못하면", "소용이 없습니다.",
        "근접 점수는 타일을 놓을 때마다 확인해야 하는 정보라,", "참조표를 얼마나 빨리 읽을 수 있느냐가",
        "게임의 속도를 정합니다."], 0.3, 14.8))

def web05():
    punch = "crop=1040:585:0:855"
    fc = ";".join([seg(0, 1, 4) + "[a]", seg(1, 0.67, 5, punch) + "[b]", seg(2, 1, 4) + "[c]",
                   "[a][b][c]concat=n=3:v=1:a=0[o]"])
    ff([*inp(WEB, 1049, 4), *inp(WEB, 1055.5, 4), *inp(WEB, 1059.5, 4),
        "-filter_complex", fc, "-map", "[o]"], f"{CLEAN}/웹_05_본론2_웹게임참조표.mp4")
    burn("웹_05_본론2_웹게임참조표", cues_in([
        "웹게임이 되면서 참조표의 UI를 다시 고민했습니다.", "복잡한 숫자표는 지우고,",
        "최대한 직관적인 색상과 그림으로 바꿨습니다.", "그리고 어떤 배치가", "플레이에 가장 도움이 될지 고민했습니다."], 0.3, 12.9))

def web06():
    # 11:06~11:40 기획서 리뷰 프로젝트: 요청 2개 확대 → 페르소나 4명 표 → 회의록 문서 + Claude 확인 질문
    # 회의록 첫 화면(11:36)은 작성자 이름 줄이 보여서 쓰지 않고, 본문으로 내려간 11:40을 쓴다.
    still = lambda i, crop, hold: (f"[{i}:v]crop={crop},{OUT},trim=0:0.04,setpts=PTS-STARTPTS,"
                                   f"tpad=stop_mode=clone:stop_duration={hold}")
    fc = ";".join([zoom(0, (914, 90, 1832, 196), 2.4) + "[a]", zoom(1, (914, 374, 1832, 480), 2.4) + "[b]",
                   zoom(2, (734, 790, 1832, 1180), 3.6) + "[c]",
                   still(3, "1840:1035:720:100", 2.4) + "[d]", zoom(4, (2020, 490, 2444, 676), 3.0) + "[e]",
                   "[a][b][c][d][e]concat=n=5:v=1:a=0[o]"])
    ff([*inp(WEB, 666, 0.5), *inp(WEB, 672, 0.5), *inp(WEB, 672, 0.5), *inp(WEB, 700, 0.5), *inp(WEB, 700, 0.5),
        "-filter_complex", fc, "-map", "[o]"], f"{CLEAN}/웹_06_리뷰_페르소나회의.mp4")
    burn("웹_06_리뷰_페르소나회의", [
        (0.3, 4.9, "먼저 기획서를 AI에게 리뷰받았습니다."),
        (5.0, 7.6, "시니어 기획자, 퍼블리셔, QA 테스터, 교사."),
        (7.7, 10.4, "네 명의 페르소나가 회의하듯 의견을 나눴습니다."),
        (10.5, 14.0, "해석이 갈리는 규칙은 AI가 질문으로 따로 남겼습니다.")])

def web07():
    # 16:20~16:52 튜토리얼: 시작 화면(실속) → 튜토리얼 카드 8장(2.33배)
    # 카드가 화면 높이의 80%라서 크롭하지 않는다(크롭하면 카드 글이 자막에 가려짐). 튜토리얼이 닫히기 전(16:52)까지만.
    fc = ";".join([seg(0, 1, 2) + "[a]", seg(1, 2.33, 12) + "[b]", "[a][b]concat=n=2:v=1:a=0[o]"])
    ff([*inp(WEB, 980, 2), *inp(WEB, 984, 28), "-filter_complex", fc, "-map", "[o]"],
       f"{CLEAN}/웹_07_본론3_튜토리얼.mp4")
    burn("웹_07_본론3_튜토리얼", [
        (0.3, 6.6, "보드게임을 웹게임으로 바꾸며 튜토리얼도 따로 필요했습니다."),
        (6.8, 13.8, "보드게임을 처음 하는 사람도 이해할 수 있게 용어도 풀어 설명했습니다.")])

def web08():
    # 12:48~13:10 참조표 변화: 8.2 가시성 요청 확대 → 그림 참조표 시안들(4배) → 완성 카드 PNG
    fc = ";".join([zoom(0, (892, 584, 1832, 724), 2.6) + "[a]", seg(1, 4, 5) + "[b]",
                   f"[2:v]crop=1250:1325:1290:60,scale=-2:{H},pad={W}:{H}:(ow-iw)/2:0:white,setsar=1,fps=30,format=yuv420p,"
                   f"trim=0:0.04,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=3.4[c]",
                   "[a][b][c]concat=n=3:v=1:a=0[o]"])
    ff([*inp(WEB, 768, 0.5), *inp(WEB, 770, 20), *inp(WEB, 790, 0.5), "-filter_complex", fc, "-map", "[o]"],
       f"{CLEAN}/웹_08_본론2_참조표변화.mp4")
    burn("웹_08_본론2_참조표변화", [(0.3, 5.4, "숫자표로만 돼있던 참조표를"), (5.5, 11.0, "그림으로 읽는 참조표로 바꿔 나갔습니다.")])

def web09():
    # 13:10~14:26 밸런스: 계산 요청 → 결과표 → 스크롤 → '공장끼리 +5' 요청 → 비교표 → 기각 이유 → 이후 정리
    fc = ";".join([zoom(0, (632, 1036, 1220, 1092), 2.4) + "[a]", zoom(1, (734, 470, 1832, 980), 6) + "[b]",
                   seg(2, 3, 4.6, NOSIDE) + "[c]", zoom(3, (1264, 310, 1832, 376), 2.4) + "[d]",
                   zoom(4, (734, 590, 1832, 890), 5) + "[e]", zoom(5, (734, 980, 1832, 1280), 5.5) + "[f]",
                   seg(6, 4, 7, NOSIDE) + "[g]", "[a][b][c][d][e][f][g]concat=n=7:v=1:a=0[o]"])
    ff([*inp(WEB, 790, 0.5), *inp(WEB, 802, 0.5), *inp(WEB, 802, 14), *inp(WEB, 830, 0.5), *inp(WEB, 830, 0.5),
        *inp(WEB, 830, 0.5), *inp(WEB, 838, 28), "-filter_complex", fc, "-map", "[o]"],
       f"{CLEAN}/웹_09_본론1_밸런스.mp4")
    burn("웹_09_본론1_밸런스", [
        (0.3, 4.4, "각 건물의 기댓값과 흔한 점수 범위와"), (4.5, 8.4, "점수 확률 등을 계산했습니다."),
        (8.6, 11.6, "사람이 하면 엄청난 노동이 필요한 플레이 테스트도"),
        (11.7, 15.4, "AI에게 시뮬레이션을 돌려 검증 데이터를 금방 쌓았습니다."),
        (15.6, 18.6, "고점을 균등하게 숫자 맞춤하는 게 아니라,"),
        (18.7, 21.5, "특색에 맞는 밸런스를 기획자가 맞춰야"), (21.6, 24.0, "게임의 재미가 살아납니다."),
        (24.2, 28.6, "AI에게 끌려가지 않으려면 기획자의 판단이 중요합니다."),
        (28.8, 33.5, "해결 과제를 정리하고 의견을 기각하는 선택도 중요합니다.")])

SETTLE = ["걸린 시간은 기획 10분, 아트 10분,", "다듬기 3시간입니다.", "구독 외에 따로 낸 돈은 없습니다.",
          "같은 양을 API로 썼다면,", "언리얼 1차 구현에만 약 71달러가 들었을 겁니다."]

def token01():
    ff([*inp(TOK, 104, 12), "-filter_complex", seg(0, 1, 12, "crop=1496:842:1064:170") + "[o]", "-map", "[o]"],
       f"{CLEAN}/토큰_01_결과_1편정산탭.mp4")
    burn("토큰_01_결과_1편정산탭", cues_in(SETTLE, 0.3, 11.9))

def settle01():
    hold = [1.6, 1.6, 1.8, 2.4, 0.6, 1.2, 1.2, 3.4]   # 기획·아트·다듬기·$0 → (잠깐) → Opus·Fable·합계
    args, fc, prev, off = [], [], "v0", 0.0
    for k, h in enumerate(hold):
        args += ["-loop", "1", "-t", str(h), "-i", f"{S}/cards/cost_{k}.png"]; fc.append(f"[{k}:v]{OUT}[v{k}]")
    for k in range(1, len(hold)):
        off = round(off + hold[k - 1] - 0.2, 2)
        fc.append(f"[{prev}][v{k}]xfade=transition=fade:duration=0.2:offset={off}[x{k}]"); prev = f"x{k}"
    fc.append(f"[{prev}]format=yuv420p[xo]"); prev = "xo"   # xfade 출력이 yuv444p가 되면 이어 붙인 합본이 그 지점에서 멈춘다
    ff([*args, "-filter_complex", ";".join(fc), "-map", f"[{prev}]"], f"{CLEAN}/정산_01_결과_정산표.mp4")
    # 카드 공개 순서(기획→아트→다듬기→$0→API 카드)에 맞춘 수동 타이밍
    burn("정산_01_결과_정산표", [(0.2, 3.1, SETTLE[0]), (3.2, 4.9, SETTLE[1]), (5.0, 7.0, SETTLE[2]),
                                (7.1, 8.8, SETTLE[3]), (8.9, 12.3, SETTLE[4])])

def unreal01():
    # 요청 3개(스팀 가이드 → 편집 가능한 파일 → 빌드 오류)를 확대해서 멈춰 보여 주고, 사이는 빨리감기
    fc = ";".join([zoom(0, (916, 310, 1832, 414), 2.6) + "[z1]", seg(1, 40, 2) + "[a]",
                   zoom(2, (1062, 320, 1833, 379), 1.8) + "[z2]", zoom(3, (1536, 1055, 1830, 1114), 1.6) + "[z3]",
                   seg(4, 40, 1.5) + "[b]", seg(5, 25, 2) + "[c]", seg(6, 1.5, 8, VIEW) + "[d]",
                   "[z1][a][z2][z3][b][c][d]concat=n=7:v=1:a=0[o]"])
    ff([*inp(UNR, 1, 0.5), *inp(UNR, 2, 80), *inp(UNR, 82, 0.5), *inp(UNR, 88, 0.5), *inp(UNR, 89, 61),
        *inp(UNR, 180, 50), *inp(UNR, 236, 12),
        "-filter_complex", fc, "-map", "[o]"], f"{CLEAN}/언리얼_01_결과_1차구현.mp4")
    burn("언리얼_01_결과_1차구현", cues_in(SETTLE[3:], 3.0, 10.0))

def unreal02():
    TW, TH, GAP, Y0 = px(170), px(194), px(18), px(120); X0 = (W - 6 * TW - 5 * GAP) // 2
    tiles = sorted(f for f in os.listdir(TILES) if f.endswith(".png"))
    args = [*inp(UNR, 250, 6), *inp(UNR, 256, 180), *inp(UNR, 436, 1)]
    fc = [seg(0, 1, 6, VIEW) + "[a]", seg(1, 30, 6, VIEW) + "[b]",
          f"[2:v]{VIEW},{OUT},trim=0:0.1,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=17.4[c0]",
          f"color=black:s={W}x{H}:d=17.5,format=rgba,colorchannelmixer=aa=0.55,fade=in:st=0.3:d=0.5:alpha=1[dim]",
          "[c0][dim]overlay[c]", "[a][b][c]concat=n=3:v=1:a=0[base]"]
    prev = "base"
    for i, t in enumerate(tiles):
        args += ["-loop", "1", "-t", "29.4", "-i", f"{TILES}/{t}"]
        r, c = divmod(i, 6); x = X0 + c * (TW + GAP); y = Y0 + r * (TH + GAP); t0 = round(12.8 + 0.25 * i, 2)
        fc.append(f"[{i+3}:v]scale={TW}:{TH},format=rgba,fade=in:st={t0}:d=0.3:alpha=1[t{i}]")
        fc.append(f"[{prev}][t{i}]overlay=x={x}:y='{y}+{px(30)}*max(0,1-(t-{t0})/0.3)':enable='gte(t,{t0})'[o{i}]"); prev = f"o{i}"
    fc[-1] = fc[-1].rsplit("[", 1)[0] + "[o]"
    ff([*args, "-filter_complex", ";".join(fc), "-map", "[o]", "-t", "29.5"], f"{CLEAN}/언리얼_02_예고_기본도형.mp4")
    burn("언리얼_02_예고_기본도형", [
        (0.5, 5.5, "지금 언리얼 버전은 네모와 상자만으로 돌아갑니다."),
        (12.6, 15.6, "다음 편에서는 이 아트워크를 언리얼에 입혀 보겠습니다."),
        (15.7, 19.2, "2D 보드게임이 3D로 어떻게 변하는지 궁금하시다면"),
        (19.3, 23.3, "구독과 좋아요, 댓글, 알림설정까지 부탁드리겠습니다!"),
        (23.4, 26.1, "빠른 시일내에 스팀 출시까지 해서"),
        (26.2, 29.4, "수익 정산까지 보여드리겠습니다!")])

JOBS = dict(web08=web08, web09=web09, web07=web07, web06=web06, web01=web01, web02=web02, web03=web03, web04=web04, web05=web05,
            token01=token01, settle01=settle01, unreal01=unreal01, unreal02=unreal02)
if __name__ == "__main__":
    for name in (sys.argv[1:] or JOBS):
        JOBS[name]()
