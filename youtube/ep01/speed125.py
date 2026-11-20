"""세로 쇼츠·릴스 영상을 1.25배속으로(목소리 높이는 유지) + 자막 시간도 맞춰 줄인다."""
import re, subprocess, sys
D = "C:/Users/user/Desktop/유튜브/영상/1. AI 딸깍 게임에 재미는 어떻게 입힐까요"
SP = 1.25
for name in sys.argv[1:]:
    src, out = f"{D}/{name}", f"{D}/{name}_1.25배속"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{src}.mp4",
                        "-filter_complex", f"[0:v]setpts=PTS/{SP},fps=30[v];[0:a]atempo={SP}[a]", "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", f"{out}.mp4"],
                       capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode: sys.exit(r.stderr)
    def sc(m):
        ms = round((int(m[1]) * 3600000 + int(m[2]) * 60000 + int(m[3]) * 1000 + int(m[4])) / SP)
        return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
    srt = open(f"{src}.srt", encoding="utf-8").read()
    open(f"{out}.srt", "w", encoding="utf-8").write(re.sub(r"(\d+):(\d+):(\d+),(\d+)", sc, srt))
    dur = lambda p: float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
    print(name, f"{dur(src + '.mp4'):.2f}s -> {dur(out + '.mp4'):.2f}s")
