# YouTube Longform Generator

GPT · Public Domain 음악 · FFmpeg을 조합해 **다양한 주제의 롱폼 영상**을 자동으로 제작하는 파이프라인입니다.  
화이트노이즈/환경음에 머무르지 않고, **BGM·시니어 브레인트레이닝·틀린그림찾기** 등 여러 포맷을 선택적으로 생성할 수 있도록 리팩토링되었습니다.  
각 파이프라인은 이미지/오디오/텍스트를 자동 생성하고, 최종 MP4와 메타데이터 파일을 산출합니다.

## 핵심 콘셉트

| 모드 (`--mode`) | 설명 | 프리셋 예시 |
| --- | --- | --- |
| `longform_bgm` | Public Domain 음악 또는 합성 음원을 조합한 2~6시간 BGM | `cafe_jazz_3h`, `blues_3h`, `lofi_3h`, `christmas_ambient_4h` |
| `spot_difference` | GPT 이미지/분석을 활용한 시니어용 틀린그림찾기(10~20 문제) | `senior_easy`, `senior_normal` |
| `brain_training` | GPT 문제 생성 기반 시니어 두뇌훈련 | `number_memory_senior`, `mixed_brain_training_senior` |
| (Legacy) noise | 전통적인 노이즈/환경음 합성 스크립트 | `white_noise`, `rain`, `asmr` |

필요한 프리셋만 지정하면 **이미지→오디오→영상→메타데이터**까지 한 번에 생성됩니다.  
YouTube 업로드는 `--upload` 옵션으로 자동화하거나, 생성된 파일을 수동 검토 후 올릴 수 있습니다.

## 프로젝트 구조

```
```
youtubenoise/
  audio/
    public_domain/              # 장르별 Public Domain 음악
  images/                       # 생성된 배경/틀린그림찾기 이미지
  videos/
    spot_difference/
  scripts/
    generate_bgm.py             # 롱폼 BGM
    generate_image.py           # 배경 이미지
    generate_audio.py           # 노이즈/환경음
    make_video.py               # BGM/노이즈 영상
    upload_youtube.py           # (옵션) 업로드
    scheduler.py                # 배치 실행
    generate_spot_difference*.py# 틀린그림찾기 파이프라인
    make_spot_difference_video.py
    generate_brain_training*.py # 브레인트레이닝
  config/
    config.json                 # 공통 설정
    bgm_presets.yaml
    spot_difference_presets.yaml
    brain_training_presets.yaml
  docs/                         # 가이드 모음
  logs/app.log
  main.py                       # CLI 엔트리포인트
```
```

## 설치 방법

### 1. 저장소 클론 또는 다운로드

```bash
cd /path/to/youtubenoise
```

### 2. Python 가상환경 생성 및 활성화 (권장)

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. FFmpeg 설치

