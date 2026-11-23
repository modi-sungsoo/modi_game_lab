"""ElevenLabs API로 대본(lines.json) 줄마다 나레이션 mp3를 바로 만든다. 글자별 시각(alignment)도 같은 이름의 .json으로 저장한다.
API 키는 환경변수 ELEVENLABS_API_KEY 에서만 읽는다 (저장소에 넣지 않음).

사용:
  python narrate_api.py voices                                   # 내 보이스 이름·ID 목록
  python narrate_api.py <lines.json> <저장폴더> <voice_id> [줄번호 ...] [--suffix _Modi] [--dry-run]
    줄번호를 안 주면 전체. 이미 있는 파일은 건너뛴다. --dry-run 은 만들 파일과 글자 수만 보여 준다(키 불필요).
파일 이름은 1편과 같다: '{대본 문장}{suffix}.mp3' (윈도 파일명 금지 문자만 뺌)."""
import base64, json, os, re, sys
import requests

API = "https://api.elevenlabs.io/v1"
MODEL = "eleven_multilingual_v2"   # 한국어 지원 모델. 1편에서 웹으로 쓴 모델과 다르면 바꾼다


def key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        sys.exit("환경변수 ELEVENLABS_API_KEY 가 없습니다. ElevenLabs 웹 > Developers > API Keys 에서 만든 키를 설정하세요.")
    return {"xi-api-key": k}


def call(method, path, **kw):
    r = requests.request(method, API + path, headers=key(), timeout=120, **kw)
    if r.status_code != 200:
        sys.exit(f"ElevenLabs {r.status_code}: {r.text[:300]}")
    return r.json()


def name(line, suffix):
    return re.sub(r'[\\/:*?"<>|]', "", line).strip() + suffix


def main(argv):
    if argv[:1] == ["voices"]:
        for v in call("GET", "/voices")["voices"]:
            print(v["voice_id"], v["name"], v.get("category", ""))
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
    chars = sum(len(lines[n - 1]) for n in todo)
    print(f"만들 줄 {len(todo)}개, {chars}자")
    if dry:
        for n in todo: print(n, names[n - 1] + ".mp3")
        return

    sub = call("GET", "/user/subscription")
    left = sub["character_limit"] - sub["character_count"]
    print(f"이번 달 남은 글자 {left}자")
    if chars > left:
        sys.exit("남은 글자 수가 모자라 아무것도 만들지 않았습니다.")

    os.makedirs(out, exist_ok=True)
    for n in todo:
        text = lines[n - 1]
        r = call("POST", f"/text-to-speech/{voice}/with-timestamps",
                 params={"output_format": "mp3_44100_128"},
                 json={"text": text, "model_id": MODEL})
        base = f"{out}/{names[n - 1]}"
        open(base + ".mp3", "wb").write(base64.b64decode(r["audio_base64"]))
        json.dump({"text": text, "alignment": r["alignment"]}, open(base + ".json", "w", encoding="utf-8"),
                  ensure_ascii=False)
        print(n, names[n - 1] + ".mp3")


if __name__ == "__main__":
    main(sys.argv[1:])
