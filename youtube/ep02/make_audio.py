"""2편 BGM 1곡과 연출 효과음을 ElevenLabs로 만든다. 이미 있는 파일은 건너뛴다(크레딧 절약).
사용: python make_audio.py
"""
import os, sys
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env.local"))
BGM_DIR = "C:/Users/user/Desktop/유튜브/배경음악/2편"
SFX_DIR = "C:/Users/user/Desktop/유튜브/효과음/2편"

BGM = ("BGM_Cozy_Workshop", 215_000,
       "Cozy, warm instrumental for an indie game dev log video. Light acoustic guitar, soft marimba, gentle brushed drums, "
       "warm bass. Calm and curious, steady tempo around 95 bpm, no vocals, no big drops, consistent energy so it sits under "
       "spoken narration. Ends with a soft resolved ending.")
SFX = [  # (이름, 길이 초, 설명)
    ("01_팝_프롬프트", 0.8, "Soft UI pop, a chat message bubble appearing, clean and short, no echo"),
    ("02_휙_전환", 1.0, "Quick soft whoosh transition, airy swipe, short"),
    ("03_카드_슬라이드", 1.2, "Paper card sliding onto a wooden table with a light soft tap at the end"),
    ("04_반짝_변신", 2.0, "Magical sparkle shimmer, gentle chimes rising, like simple shapes turning into colorful art"),
    ("05_알림_차임", 1.5, "Gentle two-note notification chime, friendly, a bit hesitant, UI alert"),
    ("06_타일_놓기", 0.8, "Wooden board game tile placed on a table, satisfying soft click"),
    ("07_마무리_징글", 3.0, "Short cheerful success jingle, xylophone and soft bells, warm ending for a video outro"),
]

key = os.environ.get("ELEVENLABS_API_KEY") or sys.exit("ELEVENLABS_API_KEY 가 없습니다.")
c = ElevenLabs(api_key=key)
for d in (BGM_DIR, SFX_DIR): os.makedirs(d, exist_ok=True)

for name, sec, text in SFX:
    p = f"{SFX_DIR}/{name}.mp3"
    if os.path.exists(p): continue
    data = b"".join(c.text_to_sound_effects.convert(text=text, duration_seconds=sec, prompt_influence=0.5,
                                                    output_format="mp3_44100_128"))
    open(p, "wb").write(data); print("효과음", p, flush=True)

name, ms, prompt = BGM
p = f"{BGM_DIR}/{name}.mp3"
if not os.path.exists(p):
    data = b"".join(c.music.compose(prompt=prompt, music_length_ms=ms, force_instrumental=True,
                                    output_format="mp3_44100_128"))
    open(p, "wb").write(data); print("BGM", p, flush=True)

s = c.user.subscription.get(); print(f"남은 글자 {s.character_limit - s.character_count}")
