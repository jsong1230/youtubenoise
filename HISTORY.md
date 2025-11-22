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

### 이전 (2025-11 이전)
- **초기 구현**:
  - 롱폼 BGM 자동 생성 (Public Domain 음악 활용)
  - 시니어용 틀린그림찾기 (DALL-E + GPT 기반)
  - 시니어용 브레인트레이닝 (7가지 모듈)
  - YouTube 자동 업로드 시스템
  - 통계 추적 및 리포트 생성

---

## 🔑 API 키 설정 가이드

### 필수 API 키

#### 1. OpenAI API
```bash
OPENAI_API_KEY=sk-...
```
- **발급 방법**: [platform.openai.com](https://platform.openai.com/api-keys)
- **용도**: GPT-4o, GPT-4o-mini (텍스트 생성), DALL-E 3 (이미지 생성)
- **비용**: 
  - GPT-4o-mini: $0.15/1M input tokens, $0.60/1M output tokens
  - DALL-E 3: $0.04/image (1024x1024)

#### 2. Claude API (Anthropic)
```bash
ANTHROPIC_API_KEY=sk-ant-...
# 또는
CLAUDE_API_KEY=sk-ant-...
```
- **발급 방법**: [console.anthropic.com](https://console.anthropic.com/)
- **용도**: Claude 3.5 Sonnet (긴 스크립트), Claude 3 Haiku (빠른 메타데이터)
- **비용**:
  - Claude 3.5 Sonnet: $3/1M input tokens, $15/1M output tokens
  - Claude 3 Haiku: $0.25/1M input tokens, $1.25/1M output tokens
- **장점**: GPT 대비 저렴하고 긴 컨텍스트 처리에 강함

#### 3. YouTube Data API v3
```bash
YOUTUBE_API_KEY=AIza...
YOUTUBE_CLIENT_ID=...apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=GOCSPX-...
YOUTUBE_REFRESH_TOKEN=1//...
```
- **발급 방법**: [Google Cloud Console](https://console.cloud.google.com/)
  1. 프로젝트 생성
  2. YouTube Data API v3 활성화
  3. OAuth 2.0 클라이언트 ID 생성 (데스크톱 앱)
  4. `scripts/refresh_youtube_token.py` 실행하여 Refresh Token 발급
- **용도**: 영상 업로드, 채널 통계, 영상 목록
- **할당량**: 10,000 quota/day (무료)

### 선택 API 키 (무료)

#### 4. Unsplash API
```bash
UNSPLASH_ACCESS_KEY=...
```
- **발급 방법**: [unsplash.com/developers](https://unsplash.com/developers)
- **용도**: 무료 고품질 배경 이미지 다운로드
- **할당량**: 50 requests/hour (무료)

#### 5. Pexels API
```bash
PEXELS_API_KEY=...
```
- **발급 방법**: [pexels.com/api](https://www.pexels.com/api/)
- **용도**: 무료 고품질 배경 이미지/영상 다운로드
- **할당량**: 200 requests/hour (무료)

#### 6. Pixabay API
```bash
PIXABAY_API_KEY=...
```
- **발급 방법**: [pixabay.com/api/docs](https://pixabay.com/api/docs/)
- **용도**: 무료 이미지/영상/음악 다운로드
- **할당량**: 5,000 requests/day (무료)

---

## 📁 프로젝트 구조

```
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
│       ├── jazz/
│       ├── classical/
│       └── ...
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

## 🎯 콘텐츠 필러 (Content Pillars)

### Pillar A: 시니어 브레인트레이닝
- **타깃**: 40-70대 시니어 (KR + NA)
- **포맷**: 10-30분 두뇌운동 영상
- **주제**: 기본 두뇌운동, 테마형 두뇌운동 (시장 보기, 여행 떠나는 날 등)
- **언어**: 한글/영어 이중언어 지원

### Pillar B: 시니어 틀린그림찾기
- **타깃**: 40-70대 시니어 (KR + NA)
- **포맷**: 15-20문제, 10-30초 카운트다운
- **주제**: 계절/테마형 (봄/벚꽃, 여름/바다, 가을/단풍, 겨울/눈)
- **언어**: 한글/영어 이중언어 자막

### Pillar C: 집중 & 힐링 BGM
- **타깃**: 전 연령대 (Global)
- **포맷**: 2-6시간 롱폼 BGM
- **주제**: Deep Focus (개발자/직장인), Sleep & Calm (불면증, 벽난로)
- **언어**: 한글/영어 제목 및 설명

### Pillar D: AI & Tech Explained (신규)
- **타깃**: 20-50대 개발자/직장인 (KR + NA)
- **포맷**: 10-15분 설명 영상
- **주제**: AI 도구/자동화, 생산성, 개인 재무
- **언어**: 한글/영어 선택

---

## 🔄 워크플로우

### 일일 자동 업로드 워크플로우
1. **Cron 실행** (매일 오전 9시)
2. **스케줄 확인** (`data/upload_schedule.yaml`)
3. **콘텐츠 생성**:
   - 오디오 생성 (BGM/노이즈)
   - 이미지 생성 (배경/틀린그림찾기)
   - 메타데이터 생성 (제목/설명/태그)
   - 영상 합성 (FFmpeg)
4. **YouTube 업로드**
5. **채널 상태 업데이트** (`data/channel_state.json`)
6. **API 사용량 기록** (`data/api_usage.json`)

### 주간 통계 동기화 워크플로우
1. **Cron 실행** (매주 일요일 자정)
2. **YouTube API 호출** (채널 통계, 영상 통계)
3. **채널 상태 업데이트**
4. **Git 커밋** (선택사항)

---

## 💡 주요 결정사항

### API 선택 전략
- **텍스트 생성**: Claude 우선 (비용 절감) → GPT 백업
- **이미지 생성**: 무료 API 우선 (Unsplash/Pexels/Pixabay) → DALL-E 최후
- **예상 비용 절감**: 96% (월 $1.50 → $0.06)

### 언어 전략
- **제목**: 주 언어 + 부 언어 (예: "시니어 두뇌운동 | Brain Workout (20min)")
- **설명**: Section 1 (주 언어) + Section 2 (부 언어) + Section 3 (혼합)
- **태그**: 양 언어 혼합 (예: ["brain training", "시니어 두뇌운동"])

### Git 관리 전략
- **포함**: 소스 코드, 설정, 채널 상태, API 사용량
- **제외**: 비밀 정보 (.env, token.json), 생성 파일 (output/)
- **목적**: 어디서든 `git pull`로 현재 상태 파악 가능

---

## 🚀 다음 단계

1. **Phase 1**: Git History & 채널 상태 추적 (진행 중)
2. **Phase 2**: 이중언어 메타데이터 시스템
3. **Phase 3**: API Manager 구현
4. **Phase 4**: Flask 웹 대시보드
5. **Phase 5**: 콘텐츠 필러 확장
6. **Phase 6**: 스케줄링 자동화
7. **Phase 7**: 문서화 및 배포

---

**마지막 업데이트**: 2025-11-22  
**작성자**: AI Assistant (Antigravity)
