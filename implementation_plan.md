# Project Restructuring Plan

## Goal
Restructure the project to match the desired folder layout, specifically creating a `data` folder that can be synced across machines.

## User Review Required
- **Data Syncing**: The `data` folder will be tracked in git. Ensure

# YouTube 롱폼 자동화 2025 - Implementation Plan

## Goal Description

이 구현 계획은 YouTube 롱폼 자동화 프로젝트를 2025년 전략에 맞춰 확장하는 것을 목표로 합니다.

**주요 목표**:
1. Git 기반 히스토리 관리 시스템 구축 (어디서든 `git pull`로 현재 상태 파악 가능)
2. Flask 웹 대시보드로 수익 및 시청 상태 모니터링
3. Claude API + 무료 이미지 API 통합으로 비용 96% 절감
4. 한글/영어 이중언어 콘텐츠 지원 (KR + NA 시장 타깃)
5. 다양한 콘텐츠 필러 확장 (Brain Training, Spot Difference, BGM, AI Explainer)

## User Review Required

> [!IMPORTANT]
> **API 키 설정 필수**
> - `ANTHROPIC_API_KEY` 또는 `CLAUDE_API_KEY`: Claude API 사용을 위해 필요
> - `UNSPLASH_ACCESS_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`: 무료 이미지 다운로드용
> - 기존 `OPENAI_API_KEY`, `YOUTUBE_API_KEY`는 계속 사용

> [!WARNING]
> **Breaking Changes**
> - `scripts/generate_title_description.py`의 함수 시그니처 변경 (언어 파라미터 추가)
> - `scripts/generate_image.py`가 `APIManager`를 사용하도록 변경
> - 기존 스크립트를 직접 호출하는 외부 코드가 있다면 수정 필요

> [!CAUTION]
> **Git 관리 전략 변경**
> - `data/channel_state.json`과 `data/api_usage.json`을 Git으로 추적
> - 민감한 정보가 포함되지 않도록 주의 필요
> - `.gitignore` 업데이트 후 기존 파일 확인 권장

## Proposed Changes

### Component 1: Git History & Channel State Management

프로젝트 상태를 Git으로 추적하여 어디서든 `git pull`로 최신 상태 파악 가능

#### [NEW] [HISTORY.md](file:///Users/joohansong/dev/youtubenoise/HISTORY.md)
- 프로젝트 시작부터 현재까지의 타임라인
- 주요 결정사항 및 변경 이력 문서화
- API 키 설정 가이드 포함

#### [MODIFY] [.gitignore](file:///Users/joohansong/dev/youtubenoise/.gitignore)
- 비밀 정보 제외: `.env`, `token.json`, `data/youtube_client_secret.json`
- 생성 파일 제외: `output/`, `logs/*.log`
- 채널 상태 포함: `!data/channel_state.json`, `!data/api_usage.json`

#### [NEW] [data/channel_state.json](file:///Users/joohansong/dev/youtubenoise/data/channel_state.json)
- 채널 통계 (영상 수, 조회수, 구독자, 시청 시간)
- 콘텐츠 필러별 성과 추적
- Git으로 관리되어 히스토리 추적 가능

#### [NEW] [data/api_usage.json](file:///Users/joohansong/dev/youtubenoise/data/api_usage.json)
- 일별 API 사용량 및 비용 추적
- 월별 비용 분석 데이터

#### [NEW] [scripts/sync_channel_state.py](file:///Users/joohansong/dev/youtubenoise/scripts/sync_channel_state.py)
- YouTube API로 채널 통계 가져오기
- `channel_state.json` 자동 업데이트
- Cron으로 주기적 실행 가능

---

### Component 2: Flask Web Dashboard

수익 및 시청 상태를 실시간 모니터링하는 웹 대시보드

#### [NEW] [src/web/app.py](file:///Users/joohansong/dev/youtubenoise/src/web/app.py)
- Flask 앱 엔트리포인트
- 라우트 등록 및 설정

#### [NEW] [src/web/routes/dashboard.py](file:///Users/joohansong/dev/youtubenoise/src/web/routes/dashboard.py)
- `/`: 홈 대시보드 (채널 통계 요약)
- `/videos`: 영상 목록 페이지

#### [NEW] [src/web/routes/api.py](file:///Users/joohansong/dev/youtubenoise/src/web/routes/api.py)
- `/api/stats`: 채널 통계 JSON
- `/api/videos`: 영상 목록 JSON
- `/api/revenue`: 수익 데이터 JSON (향후 구현)

