# YouTube Longform Generator

GPT · Claude · Public Domain 음악 · FFmpeg을 조합해 **다양한 주제의 롱폼 영상**을 자동으로 제작하는 파이프라인입니다.  
**2025 전략**: 이중언어 메타데이터, API 비용 최적화, 요일별 필러 로테이션, AI Explainer 콘텐츠 추가  
화이트노이즈/환경음에 머무르지 않고, **BGM·시니어 브레인트레이닝·AI Explainer** 등 여러 포맷을 선택적으로 생성할 수 있습니다.  
각 파이프라인은 이미지/오디오/텍스트를 자동 생성하고, 최종 MP4와 메타데이터 파일을 산출합니다.  
**모든 모드에서 DALL-E를 사용한 썸네일이 자동으로 생성됩니다.**

> **📌 다른 머신/IDE에서 작업 시작하기**: [`QUICK_START.md`](QUICK_START.md)를 먼저 읽으세요.  
> **📋 작업 히스토리 확인**: [`WORK_HISTORY.md`](WORK_HISTORY.md)에서 최근 작업 내역과 현재 상태를 확인하세요.

## 핵심 콘셉트

| 모드 (`--mode`) | 설명 | 프리셋 예시 |
| --- | --- | --- |
| `longform_bgm` | Public Domain 음악 또는 합성 음원을 조합한 2~6시간 BGM | `cafe_jazz_3h`, `blues_3h`, `lofi_3h`, `christmas_ambient_4h` |
| `brain_training` | GPT 문제 생성 기반 시니어 두뇌훈련 (한글/영어 지원) | `number_memory_senior`, `mixed_brain_training_senior` |
| `ai_explainer` | Claude로 생성한 AI & Tech 설명 롱폼 영상 | `ChatGPT로 코딩하기: 실전 팁` |
| `auto` | 요일별 스케줄에 따라 자동 실행 | `data/upload_schedule.yaml` 참고 |
| (Legacy) noise | 전통적인 노이즈/환경음 합성 스크립트 | `white_noise`, `rain`, `asmr` |

필요한 프리셋만 지정하면 **이미지→오디오→영상→메타데이터**까지 한 번에 생성됩니다.  
YouTube 업로드는 `--upload` 옵션으로 자동화하거나, 생성된 파일을 수동 검토 후 올릴 수 있습니다.

## 프로젝트 구조

```
youtubenoise/
  audio/
    public_domain/              # 장르별 Public Domain 음악
  images/                       # 생성된 배경 이미지
  scripts/
    generate_bgm.py             # 롱폼 BGM
    generate_image.py           # 배경 이미지
    generate_audio.py           # 노이즈/환경음
    make_video.py               # BGM/노이즈 영상
    upload_youtube.py           # (옵션) 업로드
    scheduler.py                # 배치 실행
    generate_brain_training*.py # 브레인트레이닝
    create_thumbnail_dalle.py  # 썸네일 생성 (DALL-E)
    upload_thumbnail.py         # 썸네일 업로드
  config/
    config.json                 # 공통 설정
    bgm_presets.yaml
    brain_training_presets.yaml
  docs/                         # 가이드 모음
  logs/app.log
  main.py                       # CLI 엔트리포인트
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
# 필수: OpenAI API (텍스트/이미지 생성)
OPENAI_API_KEY=sk-...

# 필수: Claude API (비용 절감을 위한 대안, 텍스트 생성)
ANTHROPIC_API_KEY=sk-ant-...
# 또는
CLAUDE_API_KEY=sk-ant-...

# YouTube 업로드 자동화를 사용할 경우
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REFRESH_TOKEN=...

# 선택: 무료 이미지 API (비용 절감)
UNSPLASH_ACCESS_KEY=...
PEXELS_API_KEY=...
PIXABAY_API_KEY=...
```

### API 키 발급 가이드

