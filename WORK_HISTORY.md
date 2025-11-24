# 작업 히스토리 (Work History)

이 문서는 프로젝트의 최근 작업 내역과 현재 상태를 상세히 기록합니다.  
**다른 머신이나 IDE에서 작업을 이어갈 때 이 문서를 먼저 확인하세요.**

---

## 📍 현재 상태 (2025-11-24)

### ✅ 최근 완료된 작업

#### 1. 두뇌훈련 영상 UI 개선 및 버그 수정 (2025-11-24)
- **질문 텍스트 줄바꿈 개선**
  - `create_text_image` 함수에서 긴 질문이 옆으로 잘리는 문제 수정
  - `wrap_text` 함수를 사용하여 텍스트 자동 줄바꿈 처리
  - 화면 중앙에 여러 줄로 배치되도록 개선
  
- **정답 화면 중앙 배치**
  - `create_answer_image` 함수에서 정답 텍스트를 화면 중앙에 배치하도록 수정
  - 정답 텍스트의 총 높이를 계산하여 화면 중앙에 정확히 배치
  - 제목과 정답 텍스트 간격 조정
  
- **계산 문제 폰트 크기 고정 (재수정)**
  - `create_calculation_display_image` 함수에서 폰트 크기를 절대값으로 고정 (최소 250px)
  - `font_size`에 의존하지 않고 절대값 사용하여 일관성 유지
  - 폰트 크기가 변하는 문제 완전 해결
  
- **한글 텍스트에 영어 단어 섞임 문제 수정**
  - `generate_shape_matching_problem` 함수에서 한글 텍스트에 영어 도형명이 섞이는 문제 수정
  - `shape_names_ko` 딕셔너리를 먼저 정의하고 한글 도형명 사용
  - GPT 생성 텍스트에도 한글 도형명 사용하도록 프롬프트 개선
  - 생성된 텍스트에 영어가 섞여있는지 검증 및 자동 수정 로직 추가
  
- **패턴 순서 문제 검증 로직 추가**
  - GPT가 생성한 패턴의 필수 필드 검증
  - 명백히 잘못된 패턴은 자동 재생성
  - 패턴 설명이 너무 짧거나 모호한 경우 경고 로그 출력
  
- **BGM 프리셋 문제 해결**
  - `data/bgm_presets.yaml`에 `piano` 프리셋 추가
  - `piano` 폴더에서 음악 자동 선택되도록 설정 완료
  
- **수정된 파일**
  - `scripts/make_brain_training_video.py`: 텍스트 줄바꿈, 정답 중앙 배치, 계산 폰트 고정
  - `scripts/generate_brain_training_content.py`: 패턴 검증 로직 추가
  - `data/bgm_presets.yaml`: piano 프리셋 추가

#### 2. 두뇌훈련 모듈 확장 (2025-11-23)
- **틀린그림 찾기 기능 비활성화**
  - DALL-E로 같은 장면의 두 이미지를 생성하는 것이 어려워 기능 비활성화
  - `missing_object` 모듈 및 `missing_object_senior` 프리셋 주석 처리
  - `mixed_brain_training_senior`에서 `missing_object` 모듈 제거 및 가중치 재분배

- **두뇌훈련 모듈 5개 추가 (총 10개 모듈)**
  - **1순위 모듈 (3개)**
    - `color_memory` (색상 기억): 4개 색상 박스를 순서대로 기억하는 훈련
    - `simple_calculation` (간단한 계산): 덧셈/뺄셈 문제
    - `direction_memory` (방향 기억): 4개 화살표 방향을 순서대로 기억하는 훈련
  - **2순위 모듈 (2개)**
    - `category_classification` (카테고리 분류): 여러 항목 중 카테고리에 속하지 않는 것 찾기
    - `shape_matching` (도형 매칭): 주어진 도형과 같은 도형 찾기 (원, 사각형, 삼각형, 직사각형, 별, 다이아몬드)
  
