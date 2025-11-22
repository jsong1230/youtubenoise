# 작업 히스토리 (Work History)

이 문서는 프로젝트의 최근 작업 내역과 현재 상태를 상세히 기록합니다.  
**다른 머신이나 IDE에서 작업을 이어갈 때 이 문서를 먼저 확인하세요.**

---

## 📍 현재 상태 (2025-11-22)

### ✅ 최근 완료된 작업

#### 1. 프로세스 중복 실행 방지 시스템 구현 (2025-11-22)
- **`scripts/utils.py`에 `check_running_process()` 함수 추가**
  - Python 프로세스 확인 (zsh 셸 래퍼 제외)
  - FFmpeg 프로세스 확인 (같은 프리셋 관련)
  - psutil 사용, fallback으로 subprocess 사용
  - zsh 셸 래퍼(extendedglob, builtin, unsetopt 등) 필터링

- **`main.py`의 모든 모드에 중복 확인 로직 추가**
  - `longform_bgm` 모드
  - `spot_difference` 모드
  - `brain_training` 모드
  - `ai_explainer` 모드
  - 실행 전 반드시 `check_running_process()` 호출
  - 중복 발견 시 즉시 `sys.exit(1)`로 종료

- **`.cursorrules`에 프로세스 중복 실행 방지 규칙 추가**
  - 반드시 준수해야 할 사항 명시
  - 절대 금지 사항 명시
  - 예시 코드 포함

- **BGM 영상 생성 및 업로드**
  - piano_3h 영상 생성 및 YouTube 업로드 완료
  - rock_3h 영상 생성 및 YouTube 업로드 완료
  - world_3h 영상 생성 및 YouTube 업로드 진행 중

#### 1. 타입 힌팅 전면 적용 (2025-11-22)
- **`scripts/utils.py` 타입 힌팅 보완**
  - `Dict[str, Any]` 타입 추가 (`load_yaml_file`, `load_json_file`, `save_json_file`)
  - `Tuple[int, ...]` 타입 추가 (`retryable_status_codes`)
  - `Tuple[type, ...]` 타입 추가 (`exceptions`)
  - `Callable[[Callable[..., T]], Callable[..., T]]` 반환 타입 추가 (`retry_with_backoff`)

- **주요 스크립트들 타입 힌팅 추가**
  - `scripts/generate_bgm.py`: `load_bgm_presets()` → `Dict[str, Any]`
  - `scripts/upload_youtube.py`: `load_config()` → `Dict[str, Any]`, `get_authenticated_service()` → `Any`

- **mypy 정적 타입 체크 설정**
  - `mypy.ini` 설정 파일 생성
  - 외부 라이브러리 타입 스텁 없음 처리
  - 점진적 타입 체크 모드 설정

#### 2. 코드 품질 개선 (2025-11-22)
- **공통 유틸리티 모듈화** (`scripts/utils.py` 생성)
  - `setup_logging()`: 공통 로깅 설정
  - `check_ffmpeg()`: FFmpeg 설치 확인
  - `load_yaml_file()`, `load_json_file()`, `save_json_file()`: 파일 I/O 유틸리티
  - `get_project_root()`, `ensure_output_dir()`: 경로 유틸리티
  - `retry_with_backoff()`: 재시도 데코레이터 (지수 백오프)
  - `handle_api_error()`: API 에러 처리
  - `safe_execute()`: 안전한 함수 실행

- **로깅 설정 통합** (14개 파일 업데이트)
  - 모든 스크립트가 `setup_logging()` 사용하도록 변경
  - 중복된 `logging.basicConfig()` 제거
  - 업데이트된 파일:
    - `scripts/upload_youtube.py`
    - `scripts/sync_channel_state.py`
    - `scripts/generate_audio.py`
    - `scripts/generate_spot_difference_image.py`
    - `scripts/generate_spot_difference_metadata.py`
    - `scripts/generate_brain_training_content.py`
    - `scripts/generate_brain_training_metadata.py`
    - `scripts/update_statistics.py`
    - `scripts/download_public_domain_music.py`
    - `scripts/download_public_domain_images.py`
    - `scripts/pixabay_genre_downloader.py`
    - `scripts/organize_music_by_genre.py`
    - `scripts/pixabay_christmas_downloader.py`
    - 기타 주요 스크립트들

- **에러 처리 표준화**
  - `retry_with_backoff` 데코레이터 추가
  - API Provider에 재시도 로직 적용:
    - `src/api/providers/openai_provider.py`: `generate_text()` 재시도
    - `src/api/providers/claude_provider.py`: `generate_text()` 재시도
    - `src/api/providers/image_provider.py`: `download_from_unsplash()` 재시도

#### 2. 이전 완료 작업 (2025-11)

- **이중언어 메타데이터 시스템** (2025-11-21)
  - 한글/영어 자동 생성
  - 기본 언어: 영어 (영어 우선)
  - `generate_title_description.py` 업데이트
  - 프리셋 YAML에 `languages`, `region_targets` 필드 추가

- **AI Explainer 콘텐츠 필러** (2025-11-21)
  - Claude 3.5 Sonnet 사용
  - `scripts/generate_ai_explainers.py`: 스크립트 생성
  - `scripts/make_ai_explainer_video.py`: 영상 제작
  - `data/ai_explainer_topics.yaml`: 주제 관리

- **스케줄링 & 자동화 시스템** (2025-11-21)
  - `scripts/scheduler.py`: 요일별 필러 로테이션
  - `data/upload_schedule.yaml`: 스케줄 설정
  - `main.py`에 `--mode auto` 옵션 추가

