# Project History - YouTube 롱폼 자동화

이 문서는 프로젝트의 시작부터 현재까지의 주요 결정사항과 변경 이력을 기록합니다.  
**다른 머신이나 IDE에서 작업을 이어갈 때 이 문서를 먼저 확인하세요.**

---

## 📅 Timeline

### 2025-11-25: 두뇌훈련 시계 및 색상 개선
- **시계 읽기 문제 개선**
  - 시계가 항상 12시가 위에 오도록 각도 계산 수정
  - 숫자 표시 위치 정확도 개선 (12, 3, 6, 9)
  - 시침과 분침 각도 계산 정확도 개선

- **색상 기억 문제 개선**
  - 색상 구분을 명확하게 하기 위해 더 밝고 선명한 RGB 값 사용
  - 파랑: (0, 0, 255) → (0, 100, 255)로 변경하여 더 선명하게
  - 초록: (0, 128, 0) → (0, 200, 0)로 변경하여 더 선명하게
  - 주황, 보라, 분홍 등도 더 밝고 선명하게 조정
  - 색상 박스 테두리를 더 두껍게 (width: 5 → 6, 외곽 테두리 width: 10 추가)
  - 하늘색, 연두색 추가로 색상 선택지 확대

### 2025-11-24: 썸네일 자동 생성 및 다국어 지원 개선
- **모든 모드에 썸네일 자동 생성 기능 추가**
  - `scripts/create_thumbnail_dalle.py` 신규 생성: DALL-E 3 기반 썸네일 생성 (1280x720)
  - `scripts/upload_thumbnail.py` 신규 생성: YouTube 썸네일 업로드
  - `scripts/upload_youtube.py`에 `compress_thumbnail` 함수 통합
  - `brain_training`, `longform_bgm`, `ai_explainer` 모드에 자동 썸네일 생성 로직 추가
  - 썸네일 경로를 메타데이터에 자동 포함

- **두뇌훈련 영상 다국어 지원 개선 및 버그 수정**
  - 영어 버전에서 한글 텍스트 제거 및 폰트 깨짐 문제 해결
  - 모든 이미지 생성 함수에 `languages` 파라미터 추가
  - 영어 버전일 때 영어 폰트(Helvetica) 사용, 한글 폰트(AppleSDGothicNeo)는 한글 버전에서만 사용
  - `korean_word_puzzle` 모듈을 영어 버전에서 자동 제외
  - 언어별 파일명 구분 (`_ko_`, `_en_` 식별자 추가)
  - 메타데이터, 제목, 설명, 태그 파일도 언어별로 구분

- **spot_difference 모드 제거**
  - 구현이 어려워 실제로 사용하지 않음
  - DALL-E로 동일한 이미지에서 차이점을 만드는 것이 일관성 있게 생성되지 않음
  - `main.py`에서 `spot_difference` 모드 제거
  - `README.md`에서 `spot_difference` 관련 설명 제거

- **30-45분 두뇌훈련 영상 생성 기능 추가**
  - `brain_training_30min_korean`, `brain_training_30min_english` 프리셋 추가
  - BGM 자동 포함 기능 (public_domain 폴더에서 랜덤 선택, 루프 반복)
  - 영상 길이 계산 및 메타데이터에 실제 길이 포함
  - DALL-E 3를 사용한 썸네일 자동 생성

- **생성된 파일 정리 및 히스토리 Git 포함**
  - 업로드 완료된 비디오 파일 및 메타데이터 삭제
  - 생성된 썸네일 파일 삭제
  - 생성된 오디오 파일 삭제
  - 히스토리 파일(`logs/history.json`, `output/logs/history.json`) Git에 포함
  - `.gitignore` 수정하여 히스토리 파일 포함 규칙 추가