#### [NEW] [src/web/templates/base.html](file:///Users/joohansong/dev/youtubenoise/src/web/templates/base.html)
- 기본 레이아웃 템플릿
- 네비게이션 바 포함

#### [NEW] [src/web/templates/dashboard.html](file:///Users/joohansong/dev/youtubenoise/src/web/templates/dashboard.html)
- 채널 통계 대시보드
- 콘텐츠 필러별 성과 카드

#### [NEW] [src/web/templates/videos.html](file:///Users/joohansong/dev/youtubenoise/src/web/templates/videos.html)
- 영상 목록 테이블
- 조회수, 좋아요, 댓글 등 성과 지표

#### [NEW] [src/web/static/css/style.css](file:///Users/joohansong/dev/youtubenoise/src/web/static/css/style.css)
- 대시보드 스타일시트
- 반응형 그리드 레이아웃

#### [NEW] [src/web/static/js/dashboard.js](file:///Users/joohansong/dev/youtubenoise/src/web/static/js/dashboard.js)
- 실시간 통계 업데이트 (30초마다)
- Chart.js 통합 (향후)

---

### Component 3: Multi-API Integration System

Claude API + 무료 이미지 API 통합으로 비용 96% 절감

#### [NEW] [src/api/api_manager.py](file:///Users/joohansong/dev/youtubenoise/src/api/api_manager.py)
- 모든 AI/이미지 API 통합 관리
- 최적 API 자동 선택 로직
- `generate_text()`: 길이/우선순위에 따라 GPT/Claude 선택
- `generate_image()`: 무료 API 우선, 실패 시 DALL-E

#### [NEW] [src/api/usage_tracker.py](file:///Users/joohansong/dev/youtubenoise/src/api/usage_tracker.py)
- API 사용량 및 비용 추적
- 일별/월별 비용 계산
- `data/api_usage.json`에 저장

#### [NEW] [src/api/providers/openai_provider.py](file:///Users/joohansong/dev/youtubenoise/src/api/providers/openai_provider.py)
- OpenAI API 래퍼
- GPT-4o, GPT-4o-mini, DALL-E 3 지원

#### [NEW] [src/api/providers/claude_provider.py](file:///Users/joohansong/dev/youtubenoise/src/api/providers/claude_provider.py)
- Anthropic Claude API 래퍼
- Claude 3.5 Sonnet, Claude 3 Haiku 지원

#### [NEW] [src/api/providers/image_provider.py](file:///Users/joohansong/dev/youtubenoise/src/api/providers/image_provider.py)
- 무료 이미지 API 통합
- Unsplash, Pexels, Pixabay 지원
- 이미지 다운로드 및 저장

---

### Component 4: Bilingual Metadata System

한글/영어 이중언어 메타데이터 자동 생성

#### [MODIFY] [scripts/generate_title_description.py](file:///Users/joohansong/dev/youtubenoise/scripts/generate_title_description.py)
- `language_primary`, `language_secondary`, `region` 파라미터 추가
- 이중언어 제목 생성 (예: "시니어 두뇌운동 | Brain Workout (20min)")
- 이중언어 설명 생성 (Section 1: KO, Section 2: EN, Section 3: Mixed)
- 양 언어 혼합 태그 생성
- `APIManager` 사용으로 전환 (Claude Haiku 우선)

#### [MODIFY] [data/bgm_presets.yaml](file:///Users/joohansong/dev/youtubenoise/data/bgm_presets.yaml)
- `languages: ["ko", "en"]` 필드 추가
- `region_targets: ["KR", "NA"]` 필드 추가
- 각 프리셋에 한글/영어 제목 템플릿 추가

#### [MODIFY] [data/brain_training_presets.yaml](file:///Users/joohansong/dev/youtubenoise/data/brain_training_presets.yaml)
- 이중언어 지원 필드 추가
- 테마형 두뇌운동 프리셋 추가 (시장 보기, Grocery Store 등)

#### [MODIFY] [data/spot_difference_presets.yaml](file:///Users/joohansong/dev/youtubenoise/data/spot_difference_presets.yaml)
- 계절/테마 필드 추가 (봄/벚꽃, 여름/바다, 가을/단풍, 겨울/눈)
- 이중언어 자막 옵션 추가

---

### Component 5: Content Pillar Expansion

새로운 콘텐츠 필러 추가 (AI Explainer)

#### [NEW] [scripts/generate_ai_explainers.py](file:///Users/joohansong/dev/youtubenoise/scripts/generate_ai_explainers.py)
- AI & Tech 설명 스크립트 자동 생성
- Claude 3.5 Sonnet으로 긴 스크립트 생성
- Hook → Sections → Outro 구조
- B-roll 영상 타이밍 포함