- **구현 내용**
  - `scripts/generate_brain_training_content.py`: 5개 모듈의 문제 생성 함수 추가
  - `scripts/make_brain_training_video.py`: 이미지 생성 함수 및 비디오 클립 생성 로직 추가
  - `config/brain_training_presets.yaml`: 모듈 정의 추가 및 `mixed_brain_training_senior` 프리셋에 가중치 추가
  - `scripts/generate_brain_training_metadata.py`: 모듈 이름 추가
  - `docs/BRAIN_TRAINING_MODULE_IDEAS.md`: 모듈 아이디어 문서 생성

- **현재 사용 가능한 모듈 (총 10개)**
  1. number_memory (숫자 기억)
  2. pattern_sequence (패턴 순서)
  3. word_association (단어 연상)
  4. clock_reading (시계 읽기)
  5. korean_word_puzzle (한글 퍼즐)
  6. color_memory (색상 기억) ⭐ 새로 추가
  7. simple_calculation (간단한 계산) ⭐ 새로 추가
  8. direction_memory (방향 기억) ⭐ 새로 추가
  9. category_classification (카테고리 분류) ⭐ 새로 추가
  10. shape_matching (도형 매칭) ⭐ 새로 추가

- **15분 영상 구성 가능**
  - 10개 모듈 × 평균 1.5분 = 15분 이상 영상 생성 가능
  - 각 모듈별 가중치 조정으로 골고루 분배

#### 2. 두뇌훈련 영상 다국어 지원 및 로직 개선 (2025-11-23)
- **틀린그림 찾기 로직 개선**
  - 기존: 원본 이미지에서 물건을 가리는 방식 (비교 불가능)
  - 변경: DALL-E로 원본 이미지 생성 후, 같은 장면에서 특정 물건이 없는 새 이미지를 별도로 생성
  - `generate_missing_object_problem`에서 원본과 수정본 이미지를 각각 DALL-E로 생성
  - 같은 그림에서 물건이 제거된 진정한 "틀린그림 찾기" 구현

- **다국어 옵션 개선**
  - 기존: `languages: ["ko", "en"]`이면 한글과 영어를 동시에 표시
  - 변경: 프리셋의 첫 번째 언어만 사용하도록 수정
  - `languages: ["ko"]` → 한글만 표시
  - `languages: ["en"]` → 영어만 표시
  - 문제 소개 화면과 정답 화면 모두 단일 언어로 표시

- **한글/영어 다국어 지원 구현**
  - 문제 생성 함수들에 `languages` 파라미터 추가
  - GPT API를 활용한 다국어 텍스트 자동 생성
  - 텍스트 이미지 생성 함수에 다국어 표시 기능 추가 (한글 위, 영어 아래)
  - 정답 화면에도 다국어 지원 추가

- **문제 반복 문제 수정**
  - 시계 읽기 문제: `problem_index`를 사용하여 시간을 순환 생성 (12시간 × 2분 = 24가지 조합)
  - 패턴 순서 문제: `problem_index`로 패턴 타입 다양화, GPT temperature 증가 (0.8 → 1.0)
  - 단어 연상 문제: `problem_index` 추가, GPT 프롬프트에 다양성 요구
  - 한글 퍼즐 문제: `problem_index` 추가, GPT temperature 증가

- **프리셋 경로 수정**
  - `DATA_DIR / "brain_training_presets.yaml"` → `config/brain_training_presets.yaml`
  - 프리셋 파일이 올바른 위치에서 로드되도록 수정

- **한글 테스트 영상 생성**
  - 10개 문제로 설정 (골고루 분배)
  - 모듈 구성: number_memory, missing_object, pattern_sequence, word_association, clock_reading, korean_word_puzzle
  - 한글 전용으로 설정 (`languages: ["ko"]`)

#### 2. 프로세스 중복 실행 방지 시스템 구현 (2025-11-22)
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

### 📋 다음 단계 (2025-11-23)
- 이미지 다운로드 타임아웃 에러 해결 (재시도 로직 추가)
- 영어 테스트 영상 생성
- 영상 품질 검증 및 개선
- 틀린그림 찾기 이미지 품질 개선 (DALL-E 프롬프트 최적화)

### 📋 다음 단계 (이전)
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

**마지막 업데이트**: 2025-11-23 (두뇌훈련 모듈 5개 추가 완료)  
**작성자**: AI Assistant (Cursor)  
**목적**: 다른 머신/IDE에서 작업 이어가기

