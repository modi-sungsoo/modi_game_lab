# modi_game_lab

게임 개발 유튜브 채널 작업용 스크립트 모음.

## youtube/ep01 — 디자인빌리지 개발일지 1편 "AI 딸깍 게임에 재미는 어떻게 입힐까요"

ffmpeg 7 + Python 3 (Pillow) 로 만든 편집 스크립트. 결과물(영상·음성·썸네일)은 `Desktop\유튜브\` 의 1편 폴더에 있고 여기엔 스크립트만 둔다.

| 단계 | 스크립트 | 하는 일 |
|---|---|---|
| 1. 클립 | `build_ep1.py [--1080]` | 녹화본에서 장면별 클립(웹_01~09, 정산_01, 언리얼_02) 만들기 |
| | `make_assets.py` | 건물 타일 잘라내기 + 정산표 카드 이미지 |
| | `join_ep1.py` | 클립 합치기 + 합본 자막 |
| 2. 나레이션 | `lines.json` | 대본 57줄 |
| | `place_nar.py`, `place_modi.py` | ElevenLabs 다운로드 mp3 를 대본 이름으로 옮기기 (태형 / ModiSungSoo) |
| | `check_nar.py`, `narrate_ep1.py` | 나레이션 확인, 나레이션 입힌 합본 |
| 3. 최종본 | `final_ep1.py`, `final_modi.py` | Vrew 타임라인대로 나레이션·효과음·BGM 합쳐 최종본 |
| 4. 썸네일 | `make_thumbs.py`, `make_thumb_a2.py` | 유튜브 썸네일 시안 / 최종(A2) |
| | `make_insta_cover.py` | 인스타 릴스 커버 1080x1920 |
| 5. 세로 | `make_shorts.py`, `make_shorts_hl.py` | 쇼츠·릴스 58초 / 하이라이트 26초 |
| | `make_vertical_full.py` | 본편 전체 세로 영상 |
| | `speed125.py <이름>...` | 인스타용 1.25배속 (+자막 시간 맞춤) |

### 다시 쓸 때 주의
- 많은 스크립트가 예전 위치 `C:/Users/user/Videos` 를 가리킨다. 2026-11-19 에 결과물이 `Desktop/유튜브/{영상,썸네일,나레이션,효과음,배경음악}/1. AI 딸깍 게임에 재미는 어떻게 입힐까요/` 로 옮겨졌으니 맨 위 경로 상수를 바꿔서 쓴다.
- 세로 영상 스크립트는 자막 없는 본편 `modi_tmp/body.mp4` 가 필요하다 (`final_modi.py` 가 만듦, 용량 때문에 git 제외).
- `thumb/f1680.png` 는 썸네일에 쓰는 게임 화면 프레임.