- **API Manager 구현** (2025-11-20)
  - `src/api/api_manager.py`: 중앙 API 관리
  - `src/api/usage_tracker.py`: 사용량 추적
  - `src/api/providers/`: OpenAI, Claude, Image Provider

- **Flask 웹 대시보드** (2025-11-20)
  - `src/web/app.py`: Flask 앱
  - `src/web/routes/`: 대시보드, API 라우트
  - `run_dashboard.py`: 대시보드 실행 스크립트

---

## 🔄 현재 작업 중인 항목

**없음** - 타입 힌팅 전면 적용 완료

---

## 📋 다음 단계 (우선순위 순)

### 1. 단위 테스트 추가
- `pytest` 설정
- 주요 함수 단위 테스트 작성
- API Provider 테스트

### 3. 기능 개선
- 틀린그림찾기: 다양한 테마 및 난이도 프리셋 추가
- BGM: 다양한 장르 프리셋 추가
- 영상 메타데이터 최적화 (SEO 개선)

---

## 🗂️ 프로젝트 구조

```
youtubenoise/
├── scripts/                    # 실행 스크립트들
│   ├── utils.py               # ⭐ 공통 유틸리티 (최신)
│   ├── generate_bgm.py         # 롱폼 BGM 생성
│   ├── generate_image.py       # 배경 이미지 생성
│   ├── generate_title_description.py  # 메타데이터 생성
│   ├── make_video.py           # 영상 생성
│   ├── upload_youtube.py        # YouTube 업로드
│   ├── scheduler.py             # 자동 스케줄링
│   ├── generate_spot_difference*.py  # 틀린그림찾기
│   ├── generate_brain_training*.py   # 브레인트레이닝
│   └── generate_ai_explainers.py    # AI Explainer
│
├── src/
│   ├── api/                    # API 통합
│   │   ├── api_manager.py      # 중앙 API 관리
│   │   ├── usage_tracker.py    # 사용량 추적
│   │   └── providers/          # API Provider들
│   │       ├── openai_provider.py
│   │       ├── claude_provider.py
│   │       └── image_provider.py
│   │
│   └── web/                     # Flask 웹 대시보드
│       ├── app.py
│       ├── routes/
│       └── templates/
│
├── config/                      # 설정 파일
│   ├── config.json
│   ├── bgm_presets.yaml
│   └── ...
│
├── data/                        # 데이터 파일 (Git 추적)
│   ├── channel_state.json       # 채널 상태
│   ├── api_usage.json           # API 사용량
│   └── upload_schedule.yaml     # 업로드 스케줄
│
├── docs/                        # 문서
│   ├── CURSOR_PROMPT.md         # Cursor AI 가이드
│   └── ...
│
├── main.py                      # CLI 엔트리포인트
├── HISTORY.md                   # 프로젝트 히스토리
├── WORK_HISTORY.md              # ⭐ 작업 히스토리 (이 파일)
└── TODO.md                      # TODO 목록
```

---

## 🔑 주요 변경사항 요약

### 코드 품질 개선 (2025-11-22)

**변경 전:**
```python
# 각 스크립트마다 중복된 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```

**변경 후:**
```python
from scripts.utils import setup_logging

logger = setup_logging()
```

**변경 전:**
```python
# 각 스크립트마다 중복된 파일 로드
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
except FileNotFoundError:
    logger.error(f"파일을 찾을 수 없습니다: {config_path}")
    raise
```

**변경 후:**
```python
from scripts.utils import load_json_file

return load_json_file(CONFIG_JSON_FILE)
```

---

## 🚀 빠른 시작 가이드

### 1. 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt

# .env 파일 설정 (필수 API 키)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REFRESH_TOKEN=...
```

### 2. 프로젝트 상태 확인
```bash
# 최신 상태 확인
git pull

# 작업 히스토리 확인
cat WORK_HISTORY.md

# TODO 확인
cat TODO.md
```

### 3. 주요 명령어
```bash
# BGM 생성
python main.py --mode longform_bgm --preset cafe_jazz_3h

# 틀린그림찾기 생성
python main.py --mode spot_difference --preset senior_easy

# AI Explainer 생성
python main.py --mode ai_explainer --topic "ChatGPT로 코딩하기"

# 자동 스케줄 실행
python main.py --mode auto

# 웹 대시보드 실행
python run_dashboard.py
```

---

## 📝 작업 기록 형식

새로운 작업을 시작할 때는 이 문서를 업데이트하세요:

```markdown
## 📍 현재 상태 (YYYY-MM-DD)

### ✅ 최근 완료된 작업
- 작업 내용
- 변경된 파일
- 주요 변경사항

### 🔄 현재 작업 중인 항목
- 진행 중인 작업
- 예상 완료 시기

### 📋 다음 단계
- 우선순위별 다음 작업
```

---

## 🔍 문제 해결

### Import 에러 발생 시
```bash
# 프로젝트 루트에서 실행 확인
cd /path/to/youtubenoise
python -c "from scripts.utils import setup_logging; print('OK')"
```

### 로깅이 작동하지 않을 때
- `scripts/utils.py`의 `setup_logging()` 함수 확인
- `logs/app.log` 파일 권한 확인

### API 호출 실패 시
- `src/api/providers/`의 재시도 로직 확인
- `logs/app.log`에서 에러 메시지 확인

---

**마지막 업데이트**: 2025-11-22  
**작성자**: AI Assistant (Cursor)  
**목적**: 다른 머신/IDE에서 작업 이어가기