### 2025-11-23: 두뇌훈련 모듈 확장 및 다국어 지원
- **두뇌훈련 모듈 5개 추가 (총 10개 모듈)**
  - `color_memory` (색상 기억): 4개 색상 박스를 순서대로 기억하는 훈련
  - `simple_calculation` (간단한 계산): 덧셈/뺄셈 문제
  - `direction_memory` (방향 기억): 4개 화살표 방향을 순서대로 기억하는 훈련
  - `category_classification` (카테고리 분류): 여러 항목 중 카테고리에 속하지 않는 것 찾기
  - `shape_matching` (도형 매칭): 주어진 도형과 같은 도형 찾기

- **두뇌훈련 영상 다국어 지원 및 로직 개선**
  - 프리셋의 첫 번째 언어만 사용하도록 수정 (`languages: ["ko"]` 또는 `["en"]`)
  - 문제 생성 함수들에 `languages` 파라미터 추가
  - GPT API를 활용한 다국어 텍스트 자동 생성
  - 문제 반복 문제 수정 (시계, 패턴 문제 다양성 확보)

- **틀린그림 찾기 기능 비활성화**
  - DALL-E로 같은 장면의 두 이미지를 생성하는 것이 어려워 기능 비활성화
  - `missing_object` 모듈 및 `missing_object_senior` 프리셋 주석 처리

### 2025-11-22: 코드 품질 개선 완료
- **목표**: 코드 중복 제거, 공통 유틸리티 모듈화, 에러 처리 표준화
- **주요 변경사항**:
  - `scripts/utils.py` 생성: 공통 유틸리티 함수 모듈화
  - 모든 스크립트(14개)가 `setup_logging()` 사용하도록 통합
  - `retry_with_backoff` 데코레이터 추가: API 호출 재시도 로직
  - API Provider에 재시도 로직 적용 (OpenAI, Claude, Image Provider)
  - 파일 I/O 유틸리티 통합 (`load_json_file`, `load_yaml_file` 등)
- **영향받은 파일**:
  - `scripts/utils.py` (신규)
  - `scripts/upload_youtube.py`, `scripts/sync_channel_state.py` 등 14개 파일
  - `src/api/providers/openai_provider.py`, `claude_provider.py`, `image_provider.py`

- **프로세스 중복 실행 방지 시스템 구현**
  - `scripts/utils.py`에 `check_running_process()` 함수 추가
  - `main.py`의 모든 모드에 중복 확인 로직 추가
  - `.cursorrules`에 프로세스 중복 실행 방지 규칙 추가

- **타입 힌팅 전면 적용**
  - `scripts/utils.py` 타입 힌팅 보완
  - 주요 스크립트들 타입 힌팅 추가
  - `mypy.ini` 설정 파일 생성

### 2025-11-21: 2025 전략 수립 및 인프라 구축 시작
- **목표**: 한국(KR) + 북미(NA) 타깃, 이중언어 지원, 다양한 콘텐츠 필러
- **주요 결정사항**:
  - Claude API 통합으로 비용 96% 절감 (GPT 대비)
  - 무료 이미지 API (Unsplash, Pexels, Pixabay) 우선 사용
  - Flask 웹 대시보드 구축 (수익 및 성과 모니터링)
  - Git 기반 채널 상태 추적 (`data/channel_state.json`)
  - 이중언어 메타데이터 시스템 (한글/영어)
- **생성된 문서**:
  - `TODO_2025_STRATEGY.md`: 전체 로드맵
  - `docs/API_INTEGRATION_STRATEGY.md`: API 통합 전략
  - `implementation_plan.md`: 상세 구현 계획

- **이중언어 메타데이터 시스템**
  - 한글/영어 자동 생성
  - `generate_title_description.py` 업데이트
  - 프리셋 YAML에 `languages`, `region_targets` 필드 추가

- **AI Explainer 콘텐츠 필러**
  - Claude 3.5 Sonnet 사용
  - `scripts/generate_ai_explainers.py`: 스크립트 생성
  - `scripts/make_ai_explainer_video.py`: 영상 제작
  - `data/ai_explainer_topics.yaml`: 주제 관리