#### [NEW] [data/ai_explainer_topics.yaml](file:///Users/joohansong/dev/youtubenoise/data/ai_explainer_topics.yaml)
- AI Explainer 주제 목록
- 시리즈 정의 (예: "개발자를 위한 AI 자동화" 3부작)

#### [MODIFY] [scripts/generate_image.py](file:///Users/joohansong/dev/youtubenoise/scripts/generate_image.py)
- `APIManager` 사용으로 전환
- 무료 이미지 API 우선 사용
- DALL-E는 특별한 경우만 사용

---

### Component 6: Scheduling & Automation

요일별 필러 로테이션 및 자동 업로드

#### [NEW] [data/upload_schedule.yaml](file:///Users/joohansong/dev/youtubenoise/data/upload_schedule.yaml)
- 요일별 업로드 스케줄 정의
- 월: Brain Training, 화: Spot Difference, 수: Focus BGM 등

#### [MODIFY] [scripts/scheduler.py](file:///Users/joohansong/dev/youtubenoise/scripts/scheduler.py)
- `upload_schedule.yaml` 읽어서 자동 실행
- 요일별 필러 자동 선택
- 최적 업로드 시간 적용

#### [MODIFY] [main.py](file:///Users/joohansong/dev/youtubenoise/main.py)
- `--mode auto` 옵션 추가 (스케줄에 따라 자동 실행)
- `--language` 옵션 추가 (ko/en 선택)

---

### Component 7: Documentation

프로젝트 문서 업데이트

#### [MODIFY] [README.md](file:///Users/joohansong/dev/youtubenoise/README.md)
- 2025 전략 반영
- Flask 대시보드 사용법 추가
- Claude API 설정 가이드 추가

#### [MODIFY] [TODO.md](file:///Users/joohansong/dev/youtubenoise/TODO.md)
- 기존 TODO를 `TODO_2025_STRATEGY.md`로 대체
- 단순 체크리스트로 변경

#### [NEW] [docs/API_INTEGRATION_STRATEGY.md](file:///Users/joohansong/dev/youtubenoise/docs/API_INTEGRATION_STRATEGY.md)
- API 사용 전략 문서 (이미 생성됨)

#### [MODIFY] [requirements.txt](file:///Users/joohansong/dev/youtubenoise/requirements.txt)
- Flask 추가
- anthropic 추가
- requests 추가 (이미지 다운로드용)

## Verification Plan

### Automated Tests

1. **API Manager 테스트**
   ```bash
   python -m pytest tests/test_api_manager.py
   ```
   - Claude API 연결 테스트
   - 무료 이미지 API 다운로드 테스트
   - 사용량 추적 테스트

2. **채널 상태 동기화 테스트**
   ```bash
   python scripts/sync_channel_state.py
   cat data/channel_state.json  # 결과 확인
   ```

3. **이중언어 메타데이터 테스트**
   ```bash
   python -c "from scripts.generate_title_description import generate_metadata_for_bgm; print(generate_metadata_for_bgm('cafe_jazz_3h', 180, 'ko', 'en', 'KR'))"
   ```

### Manual Verification

1. **Flask 대시보드 실행**
   ```bash
   python src/web/app.py
   # 브라우저에서 http://localhost:5000 접속
   # 채널 통계, 영상 목록 확인
   ```

2. **첫 번째 이중언어 영상 생성**
   ```bash
   python main.py --mode longform_bgm --preset cafe_jazz_3h --duration-minutes 180 --language ko
   # 생성된 메타데이터 확인 (한글 + 영어 혼합)
   # output/videos/ 에서 영상 확인
   ```

3. **AI Explainer 첫 영상 생성**
   ```bash
   python main.py --mode ai_explainer --topic "GPT로 유튜브 자동화" --language ko
   # 스크립트 품질 확인
   # B-roll 영상 매칭 확인
   ```

4. **비용 절감 확인**
   ```bash
   cat data/api_usage.json
   # 일별 비용 확인
   # DALL-E 사용 빈도 확인 (무료 API 우선 사용 확인)
   ```

5. **Git 관리 확인**
   ```bash
   git status
   # data/channel_state.json, data/api_usage.json이 추적되는지 확인
   # .env, token.json은 제외되는지 확인
   ```

---

**예상 구현 기간**: 3-4주  
**우선순위**: Phase 1 (인프라) → Phase 3 (API 통합) → Phase 2 (이중언어) → Phase 5 (콘텐츠 확장)