FFmpeg는 영상 생성에 필요합니다.

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
[FFmpeg 공식 사이트](https://ffmpeg.org/download.html)에서 다운로드하거나 Chocolatey로 설치:
```bash
choco install ffmpeg
```

## 환경 변수 (.env)

```bash
OPENAI_API_KEY=sk-...

# YouTube 업로드 자동화를 사용할 경우
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REFRESH_TOKEN=...

# 선택: 이미지/API 다운로드용 키
UNSPLASH_ACCESS_KEY=...
PEXELS_API_KEY=...
PIXABAY_API_KEY=...
```

- OpenAI 키는 [platform.openai.com](https://platform.openai.com/api-keys)에서 발급
- YouTube OAuth는 Google Cloud Console에서 “데스크톱 앱” 클라이언트 생성 후 `.env`에 입력

## 실행 방법

### 1. 롱폼 BGM
```bash
# 프리셋 목록 출력
python main.py --list-presets

# 3시간 카페 재즈 BGM 생성 (로컬 저장)
python main.py --mode longform_bgm --preset cafe_jazz_3h --duration-minutes 180

# Public Domain 음악 활용 + YouTube 업로드
python main.py --mode longform_bgm --preset blues_3h --duration-minutes 180 --upload
```
- `audio/public_domain/<genre>/`에 MP3/WAV를 두면 자동 조합됩니다.
- 여러 파일이 있으면 길이에 맞게 이어붙입니다.
- 세부 스타일은 `config/bgm_presets.yaml`에서 조정합니다.

### 2. 시니어용 틀린그림찾기 (GPT 기반)
```bash
# 쉬운 난이도 (3개 차이, 15초 카운트다운, 15문제)
python main.py --mode spot_difference --preset senior_easy

# 보통 난이도 (5개 차이, 10초 카운트다운, 20문제)
python main.py --mode spot_difference --preset senior_normal
```
- DALL·E가 원본 이미지를 생성하고 GPT가 차이점·좌표 JSON을 제공합니다.
- 비교 화면 + 1초씩 줄어드는 카운트다운 + 정답 오버레이가 자동 합성됩니다.
- 결과물: `videos/spot_difference/<date>_<preset>_ep01.mp4`  
  메타데이터는 JSON/텍스트로 함께 저장됩니다.
- 자세한 가이드는 `docs/SPOT_DIFFERENCE_GUIDE.md` 참고.

### 3. 시니어 브레인트레이닝
```bash
python main.py --mode brain_training --preset number_memory_senior
python main.py --mode brain_training --preset mixed_brain_training_senior
```
- GPT가 문제와 자막을 생성하고, Python이 카드/카운트다운을 렌더링합니다.

### 4. (Legacy) 노이즈/환경음
```bash
python scripts/generate_audio.py white_noise
python scripts/generate_image.py white_noise
python scripts/make_video.py images/bg.png audio/white_noise.wav
```
- `scripts/scheduler.py`를 사용하면 기존 파이프라인 전체를 순차 실행할 수 있습니다.

### 통계 & 리포트
```bash
python main.py --update-stats   # YouTube 통계 동기화
python main.py --report         # 콘솔 리포트 출력
```

## 프리셋 & 확장성

- **BGM**: café jazz, blues, folk, lofi, classical, christmas ambient …
- **Spot Difference**: 난이도와 테마를 YAML로 정의 (차이점 개수, 카운트다운, 색상 스킴)
- **Brain Training**: 숫자 기억, 사라진 물건, 패턴 순서 등 모듈 조합
- **노이즈/환경음**: white/brown/pink noise, rain, ocean, fireplace, asmr …

모든 프리셋은 YAML 파일로 관리되어 새 장르/테마 추가가 쉽습니다.

## Public Domain 음악 (요약)

1. 추천 소스  
   - [FreePD](https://freepd.com/)  
   - [Pixabay Music](https://pixabay.com/music/)  
   - [Musopen](https://musopen.org/music/?license=pd)
2. 다운로드 후 `audio/public_domain/<genre>/`에 저장
3. BGM 생성 시 자동으로 선별·조합
4. `scripts/pixabay_genre_downloader.py`로 장르별 자동 다운로드 지원

세부 가이드는 `docs/MUSIC_GUIDE.md`, `docs/PUBLIC_DOMAIN_GENRES.md` 참고.

## 문서

- `docs/README.md` : 활성 문서 vs 레거시 문서 정리
- `docs/SPOT_DIFFERENCE_GUIDE.md` : 틀린그림찾기 파이프라인
- `docs/MUSIC_GUIDE.md`, `docs/PUBLIC_DOMAIN_GENRES.md` : 음악 다운로드
- `docs/STATISTICS.md` : YouTube 통계 관리
- 레거시 노이즈 관련 문서는 “Legacy” 섹션에서 확인할 수 있습니다.

## 로그 및 히스토리

- `logs/app.log`: 모든 스크립트의 실행 로그
- `logs/history.json`: 업로드된 영상의 히스토리 (video ID, 생성 시간, 통계 등)

## 자동 스케줄링 (cron 예시)
```bash
0 2 * * * cd /path/to/youtubenoise && /path/to/venv/bin/python main.py --mode longform_bgm --preset cafe_jazz_3h --duration-minutes 180 >> logs/cron.log 2>&1
0 5 * * 1 cd /path/to/youtubenoise && /path/to/venv/bin/python main.py --mode spot_difference --preset senior_easy >> logs/cron.log 2>&1
```

## 주의사항 & 문제 해결

1. **저작권**: Public Domain/CC0 또는 직접 합성한 자산만 사용하세요.
2. **YouTube 정책**: 자동화된 콘텐츠도 커뮤니티 가이드라인을 준수해야 합니다.
3. **OpenAI 비용**: gpt-4o-mini/gpt-4o는 저렴하지만 이미지 생성은 비용이 크므로 사용량 모니터링.
4. **FFmpeg 필수**: 설치 및 PATH 등록 여부를 `ffmpeg -version`으로 확인.
5. **업로드 오류**: `.env`의 OAuth 정보, API 활성화 여부, 토큰 만료를 점검하세요.

### Public Domain 음악이 인식되지 않을 때
- `audio/public_domain/<genre>/` 경로가 맞는지 확인
- 파일 권한 및 로그(`logs/app.log`) 확인
- `public_domain_catalog.py`를 실행해 카탈로그 재생성

## 라이선스 & 기여

- 개인 사용/학습용 템플릿입니다.
- 버그 리포트와 기능 제안은 GitHub Issues로 남겨주세요.