- **스케줄링 & 자동화 시스템**
  - `scripts/scheduler.py`: 요일별 필러 로테이션
  - `data/upload_schedule.yaml`: 스케줄 설정
  - `main.py`에 `--mode auto` 옵션 추가

- **API Manager 구현**
  - `src/api/api_manager.py`: 중앙 API 관리
  - `src/api/usage_tracker.py`: 사용량 추적
  - `src/api/providers/`: OpenAI, Claude, Image Provider

- **Flask 웹 대시보드**
  - `src/web/app.py`: Flask 앱
  - `src/web/routes/`: 대시보드, API 라우트
  - `run_dashboard.py`: 대시보드 실행 스크립트

### 2025-11-21: 프로젝트 구조 리팩토링
- **목표**: 중앙화된 설정 관리 및 디렉토리 구조 정리
- **주요 변경사항**:
  - `config.py` 생성: 모든 경로 및 설정 중앙 관리
  - `config/` → `data/`: 설정 파일 이동
  - `videos/`, `images/` → `output/`: 생성 파일 통합
  - `logs/` → `output/logs/`: 로그 파일 통합
- **업데이트된 스크립트**:
  - 모든 `scripts/*.py` 파일이 `config.py` 사용하도록 수정
  - `main.py` 업데이트
  - `.gitignore` 업데이트

### 2025-11-20
- **완료된 작업**:
  - Blues/Folk/Lofi 3시간 BGM 제작
  - 썸네일 비율 보정
  - 시니어용 틀린그림찾기 롱폼 생성 기능 추가
- **생성된 파일**:
  - `audio/2025-11-20_combined_blues_3h_180min.wav`
  - `audio/2025-11-20_combined_folk_3h_180min.wav`
  - `audio/2025-11-20_combined_lofi_3h_180min.wav`
  - `images/2025-11-20_blues_3h_bg.png`
  - `images/2025-11-20_folk_3h_bg.png`
  - `images/2025-11-20_lofi_3h_bg.png`
  - `videos/2025-11-20_2025-11-20_combined_blues_3h_180min.mp4`
  - `videos/2025-11-20_2025-11-20_combined_folk_3h_180min.mp4`
  - `videos/2025-11-20_2025-11-20_combined_lofi_3h_180min.mp4`
  - `config/spot_difference_presets.yaml`
  - `scripts/generate_spot_difference.py`
  - `scripts/generate_spot_difference_image.py`
  - `scripts/generate_spot_difference_metadata.py`
  - `scripts/make_spot_difference_video.py`
  - `docs/SPOT_DIFFERENCE_GUIDE.md`

### 2025-11-19
- 장르별 3시간 BGM 프리셋 추가
- BGM 생성 스크립트 개선
- 장르별 BGM 및 영상 생성
- YouTube 롱폼 영상 업로드

### 2025-11-17: 롱폼 BGM 모드 추가
- **추가된 기능**:
  - 롱폼 BGM 자동 생성 모드 (`longform_bgm`)
  - Public Domain 음악 자동 사용 기능
  - 여러 음악 파일 조합 기능
  - YouTube 영상 통계 업데이트 기능
  - 영상 통계 리포트 출력 기능
  - 크리스마스 테마 이미지 생성 기능

- **개선사항**:
  - 코드 정리 및 문서 통합
  - `.gitignore` 파일 추가
  - 문서 구조 개선 (`docs/` 폴더로 통합)

- **새로운 프리셋**:
  - `christmas_cafe_3h`: 크리스마스 카페 BGM (3시간)
  - `cafe_jazz_3h`: 카페 재즈 BGM (3시간)
  - `cafe_classical_3h`: 카페 클래식 BGM (3시간)
  - `classical_piano_3h`: 클래식 피아노 BGM (3시간)

- **지원하는 Public Domain 음악 소스**:
  - FreePD (완전 Public Domain)
  - Pixabay Music (상업용 완전 무료)
  - Musopen (Public Domain 녹음만)

