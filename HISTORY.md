# Project History - YouTube 롱폼 자동화

이 문서는 프로젝트의 시작부터 현재까지의 주요 결정사항과 변경 이력을 기록합니다.

---

## 📅 Timeline

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
- **참고 문서**: `WORK_HISTORY.md` (상세 작업 히스토리)

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
│   ├── spot_difference_presets.yaml
│   ├── ai_explainer_topics.yaml
│   └── upload_schedule.yaml    # 업로드 스케줄
│
├── output/                     # 생성 파일 (Git 제외)
│   ├── videos/                 # 생성된 영상
│   ├── images/                 # 생성된 이미지
│   ├── audio/                  # 생성된 오디오
│   └── logs/                   # 로그 파일
│       ├── app.log
│       └── history.json        # 업로드 히스토리
│
├── audio/                      # 소스 오디오 (Git 포함)
│   └── public_domain/          # Public Domain 음악
│
├── scripts/                    # 스크립트 (Git 포함)
│   ├── generate_bgm.py
│   ├── generate_image.py
│   ├── generate_title_description.py
│   ├── make_video.py
│   ├── upload_youtube.py
│   ├── scheduler.py
│   ├── sync_channel_state.py  # 채널 상태 동기화
│   └── ...
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

## 📂 작업 이력 (WORK_HISTORY.md 통합)

### 2025-11-20
- Blues/Folk/Lofi 3시간 BGM 제작
- 썸네일 비율 보정
- 시니어용 틀린그림찾기 롱폼 생성 기능 추가

### 2025-11-19
- 장르별 3시간 BGM 프리셋 추가
- BGM 생성 스크립트 개선
- 장르별 BGM 및 영상 생성
- YouTube 롱폼 영상 업로드

### 2025-11-17
- Public Domain 음악 분류 시스템 구축
- DALL·E 이미지 생성 통합
- 썸네일 압축 기능
- 크리스마스 음악 대량 다운로드
- 롱폼 BGM 파이프라인 개선
- 장르별 Public Domain 음악 다운로드 시스템 구축

---

## 🔑 API 키 설정 가이드

(키 설정 내용은 `HISTORY.md`에 포함된 기존 섹션을 참고)

---

**마지막 업데이트**: 2025-11-22