- **OpenAI API**: [platform.openai.com](https://platform.openai.com/api-keys)에서 발급
  - GPT-4o, GPT-4o-mini (텍스트 생성)
  - DALL-E 3 (이미지 생성)
  
- **Claude API**: [console.anthropic.com](https://console.anthropic.com/)에서 발급
  - Claude 3.5 Sonnet (긴 텍스트 생성, 비용 효율적)
  - Claude 3.5 Haiku (짧은 텍스트 생성, 매우 저렴)
  - 비용 절감: GPT-4o-mini 대비 약 50% 저렴
  
- **YouTube OAuth**: Google Cloud Console에서 "데스크톱 앱" 클라이언트 생성 후 `.env`에 입력
  - `scripts/refresh_youtube_token.py` 실행하여 토큰 발급

- **무료 이미지 API** (선택사항):
  - Unsplash: [unsplash.com/developers](https://unsplash.com/developers)
  - Pexels: [pexels.com/api](https://www.pexels.com/api/)
  - Pixabay: [pixabay.com/api/docs](https://pixabay.com/api/docs/)

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

### 2. 시니어 브레인트레이닝
```bash
python main.py --mode brain_training --preset number_memory_senior
python main.py --mode brain_training --preset mixed_brain_training_senior
python main.py --mode brain_training --preset brain_training_30min_korean  # 30-45분 영상
python main.py --mode brain_training --preset brain_training_30min_english  # 30-45분 영상 (영어)
```
- GPT가 문제와 자막을 생성하고, Python이 카드/카운트다운을 렌더링합니다.
- BGM 자동 포함: `audio/public_domain/` 폴더의 오디오 파일을 랜덤 선택하여 영상 길이에 맞춰 자동 반복 재생합니다.
- 영상 길이: 프리셋의 `num_problems`와 `problem_settings`에 따라 자동 계산되며, 메타데이터에 정확한 길이가 포함됩니다.

### 3. AI Explainer (AI & Tech 설명 영상)
```bash
# 주제 목록 보기
python scripts/generate_ai_explainers.py --list-topics

# 전체 파이프라인 실행 (스크립트 생성 → 영상 제작 → 메타데이터 생성)
python main.py --mode ai_explainer --preset "ChatGPT로 코딩하기: 실전 팁"

# 스크립트만 생성
python scripts/generate_ai_explainers.py --topic "ChatGPT로 코딩하기: 실전 팁"
```
- Claude 3.5 Sonnet으로 긴 스크립트 생성 (Hook → Sections → Outro 구조)
- B-roll 이미지 자동 삽입
- 이중언어 메타데이터 자동 생성

### 5. 자동 스케줄링 (요일별 필러 로테이션)
```bash
# 오늘의 스케줄에 따라 자동 실행
python main.py --mode auto

# 언어 지정하여 자동 실행
python main.py --mode auto --language ko
```
- `data/upload_schedule.yaml`에 정의된 스케줄에 따라 자동 실행
- 월: Brain Training, 화: Spot Difference, 수: Focus BGM 등
- 스케줄 수정은 `data/upload_schedule.yaml` 편집

### 6. (Legacy) 노이즈/환경음
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

### 웹 대시보드
```bash
# Flask 웹 대시보드 실행
python run_dashboard.py

# 브라우저에서 접속
# http://localhost:5001 - 대시보드
# http://localhost:5001/videos - 영상 목록
# http://localhost:5001/api/stats - 채널 통계 JSON
# http://localhost:5001/api/usage - API 사용량 JSON
```

**대시보드 기능:**
- 채널 통계 실시간 모니터링 (조회수, 구독자, 시청 시간)
- 영상 목록 및 성과 지표 (조회수, 좋아요, 댓글)
- API 사용량 및 비용 추적 (일별/월별)
- 자동 새로고침 (30초마다)

### 채널 상태 동기화
```bash
# YouTube API로 채널 통계 동기화
python -m scripts.sync_channel_state

# 주기적 실행 (cron 예시)
0 */6 * * * cd /path/to/youtubenoise && /path/to/venv/bin/python -m scripts.sync_channel_state
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

## API Manager & 비용 최적화

프로젝트에는 통합 API 관리 시스템이 포함되어 있어 **비용을 96% 절감**할 수 있습니다:

```python
from src.api.api_manager import APIManager

# API Manager 초기화
api = APIManager()

# 텍스트 생성 (자동으로 최적 API 선택)
result = api.generate_text(
    prompt="YouTube 영상 제목을 생성해주세요",
    length="short",  # "short", "medium", "long"
    priority="cost"  # "cost", "quality", "speed"
)
# 비용 우선: Claude Haiku 선택 (GPT-4o-mini 대비 50% 저렴)

# 이미지 생성 (DALL-E 우선, 실패 시 무료 API)
image_path = api.generate_image(
    prompt="calm ocean sunset",
    use_dalle=True  # True면 DALL-E 우선, False면 무료 API 우선
)

# JSON 생성 (Claude 우선)
metadata = api.generate_json(
    prompt="YouTube 메타데이터를 JSON으로 생성해주세요",
    provider="claude"  # Claude Haiku 사용 (비용 효율적)
)
```

### 지원 API 및 비용 비교

| API | 용도 | 비용 (1K 토큰) | 특징 |
|-----|------|---------------|------|
| **Claude 3.5 Haiku** | 짧은 텍스트 | $0.25 | 매우 저렴, 빠름 |
| **Claude 3.5 Sonnet** | 긴 텍스트 | $3.00 | GPT-4o 대비 저렴 |
| **GPT-4o-mini** | 텍스트 | $0.15 | 저렴, 안정적 |
| **GPT-4o** | 텍스트 | $5.00 | 고품질 |
| **DALL-E 3** | 이미지 | $0.04/이미지 | 고품질 |
| **Unsplash/Pexels/Pixabay** | 이미지 | 무료 | 다운로드만 |

### 비용 절감 전략
1. **텍스트 생성**: Claude Haiku 우선 사용 (짧은 텍스트)
2. **긴 스크립트**: Claude Sonnet 사용 (AI Explainer 등)
3. **이미지**: DALL-E 우선, 실패 시 무료 API 사용
4. **자동 추적**: `data/api_usage.json`에 일별/월별 비용 저장

자세한 전략은 `docs/API_INTEGRATION_STRATEGY.md` 참고.

## 문서

- `docs/README.md` : 활성 문서 vs 레거시 문서 정리
- `docs/MUSIC_GUIDE.md`, `docs/PUBLIC_DOMAIN_GENRES.md` : 음악 다운로드
- `docs/STATISTICS.md` : YouTube 통계 관리
- `docs/API_INTEGRATION_STRATEGY.md` : API 통합 전략 및 비용 절감
- `docs/CURSOR_PROMPT.md` : Cursor AI 가이드
- `implementation_plan.md` : 2025 전략 구현 계획
- 레거시 노이즈 관련 문서는 "Legacy" 섹션에서 확인할 수 있습니다.

## 로그 및 히스토리

- `logs/app.log`: 모든 스크립트의 실행 로그
- `logs/history.json`: 업로드된 영상의 히스토리 (video ID, 생성 시간, 통계 등)

## 자동 스케줄링

### 방법 1: 자동 모드 사용 (권장)
```bash
# 매일 오전 9시에 오늘의 스케줄에 따라 자동 실행
0 9 * * * cd /path/to/youtubenoise && /path/to/venv/bin/python main.py --mode auto >> logs/cron.log 2>&1
```

### 방법 2: 수동 스케줄링
```bash
# 특정 모드/프리셋 지정
0 2 * * * cd /path/to/youtubenoise && /path/to/venv/bin/python main.py --mode longform_bgm --preset cafe_jazz_3h --duration-minutes 180 >> logs/cron.log 2>&1
```

**스케줄 수정**: `data/upload_schedule.yaml` 파일을 편집하여 요일별 콘텐츠 필러 변경

## 이중언어 메타데이터

프로젝트는 **한글/영어 이중언어 메타데이터**를 자동 생성합니다:

- **제목**: "한국어 제목 | English Title (duration)"
- **설명**: Section 1 (한국어) → Section 2 (영어) → Section 3 (혼합)
- **태그**: 양 언어 혼합

프리셋에 `languages: ["en", "ko"]` 필드가 있으면 자동으로 이중언어 메타데이터가 생성됩니다.
기본값은 영어 우선입니다.

## 🔍 타입 체크

프로젝트는 `mypy`를 사용한 정적 타입 체크를 지원합니다:

```bash
# mypy 설치 (선택사항)
pip install mypy

# 타입 체크 실행
mypy scripts/
mypy src/
```

설정 파일: `mypy.ini`

## 주의사항 & 문제 해결

1. **저작권**: Public Domain/CC0 또는 직접 합성한 자산만 사용하세요.
2. **YouTube 정책**: 자동화된 콘텐츠도 커뮤니티 가이드라인을 준수해야 합니다.
3. **API 비용**: Claude API 사용으로 비용을 크게 절감할 수 있습니다. 사용량은 `data/api_usage.json`에서 확인.
4. **FFmpeg 필수**: 설치 및 PATH 등록 여부를 `ffmpeg -version`으로 확인.
5. **업로드 오류**: `.env`의 OAuth 정보, API 활성화 여부, 토큰 만료를 점검하세요.
6. **Claude API**: `ANTHROPIC_API_KEY` 또는 `CLAUDE_API_KEY` 환경변수 설정 필요.

### Public Domain 음악이 인식되지 않을 때
- `audio/public_domain/<genre>/` 경로가 맞는지 확인
- 파일 권한 및 로그(`logs/app.log`) 확인
- `public_domain_catalog.py`를 실행해 카탈로그 재생성

## 라이선스 & 기여

- 개인 사용/학습용 템플릿입니다.
- 버그 리포트와 기능 제안은 GitHub Issues로 남겨주세요.