- **Public Domain 음악 분류 시스템 구축**
- **DALL·E 이미지 생성 통합**
- **썸네일 압축 기능**
- **크리스마스 음악 대량 다운로드**
- **롱폼 BGM 파이프라인 개선**
- **장르별 Public Domain 음악 다운로드 시스템 구축**

---

## 📁 프로젝트 구조

```text
youtubenoise/
├── .env                        # API 키 (Git 제외)
├── .gitignore                  # Git 제외 파일 목록
├── config.py                   # 중앙화된 설정 관리
├── main.py                     # CLI 엔트리포인트
├── requirements.txt            # Python 의존성
├── token.json                  # YouTube OAuth 토큰 (Git 제외)
│
├── data/                       # 설정 및 데이터 (Git 포함)
│   ├── channel_state.json      # 채널 상태 추적 (Git 포함)
│   ├── api_usage.json          # API 사용량 추적 (Git 포함)
│   ├── bgm_presets.yaml        # BGM 프리셋
│   ├── brain_training_presets.yaml
│   ├── ai_explainer_topics.yaml
│   └── upload_schedule.yaml    # 업로드 스케줄
│
├── output/                     # 생성 파일 (Git 제외)
│   ├── videos/                 # 생성된 영상
│   ├── images/                 # 생성된 이미지
│   ├── audio/                  # 생성된 오디오
│   └── logs/                   # 로그 파일
│       ├── app.log
│       └── history.json        # 업로드 히스토리 (Git 포함)
│
├── audio/                      # 소스 오디오 (Git 포함)
│   └── public_domain/          # Public Domain 음악
│
├── scripts/                    # 스크립트 (Git 포함)
│   ├── utils.py               # 공통 유틸리티
│   ├── generate_bgm.py
│   ├── generate_image.py
│   ├── generate_title_description.py
│   ├── make_video.py
│   ├── upload_youtube.py
│   ├── scheduler.py
│   ├── sync_channel_state.py  # 채널 상태 동기화
│   ├── generate_brain_training*.py   # 브레인트레이닝
│   ├── generate_ai_explainers.py    # AI Explainer
│   ├── create_thumbnail_dalle.py     # 썸네일 생성
│   └── upload_thumbnail.py            # 썸네일 업로드
│
├── src/                        # 소스 코드 (Git 포함)
│   ├── api/                    # API 통합
│   │   ├── api_manager.py
│   │   ├── usage_tracker.py
│   │   └── providers/
│   │       ├── openai_provider.py
│   │       ├── claude_provider.py
│   │       └── image_provider.py
│   │
│   └── web/                    # Flask 웹 대시보드
│       ├── app.py
│       ├── routes/
│       │   ├── dashboard.py
│       │   └── api.py
│       ├── templates/
│       │   ├── base.html
│       │   ├── dashboard.html
│       │   └── videos.html
│       └── static/
│           ├── css/style.css
│           └── js/dashboard.js
│
├── docs/                       # 문서 (Git 포함)
│   ├── API_INTEGRATION_STRATEGY.md
│   └── ...
│
└── tests/                      # 테스트 (Git 포함)
    └── test_api_manager.py
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

# 히스토리 확인
cat HISTORY.md

# TODO 확인
cat TODO.md
```

### 3. 주요 명령어
```bash
# BGM 생성
python main.py --mode longform_bgm --preset cafe_jazz_3h

# 두뇌훈련 영상 생성
python main.py --mode brain_training --preset mixed_brain_training_senior

# AI Explainer 생성
python main.py --mode ai_explainer --topic "ChatGPT로 코딩하기"

# 자동 스케줄 실행
python main.py --mode auto

# 웹 대시보드 실행
python run_dashboard.py
```

---

**마지막 업데이트**: 2025-11-24 (썸네일 자동 생성, 다국어 지원 개선, spot_difference 모드 제거, 문서 통합)
