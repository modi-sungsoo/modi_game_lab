"""ElevenLabs API로 대본(lines.json) 줄마다 나레이션 mp3를 바로 만든다. 글자별 시각(alignment)도 같은 이름의 .json으로 저장한다.
API 키는 저장소 루트의 .env.local (ElevenLabs CLI onboard 로 만듦, gitignore 됨) 또는 환경변수 ELEVENLABS_API_KEY 에서 읽는다.

사용:
  python narrate_api.py voices                                   # 내 보이스 이름·ID 목록
  python narrate_api.py <lines.json> <저장폴더> <voice_id> [줄번호 ...] [--suffix _Modi] [--dry-run]
    줄번호를 안 주면 전체. 이미 있는 파일은 건너뛴다. --dry-run 은 만들 파일과 글자 수만 보여 준다(키 불필요).
파일 이름은 1편과 같다: '{대본 문장}{suffix}.mp3' (윈도 파일명 금지 문자만 뺌)."""
import base64, json, os, re, sys
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env.local"))
MODEL = "eleven_v4"   # 2026-11-23 multilingual_v2 와 비교해 고름 (1편과 길이·음량이 거의 같음)
TAG = "[speaking quickly] "   # v4 는 speed 설정이 없어 말투 태그로 빠르게 (약 1.13배). 글자 수에 포함돼 과금된다


def client():
    if not os.environ.get("ELEVENLABS_API_KEY"):
        sys.exit("ELEVENLABS_API_KEY 가 없습니다. 저장소 루트에서 npx -y @elevenlabs/cli@latest onboard init 을 실행하세요.")
    return ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])   # SDK 기본값은 import 시점(.env.local 로드 전)에 읽혀 비어 있다


def name(line, suffix):
    return re.sub(r'[\\/:*?"<>|]', "", line).strip() + suffix


def strip_tag(a):
    """글자별 시각에서 앞에 붙인 태그 글자를 빼서 대본 글자와 1:1로 맞춘다."""
    k = len(TAG)
    assert "".join(a["characters"][:k]) == TAG, "시각 데이터가 태그로 시작하지 않습니다"
    return {key: v[k:] for key, v in a.items()}


def main(argv):
    if argv[:1] == ["voices"]:
        for v in client().voices.get_all().voices:
            print(v.voice_id, v.name, v.category or "")
        return

    dry = "--dry-run" in argv
    suffix = ""
    if "--suffix" in argv:
        i = argv.index("--suffix"); suffix = argv[i + 1]; del argv[i:i + 2]
    args = [a for a in argv if a != "--dry-run"]
    if len(args) < 3:
        sys.exit(__doc__)
    lines_path, out, voice, nums = args[0], args[1], args[2], [int(a) for a in args[3:]]

    lines = json.load(open(lines_path, encoding="utf-8"))
    names = [name(l, suffix) for l in lines]
    assert len(set(names)) == len(names), "파일명 중복: 대본에 같은 문장이 있습니다"
    todo = [n for n in (nums or range(1, len(lines) + 1))
            if not os.path.exists(f"{out}/{names[n - 1]}.mp3")]
    chars = sum(len(TAG + lines[n - 1]) for n in todo)
    print(f"만들 줄 {len(todo)}개, {chars}자")
    if dry:
        for n in todo: print(n, names[n - 1] + ".mp3")
        return

    c = client()
    sub = c.user.subscription.get()
    left = sub.character_limit - sub.character_count
    print(f"이번 달 남은 글자 {left}자")
    if chars > left:
        sys.exit("남은 글자 수가 모자라 아무것도 만들지 않았습니다.")

    os.makedirs(out, exist_ok=True)
    for n in todo:
        text = lines[n - 1]
        r = c.text_to_speech.convert_with_timestamps(voice, text=TAG + text, model_id=MODEL, language_code="ko",
                                                     output_format="mp3_44100_128")
        base = f"{out}/{names[n - 1]}"
        open(base + ".mp3", "wb").write(base64.b64decode(r.audio_base_64))
        json.dump({"text": text, "model": MODEL, "tag": TAG, "alignment": strip_tag(r.alignment.model_dump())},
                  open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False)
        print(n, names[n - 1] + ".mp3")


if __name__ == "__main__":
    main(sys.argv[1:])
